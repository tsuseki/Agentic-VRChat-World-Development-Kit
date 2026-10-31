# Bare limbs + floating sprays check for packed (shipped) tree meshes.
#
#   B="python .omp/scripts/tool.py blender"
#   $B --script .omp/skills/lowpoly-tree-generation/scripts/bare_limbs.py -- [--out <dir>] [--render] <Sp>_Booth.blend [...]
#     stage 1 (Blender): dumps each pack blend's <Sp>_Tree mesh (the shipped FBX mesh) and, for comparison, the
#     <Sp>_Tree_LOD0 bark of the sibling <Sp>_Tree.blend to <out>/<Sp>_barelimbs.npz, then runs stage 2 with the system
#     python (numpy + scipy + pillow; Blender has no scipy; --jobs 4 workers). --render: stage 3 renders every failing
#     spot (bad bark red, the shown floating card magenta, a correct card cyan) to <out>/renders/<Sp>_<kind><k>.png.
#   python bare_limbs.py <npz> [...] [--json <report.json>]     stage 2 alone
#   $B --script bare_limbs.py -- --render-json <report.json>    stage 3 alone
#   Also accepts a _Tree.blend (uses <Sp>_Tree_LOD1 = the culled shipped mesh, bark = material slot 0).
#
# Mesh split. Pack blends have one material: bark = faces whose UVs lie in the bark strip (column layout u >= 0.76;
# legacy quadrant packs: u >= 2, the pack's +100 bark tag); everything else is leaf cards. Leaf cover = the OPAQUE
# card texels only: every card is sampled every 4 cm in 3D and kept where the atlas (tex/<Tex>_Atlas_RGBA.png) alpha
# >= 0.45 (the shader cutoff), so a transparent card corner is never counted as leaves.
# Limb skeleton. Pack bark UVs run V along each tube ring by ring (tree_booth_pack.py column_uvs; tree_uv cylinder UVs
# in a build blend), so the vertices of one bark island sharing a V are one ring: ring centre + mean radius, in V order,
# plus the cone apex = one polyline per tube (a merged limb chain), base -> tip.
# Leaf mass. enclosure(p, R) = share of 26 directions around a bark point in which an opaque leaf texel lies within R m
# of the bark surface: ~1 inside foliage, ~0.5 on the crown surface, ~0 in the open.
#   covered(p)  = enclosure(p, 0.35) >= 0.5, or a spray's painted twig base is attached within max(0.10, 2 r) of p.
#   BARE END    = tube tip above 0.6 m that is not covered. Bare length = distance along the tube from the tip back
#                 to the last covered point (whole = never covered). FAIL when >= 0.25 m (shorter = 'minor'). A ground
#                 stem whose top divides into a limb whorl (a child rooted within 0.3 m of its end that reaches leaves;
#                 kit stem_dome without a merge) ends in its limbs: no bare end (its length falls to the run rule).
#   BARE RUN    = stretch above 1.0 m, longer than 1.0 m, with enclosure(p, 0.6) < 0.3 and no attached spray
#                 (no leaf mass within 0.6 m). Exempt when the tube (or a child limb rooted further out; a tube's
#                 parent = the other tube nearest its base, never a sibling rooted at the same point) ends covered
#                 AND the point is under the canopy (opaque leaves above it within 0.6 m horizontally) or on a
#                 ground-rooted trunk below the crown base (10th percentile of leaf height; palm and leaning trunks).
#                 A limb or stem that ends bare is never exempt.
#                 PROP roots (K3 stilt / pillar roots: a ground tube whose upper end lies inside another tube more
#                 than 0.3 m past that tube's base) have no bare end, and their runs are exempt under the canopy or
#                 below the crown base (they carry no leaves by design). AERIAL roots (K3 hang: a tube hanging plumb
#                 > 0.8 m from a host point past its base, not tapering to a twig tip) count as props the same way.
#   INTERIOR    = an end/run deep inside the crown (opaque leaves within 1.5 m in >= 75 % of directions): it shows
#                 only from under the tree, so it WARNs instead of failing. ends_covered_in_lod0 = bare ends that had
#                 leaf cover in the unculled LOD0 (the hidden-card cull bared them).
# FLOATING SPRAY (the user: painted twig must continue out of the end of a 3D bark twig). Per card: the painted twig
#   base = centroid of the opaque texels in the lowest 3 opaque rows of the card's cell (read from the atlas pixels,
#   not the json), mapped through the card's UVs to 3D; twig direction = towards the opaque centroid of the lowest 15 %
#   of the cell. base_d = signed distance from it to the bark surface (tube skeleton: |p - axis| - r, negative inside).
#   attached = base_d <= max(0.05, 2 r) (calibrated: EnglishOak / HolmOak / Olive cards sit at -10 .. +2 cm, 5-95 %).
#   FLOATING = not attached; DETACHED = no opaque texel of the card within 0.35 m of bark. The same base is measured
#   against the LOD0 bark (orphan_lod1 = attached to LOD0 bark, floating on the shipped one: LOD1 bark simplification).
#   Trees with < 50 % attached cards are volume crowns (spindle/ellipsoid: cards on a shell, floating by design):
#   float verdict VOLUME = allowed only where the crown hides all wood from every angle (clipped / topiary /
#   columnar), an eye check; sprig trees FAIL above 2 % floating cards.
# Output: BARE_END / BARE_RUN / FLOAT lines and per tree
#   BARELIMBS <Sp> PASS|WARN|FAIL ends <n> (minor <m>) runs <k> interior <i> floating <f>/<cards> (<pct>%) PASS|FAIL|VOLUME ...
#   PASS = no bare end >= 0.25 m, no bare run, floating ok; WARN = only interior spots; FAIL otherwise.
# Blender coordinates; Unity local = (-x, z, -y).
import sys, os, json, re, subprocess

CUT = 0.45
END_R, END_E, END_Z, END_FAIL = 0.35, 0.5, 0.6, 0.25
RUN_R, RUN_E, RUN_Z, RUN_L = 0.6, 0.3, 1.0, 1.0
ATT_MIN, FLOAT_FAIL = 0.05, 2.0   # attach tolerance (m, or 2 r); floating-card share (%) that fails a sprig tree
HERE = os.path.abspath(__file__)


# ---------------------------------------------------------------- stage 1 (Blender): dump meshes
def grab(path, names):
    import bpy
    import numpy as np
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [o for o in src.objects if o in names]
    obs = [o for o in dst.objects if o is not None]
    if not obs: return None
    ob = sorted(obs, key=lambda o: names.index(o.name.split(".")[0]) if o.name.split(".")[0] in names else 9)[0]
    me = ob.data; mw = np.array(ob.matrix_world)
    nv, nl, npo = len(me.vertices), len(me.loops), len(me.polygons)
    co = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    co = (co @ mw[:3, :3].T + mw[:3, 3]).astype(np.float32)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    uv = np.empty(nl * 2, np.float32); me.uv_layers["UVMap"].data.foreach_get("uv", uv)
    ls = np.empty(npo, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npo, np.int32); me.polygons.foreach_get("loop_total", lt)
    mi = np.empty(npo, np.int32); me.polygons.foreach_get("material_index", mi)
    me.calc_loop_triangles()
    tl = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("loops", tl)
    tp = np.empty(len(me.loop_triangles), np.int32); me.loop_triangles.foreach_get("polygon_index", tp)
    d = dict(co=co, lv=lv, uv=uv.reshape(-1, 2), ls=ls, lt=lt, mi=mi, tl=tl.reshape(-1, 3), tp=tp,
             nslots=len(me.materials), mat=me.materials[0].name if len(me.materials) else "", obname=ob.name)
    for o in obs:
        m = o.data; bpy.data.objects.remove(o)
        if m.users == 0: bpy.data.meshes.remove(m)
    return d


def dump(files, out):
    import numpy as np
    npzs = []
    for path in files:
        path = os.path.abspath(path); base = os.path.basename(path)
        sp = re.sub(r"_(Booth|Tree)\.blend$", "", base); d = os.path.dirname(path)
        pk = grab(path, [f"{sp}_Tree", f"{sp}_Tree_LOD1"])
        if pk is None: print("BARE_SKIP no mesh", path, flush=True); continue
        tb = os.path.join(d, f"{sp}_Tree.blend")
        l0 = grab(tb, [f"{sp}_Tree_LOD0"]) if os.path.exists(tb) else None
        tex = re.sub(r"\.\d+$", "", pk["mat"]); tex = tex[:-5] if tex.endswith("_Tree") else sp
        texdir = os.path.join(os.path.dirname(d), "tex")
        if not os.path.exists(os.path.join(texdir, f"{tex}_Atlas_RGBA.png")):  # build blend with a 2-slot material
            tex = re.sub(r"_(Bark|Leaves).*$", "", tex)
        rec = {f"pk_{k}": v for k, v in pk.items()}
        if l0: rec.update({f"l0_{k}": v for k, v in l0.items()})
        o = out or d; os.makedirs(o, exist_ok=True)
        f = os.path.join(o, f"{sp}_barelimbs.npz")
        np.savez_compressed(f, species=sp, blend=path, family=os.path.basename(os.path.dirname(d)),
                            atlas=os.path.join(texdir, f"{tex}_Atlas_RGBA.png"), **rec)
        npzs.append(f); print("BARE_DUMP", f, flush=True)
    return npzs


# ---------------------------------------------------------------- stage 2 (system python): analysis
def _np():
    import numpy as np
    return np


_alpha = {}
def atlas_alpha(path):
    np = _np(); from PIL import Image
    if path not in _alpha:
        Image.MAX_IMAGE_PIXELS = None
        _alpha[path] = np.asarray(Image.open(path).convert("RGBA"))[:, :, 3].astype(np.float32) / 255.0
    return _alpha[path]


def mesh(z, p):
    np = _np()
    co = z[p + "co"].astype(np.float64); uv = z[p + "uv"].astype(np.float64); ls = z[p + "ls"]; lt = z[p + "lt"]
    pid = np.repeat(np.arange(len(ls)), lt)
    if int(z[p + "nslots"]) >= 2: bark = z[p + "mi"] == 0
    else:
        umin = np.minimum.reduceat(uv[:, 0], ls)
        bark = umin >= 2.0 if uv[:, 0].max() > 2.0 else umin >= 0.76
    return dict(co=co, lv=z[p + "lv"], uv=uv, ls=ls, lt=lt, pid=pid, bark=bark, tl=z[p + "tl"], tp=z[p + "tp"])


def islands(M, polymask):
    np = _np()
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    nv, npo = len(M["co"]), len(M["ls"]); m = polymask[M["pid"]]
    A = coo_matrix((np.ones(m.sum()), (M["lv"][m], M["pid"][m] + nv)), shape=(nv + npo, nv + npo))
    return connected_components(A, directed=False)[1], m


def skeleton(M):
    """One polyline per bark tube: ring centres in V order + the cone apex. [dict(P, R, ground, verts)]"""
    np = _np()
    co, lv, uv = M["co"], M["lv"], M["uv"]
    lab, m = islands(M, M["bark"])
    li = np.nonzero(m)[0]; li = li[np.argsort(lab[lv[li]], kind="stable")]
    keys = lab[lv[li]]; tubes = []
    for grp in np.split(li, np.nonzero(np.diff(keys))[0] + 1):
        vs, inv = np.unique(lv[grp], return_inverse=True)
        vV = np.round(np.bincount(inv, uv[grp, 1]) / np.bincount(inv), 3)
        rows = []
        for val in np.unique(vV):
            ids = vs[vV == val]; P = co[ids]
            if P[:, 2].max() < -0.01: continue  # root-flare skirt
            c = P.mean(0); rows.append((val, len(ids), c, float(np.linalg.norm(P - c, axis=1).mean())))
        rings = [x for x in rows if x[1] >= 3]
        if len(rings) < 2: continue  # buried child-base cone
        apex = [x for x in rows if x[1] < 3 and x[0] > rings[-1][0]]
        P = np.array([x[2] for x in rings] + [a[2] for a in apex[-1:]])
        R = np.array([x[3] for x in rings] + [0.0 for _ in apex[-1:]])
        tubes.append(dict(P=P, R=R, ground=bool(co[vs, 2].min() <= 0.05), verts=vs))
    return tubes


def densify(tubes, step):
    np = _np()
    pts, rad, tid, arc, tan = [], [], [], [], []
    for t, T in enumerate(tubes):
        P, R = T["P"], T["R"]; s = 0.0; last = np.array([0, 0, 1.0])
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]; L = np.linalg.norm(b - a)
            if L < 1e-6: continue
            n = max(1, int(np.ceil(L / step))); f = np.arange(n) / n; last = (b - a) / L
            pts.append(a + (b - a) * f[:, None]); rad.append(R[i] + (R[i + 1] - R[i]) * f); tid.append(np.full(n, t))
            arc.append(s + L * f); tan.append(np.repeat(last[None], n, 0)); s += L
        pts.append(P[-1][None]); rad.append(R[-1:]); tid.append([t]); arc.append([s]); tan.append(last[None])
        T["length"] = s
    return dict(P=np.concatenate(pts), R=np.concatenate(rad), T=np.concatenate(tid).astype(int),
                S=np.concatenate(arc), D=np.concatenate(tan))


def bark_dist(S, Q, k=24):
    """Signed distance from Q to the bark tube surface (negative inside) and the nearest skeleton sample index."""
    np = _np(); from scipy.spatial import cKDTree
    kd = cKDTree(S["P"]); dd, ii = kd.query(Q, k=min(k, len(S["P"])))
    if dd.ndim == 1: dd, ii = dd[:, None], ii[:, None]
    sd = dd - S["R"][ii]; j = np.argmin(sd, 1); r = np.arange(len(Q))
    return sd[r, j], ii[r, j]


def leaf_cards(M, alpha, spacing=0.04):
    """Cards (leaf islands): their triangles, and the opaque texel cloud (3D points + card id)."""
    np = _np()
    co, lv, uv, tl, tp = M["co"], M["lv"], M["uv"], M["tl"], M["tp"]
    leafpoly = ~M["bark"]; lab, _ = islands(M, leafpoly)
    tm = leafpoly[tp]; T = tl[tm]
    uc, cid = np.unique(lab[lv[T[:, 0]]], return_inverse=True)
    X = co[lv[T]]; U = uv[T]; H, W = alpha.shape
    n = (np.maximum(np.linalg.norm(X[:, 1] - X[:, 0], axis=1), np.linalg.norm(X[:, 2] - X[:, 0], axis=1)) / spacing).astype(int) + 2
    cloud, cc = [], []
    grids = {}
    for k in range(len(T)):
        if n[k] not in grids:
            a, b = np.meshgrid(np.linspace(0, 1, n[k]), np.linspace(0, 1, n[k])); a, b = a.ravel(), b.ravel(); s = a + b <= 1
            grids[n[k]] = np.stack([1 - a[s] - b[s], a[s], b[s]], 1)
        w = grids[n[k]]; q = w @ U[k]
        px = np.clip((q[:, 0] % 1.0) * W, 0, W - 1).astype(int); py = np.clip((1 - q[:, 1] % 1.0) * H, 0, H - 1).astype(int)
        ok = alpha[py, px] >= CUT
        cloud.append((w @ X[k])[ok]); cc.append(np.full(ok.sum(), cid[k]))
    cards = [np.nonzero(cid == c)[0] for c in range(len(uc))]
    polys = [np.unique(tp[tm][t]) for t in cards]
    return np.concatenate(cloud), np.concatenate(cc), cards, polys, X, U


def stem_base(alpha, ub, vb):
    """Painted twig base in a UV box: centroid of the opaque texels of the lowest 3 opaque rows; + direction point."""
    np = _np(); H, W = alpha.shape
    x0, x1 = max(0, int(np.floor(ub[0] * W))), int(np.ceil(ub[1] * W)); y0, y1 = max(0, int(np.floor((1 - vb[1]) * H))), int(np.ceil((1 - vb[0]) * H))
    a = alpha[y0:y1, x0:x1] >= CUT; rows = np.nonzero(a.any(1))[0]
    if len(rows) == 0: return None
    low = rows[-3:]; _, xs = np.nonzero(a[low[0]:low[-1] + 1])
    base = ((x0 + xs.mean() + 0.5) / W, 1 - (y0 + low[-1] + 1) / H)
    top = max(0, low[-1] - int(0.15 * (y1 - y0))); ys2, xs2 = np.nonzero(a[top:low[-1] + 1])
    return base, ((x0 + xs2.mean() + 0.5) / W, 1 - (y0 + top + ys2.mean() + 0.5) / H)


def uv_to_3d(Xc, Uc, q):
    np = _np()
    a = Uc[:, 0]; v0 = Uc[:, 1] - a; v1 = Uc[:, 2] - a; v2 = q - a
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01; den = np.where(np.abs(den) < 1e-14, 1e-14, den)
    w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den
    Wt = np.stack([1 - w1 - w2, w1, w2], 1); k = np.argmax(Wt.min(1)); w = np.clip(Wt[k], 0, None); w /= w.sum()
    return w @ Xc[k]


_DIRS = None
def enclosure(kd, Pc, Q, R, rad):
    np = _np(); global _DIRS
    if _DIRS is None:
        i = np.arange(26) + 0.5; ph = np.arccos(1 - 2 * i / 26); th = np.pi * (1 + 5 ** 0.5) * i
        _DIRS = np.stack([np.cos(th) * np.sin(ph), np.sin(th) * np.sin(ph), np.cos(ph)], 1)
    out = np.zeros(len(Q))
    for i, l in enumerate(kd.query_ball_point(Q, R + rad)):
        if not l: continue
        v = Pc[l] - Q[i]; d = np.linalg.norm(v, axis=1); ok = d > 1e-6
        if ok.any(): out[i] = len(np.unique(np.argmax((v[ok] / d[ok, None]) @ _DIRS.T, 1))) / 26.0
    return out


def card_bases(M, al):
    """Leaf cards of mesh M: opaque cloud, card ids, cards, polys, painted twig base (3D) + direction, cell cache."""
    np = _np()
    cloud, cc, cards, polys, X, U = leaf_cards(M, al)
    cache, base, tdir = {}, [], []
    for t in cards:
        Uc, Xc = U[t], X[t]
        key = tuple(np.round([Uc[..., 0].min(), Uc[..., 0].max(), Uc[..., 1].min(), Uc[..., 1].max()], 4))
        if key not in cache: cache[key] = stem_base(al, key[:2], key[2:])
        sb = cache[key]
        if sb is None: base.append(np.full(3, np.nan)); tdir.append(np.zeros(3)); continue
        p = uv_to_3d(Xc, Uc, np.array(sb[0])); q = uv_to_3d(Xc, Uc, np.array(sb[1]))
        base.append(p); tdir.append((q - p) / max(1e-9, np.linalg.norm(q - p)))
    return cloud, cc, cards, polys, np.array(base).reshape(-1, 3), np.array(tdir).reshape(-1, 3), cache


def cover(cloud, base, attached_mask, Q, Rq):
    """covered(Q) = enclosure(0.35) >= 0.5 or an attached painted twig base within max(0.10, 2 r); + e35, e60, near_att."""
    np = _np(); from scipy.spatial import cKDTree
    Pc = cloud[np.unique(np.floor(cloud / 0.06).astype(np.int64), axis=0, return_index=True)[1]]; kdc = cKDTree(Pc)
    e35 = enclosure(kdc, Pc, Q, END_R, Rq); e60 = enclosure(kdc, Pc, Q, RUN_R, Rq)
    near_att = np.zeros(len(Q), bool)
    if attached_mask.any():
        near_att = cKDTree(base[attached_mask]).query(Q)[0] <= np.maximum(0.10, 2 * Rq)
    return (e35 >= END_E) | near_att, e35, e60, near_att, Pc


def analyze(npz):
    np = _np(); from scipy.spatial import cKDTree
    z = np.load(npz, allow_pickle=False); sp = str(z["species"])
    al = atlas_alpha(str(z["atlas"]))
    M = mesh(z, "pk_"); tubes = skeleton(M)
    S = densify(tubes, 0.01); S5 = densify(tubes, 0.05)
    cloud, cc, cards, polys, base, tdir, cache = card_bases(M, al)
    ok = ~np.isnan(base[:, 0])
    bd = np.full(len(cards), 9.9); cosd = np.zeros(len(cards)); rr = np.zeros(len(cards)); tipd = np.full(len(cards), 9.9)
    sd, ix = bark_dist(S, base[ok]); bd[ok] = sd; rr[ok] = S["R"][ix]; cosd[ok] = np.abs((tdir[ok] * S["D"][ix]).sum(1))
    tips = np.array([T["P"][-1] for T in tubes]); tipd[ok] = cKDTree(tips).query(base[ok])[0]
    attached = bd <= np.maximum(ATT_MIN, 2 * rr)
    # lowest opaque texel to bark, per card
    csd, _ = bark_dist(S, cloud, k=8); near = np.full(len(cards), 9.9); np.minimum.at(near, cc, csd)
    detached = near > END_R
    # LOD0 comparison (the unculled build: full bark rings, every card)
    l0 = "l0_co" in z.files; orphan = np.zeros(len(cards), bool); bd0 = np.full(len(cards), np.nan); cov0 = None
    if l0:
        M0 = mesh(z, "l0_"); S0 = densify(skeleton(M0), 0.01); s0, i0 = bark_dist(S0, base[ok]); bd0[ok] = s0
        orphan[ok] = (~attached[ok]) & (s0 <= np.maximum(ATT_MIN, 2 * S0["R"][i0]))
        if M0["uv"][~M0["bark"][M0["pid"]], 0].max() <= 0.76 and M["uv"][:, 0].max() < 2.0:  # LOD0 leaves on the same atlas
            c0, _, _, _, b0, _, _ = card_bases(M0, al); k0 = ~np.isnan(b0[:, 0])
            a0 = np.zeros(len(b0), bool); q, iq = bark_dist(S0, b0[k0]); a0[k0] = q <= np.maximum(ATT_MIN, 2 * S0["R"][iq])
            cov0 = cover(c0, b0, a0, S5["P"], S5["R"])[0]
    volume = attached.mean() < 0.5
    # ---- leaf mass around the bark
    cov, e35, e60, near_att, Pc = cover(cloud, base, attached, S5["P"], S5["R"])
    crown_base = float(np.percentile(cloud[:, 2], 10))  # main crown bottom (10th percentile of opaque leaf height)
    # canopy above a point: opaque leaves within 0.6 m horizontally and higher up
    g = 0.3; cell = {}
    for (i, j), zz in zip(map(tuple, np.floor(Pc[:, :2] / g).astype(int)), Pc[:, 2]):
        cell[(i, j)] = max(cell.get((i, j), -1e9), zz)
    def canopy(p):
        i, j = int(np.floor(p[0] / g)), int(np.floor(p[1] / g))
        return max(cell.get((i + a, j + b), -1e9) for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2)) > p[2] + 0.3
    # tube tree: parent of each tube = the other tube nearest its base; reach = tip covered or a child reaching cover
    tipcov = [bool(cov[np.nonzero(S5["T"] == t)[0][-1]]) for t in range(len(tubes))]
    parent = [(-1, 0.0)] * len(tubes)
    b0 = np.array([T["P"][0] for T in tubes])
    for t, T in enumerate(tubes):  # (not a sibling rooted at the same point: a whorl's limbs start inside each other)
        sib = np.nonzero(np.linalg.norm(b0 - T["P"][0], axis=1) < 0.05)[0]
        m = ~np.isin(S["T"], sib)
        if not m.any(): continue
        d, i = cKDTree(S["P"][m]).query(T["P"][0]); i = np.nonzero(m)[0][i]
        if d - S["R"][i] <= 0.05 and not T["ground"]: parent[t] = (int(S["T"][i]), float(S["S"][i]))
    reach = list(tipcov)
    for _ in range(len(tubes)):
        ch = False
        for t, (pa, _s) in enumerate(parent):
            if pa >= 0 and reach[t] and not reach[pa]: reach[pa] = ch = True
        if not ch: break
    def continues(t, s):  # tube t carries leaves beyond arc s (own tip, or a covered child rooted past s)
        return tipcov[t] or any(pa == t and ps >= s - 0.05 and reach[c] for c, (pa, ps) in enumerate(parent))
    zt = [float(T["P"][:, 2].max()) for T in tubes]
    def anchored(t):  # K3 prop / pillar root: a ground tube whose upper end lies inside another tube past its base
        T = tubes[t]  # (a trunk's top meets its children's bases instead: arc ~0, not a prop); hosts: non-ground
        if not T["ground"]:  # tubes or ground tubes reaching > 1 m higher (trunks, not sibling props)
            # K3 aerial root: hangs plumb (> 0.9) from its base for > 0.8 m and stays thick to its end (a drooping twig
            # tapers to its tip); its base lies inside a host > 1.5 x as thick past the host's base (not a sibling
            # strand, not a twig forking there): no bare end; its runs are exempt under the canopy
            v = T["P"][-1] - T["P"][0]; L = float(np.linalg.norm(v)); R = T["R"][T["R"] > 1e-4]  # (not the cap apex)
            if L < 0.8 or v[2] / L > -0.9 or len(R) < 2 or R[-1] < 0.45 * R[0]: return False
            m = np.array([u != t and float(tubes[u]["R"].max()) > 1.5 * R[0] for u in range(len(tubes))])[S["T"]]
            top = T["P"][0]
        else:
            m = np.array([u != t and (not tubes[u]["ground"] or zt[u] > zt[t] + 1.0) for u in range(len(tubes))])[S["T"]]
            top = T["P"][int(np.argmax(T["P"][:, 2]))]
        if not m.any(): return False
        # (k 400: a twig forking at the same point fills the nearest 1 cm samples; the host limb lies beyond them)
        ds, ii = cKDTree(S["P"][m]).query(top, k=min(400, int(m.sum()))); ii = np.nonzero(m)[0][np.atleast_1d(ii)]
        hb = np.array([tubes[int(u)]["P"][0] for u in S["T"][ii]])  # host tube bases: a trunk top meets child bases
        ok = (np.atleast_1d(ds) - S["R"][ii] <= 0.1) & (S["S"][ii] > 0.3) & (np.linalg.norm(hb - top, axis=1) > 0.5)
        return top[2] > RUN_Z and bool(ok.any())
    prop = [anchored(t) for t in range(len(tubes))]
    ends, runs = [], []
    for t, T in enumerate(tubes):
        m = np.nonzero(S5["T"] == t)[0]; P = S5["P"][m]; s = S5["S"][m]; c = cov[m]
        # (a ground stem dividing into a limb whorl at its top, kit stem_dome without merge, ends in its limbs: no bare
        # end; its length is judged by the run rule below)
        whorl = T["ground"] and any(pa == t and ps >= s[-1] - 0.3 and reach[c_] for c_, (pa, ps) in enumerate(parent))
        if P[-1, 2] > END_Z and not c[-1] and not prop[t] and not whorl:  # a prop's ends are in the ground and in its host tube
            ci = np.nonzero(c)[0]; j = ci[-1] if len(ci) else 0
            ends.append(dict(tube=t, tip=P[-1].tolist(), length=float(s[-1] - s[j]), r=float(S5["R"][m][j]),
                             e35=float(e35[m][-1]), whole=bool(len(ci) == 0), ground=T["ground"],
                             lod0_covered=None if cov0 is None else bool(cov0[m][-1]), seg=P[j:].tolist(), segr=S5["R"][m][j:].tolist()))
        bare = (P[:, 2] > RUN_Z) & (e60[m] < RUN_E) & ~near_att[m]
        for k in np.nonzero(bare)[0]:  # trunk below the crown base / limbs under the canopy that lead on into leaves /
            # prop roots (ground to host tube) under the canopy or below the crown base
            if (continues(t, s[k]) or prop[t]) and (canopy(P[k]) or (T["ground"] and P[k, 2] < crown_base)): bare[k] = False
        k = 0
        while k < len(bare):
            if not bare[k]: k += 1; continue
            j = k
            while j + 1 < len(bare) and bare[j + 1]: j += 1
            if s[j] - s[k] > RUN_L:
                runs.append(dict(tube=t, a=P[k].tolist(), b=P[j].tolist(), mid=P[(k + j) // 2].tolist(), length=float(s[j] - s[k]),
                                 z=[float(P[k:j + 1, 2].min()), float(P[k:j + 1, 2].max())], r=float(S5["R"][m][k:j + 1].max()),
                                 ground=T["ground"], seg=P[k:j + 1].tolist(), segr=S5["R"][m][k:j + 1].tolist()))
            k = j + 1
    # interior = deep inside the crown (opaque leaves within 1.5 m in >= 75 % of directions): seen only from under/inside it
    for lst, key in ((ends, "tip"), (runs, "mid")):
        if lst:
            e150 = enclosure(cKDTree(Pc), Pc, np.array([e[key] for e in lst]), 1.5, np.zeros(len(lst)))
            for e, v in zip(lst, e150): e["e150"] = float(v); e["interior"] = bool(v >= 0.75)
    major = [e for e in ends if e["length"] >= END_FAIL]
    outer = [e for e in major + runs if not e["interior"]]
    nfloat = int((~attached).sum()); pct = 100.0 * nfloat / max(1, len(cards))
    # floating: sprig trees fail above FLOAT_FAIL %; volume crowns float by design and are allowed only where the crown
    # hides all wood from every angle (clipped / topiary / columnar), which needs an eye check: VOLUME
    float_verdict = "VOLUME" if volume else ("FAIL" if pct > FLOAT_FAIL else "PASS")
    verdict = "FAIL" if (outer or float_verdict == "FAIL") else ("WARN" if (major or runs) else "PASS")
    # highlight polygons for renders: bark faces along each bad segment, leaf faces of floating cards
    co, lv, ls = M["co"], M["lv"], M["ls"]
    bpoly = np.nonzero(M["bark"])[0]; bc = np.add.reduceat(co[lv], ls)[bpoly] / M["lt"][bpoly, None]
    def hl(seg, segr):
        d, i = cKDTree(np.array(seg)).query(bc); return bpoly[d <= np.array(segr)[i] + 0.04].tolist()
    for e in ends + runs: e["polys"] = hl(e.pop("seg"), e.pop("segr"))
    fl = np.nonzero(~attached)[0]; worst_fl = fl[np.argsort(-bd[fl])] if len(fl) else fl
    floats = [dict(card=int(i), base=base[i].tolist(), base_d=float(bd[i]), r=float(rr[i]), near=float(near[i]), cos=float(cosd[i]),
                   lod0_d=None if np.isnan(bd0[i]) else float(bd0[i]), orphan=bool(orphan[i]), polys=polys[i].tolist()) for i in worst_fl[:40]]
    lowf = [i for i in fl if base[i, 2] >= 1.2 and bd[i] > 0.1]  # a clearly floating card low enough to see from eye height
    fshow = int(min(lowf, key=lambda i: base[i, 2])) if lowf else (int(worst_fl[0]) if len(fl) else None)
    float_show = None if fshow is None else dict(card=fshow, base=base[fshow].tolist(), base_d=float(bd[fshow]), near=float(near[fshow]),
                                                 lod0_d=None if np.isnan(bd0[fshow]) else float(bd0[fshow]), polys=polys[fshow].tolist())
    good = np.nonzero(attached & ok)[0]  # example of a correct card: painted twig on a bark tip, low enough to see
    if len(good):
        gi = int(good[np.argmin(tipd[good] + 2.0 * (np.abs(base[good, 2] - 2.5) > 1.5))])
        good_ex = dict(card=gi, base=base[gi].tolist(), base_d=float(bd[gi]), tip_d=float(tipd[gi]), cos=float(cosd[gi]), polys=polys[gi].tolist())
    else: good_ex = None
    rep = dict(species=sp, family=str(z["family"]), blend=str(z["blend"]), verdict=verdict, float_verdict=float_verdict, volume_crown=bool(volume),
               tubes=len(tubes), cards=len(cards), ends=sorted(ends, key=lambda e: -e["length"]), runs=sorted(runs, key=lambda e: -e["length"]),
               n_ends=len(major), n_minor=len(ends) - len(major), n_runs=len(runs), floating=nfloat, floating_pct=round(pct, 1),
               n_interior=sum(1 for e in major + runs if e["interior"]),
               detached=int(detached.sum()), orphan_lod1=int(orphan.sum()), lod0=l0, floats=floats, good_card=good_ex, float_show=float_show,
               floating_base_d_med=float(np.median(bd[fl])) if len(fl) else None, crown_base=crown_base,
               ends_covered_in_lod0=sum(1 for e in major if e["lod0_covered"]),
               base_d_pct=np.percentile(bd[ok], [5, 50, 95]).round(3).tolist() if ok.any() else None,
               cos_attached_pct=np.percentile(cosd[attached & ok], [5, 50]).round(2).tolist() if (attached & ok).any() else None,
               tipd_attached_med=float(np.median(tipd[attached & ok])) if (attached & ok).any() else None,
               cells={f"{k}": [round(float(x), 4) for x in v[0]] for k, v in cache.items() if v})
    U_ = lambda p: f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) unity ({-p[0]:.2f}, {p[2]:.2f}, {-p[1]:.2f})"
    for e in rep["ends"]:
        print(f"BARE_END {sp} tip {U_(e['tip'])} bare {e['length']:.2f} m r {e['r']:.3f} {'whole tube ' if e['whole'] else ''}"
              f"{'minor ' if e['length'] < END_FAIL else ''}{'interior ' if e['interior'] else ''}"
              f"{'(covered before the card cull)' if e['lod0_covered'] else ''}")
    for e in rep["runs"]:
        print(f"BARE_RUN {sp} {U_(e['a'])} -> {U_(e['b'])} length {e['length']:.2f} m z {e['z'][0]:.2f}-{e['z'][1]:.2f} r {e['r']:.3f}"
              f"{' interior' if e['interior'] else ''}")
    for f in floats[:5]:
        print(f"FLOAT {sp} card {f['card']} base {U_(f['base'])} bark {f['base_d']:.2f} m lowest texel {f['near']:.2f} m lod0 {f['lod0_d']}")
    bad = [e for e in major + runs if not e["interior"]] or major + runs
    w = max(bad, key=lambda e: e["length"]) if bad else None
    rep["worst"] = None if w is None else dict(kind="end" if "tip" in w else "run", pos=w["tip"] if "tip" in w else w["mid"],
                                                length=w["length"], r=w["r"], interior=w["interior"])
    ws = f"{rep['worst']['kind']} {U_(rep['worst']['pos'])} {w['length']:.2f} m" if w else "-"
    print(f"BARELIMBS {sp} {verdict} ends {rep['n_ends']} (minor {rep['n_minor']}) runs {rep['n_runs']} interior {rep['n_interior']} "
          f"floating {nfloat}/{len(cards)} ({pct:.1f}%) {float_verdict} detached {rep['detached']} orphan_lod1 {rep['orphan_lod1']} "
          f"ends_covered_in_lod0 {rep['ends_covered_in_lod0']} volume_crown {volume} worst {ws}", flush=True)
    return rep


# ---------------------------------------------------------------- stage 3 (Blender): renders of the failing spots
def render(report_json, outdir, maxspots=2):
    import bpy, math
    from mathutils import Vector
    reps = json.load(open(report_json)); os.makedirs(outdir, exist_ok=True)
    sc = bpy.context.scene
    for o in list(sc.objects): bpy.data.objects.remove(o)  # factory-startup cube / camera / light
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 12; sc.cycles.use_denoising = False
    sc.cycles.transparent_max_bounces = 128; sc.render.resolution_x = sc.render.resolution_y = 720
    sc.render.image_settings.file_format = 'PNG'
    w = bpy.data.worlds.new("__bl_w"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.9, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sc.world = w
    sun = bpy.data.objects.new("__bl_sun", bpy.data.lights.new("__bl_sun", 'SUN')); sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(40), 0, math.radians(30)); sc.collection.objects.link(sun)
    cd = bpy.data.cameras.new("__bl_cam"); cam = bpy.data.objects.new("__bl_cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.clip_start = 0.02
    gnd = bpy.data.meshes.new("__bl_g"); gnd.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new("__bl_g", gnd); sc.collection.objects.link(go)
    def mat(name, img=None, col=(0.5, 0.5, 0.5), tint=None, emit=None, ghost=1.0):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = 1.0
        if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = 1.5; b.inputs["Base Color"].default_value = (*emit, 1)
        elif img is None: b.inputs["Base Color"].default_value = (*col, 1)
        else:
            tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = 'Closest'
            if tint:
                mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[0].default_value = 0.7
                nt.links.new(tx.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
                b.inputs["Emission Color"].default_value = (*tint, 1); b.inputs["Emission Strength"].default_value = 0.6
            else: nt.links.new(tx.outputs[0], b.inputs["Base Color"])
            gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = CUT
            nt.links.new(tx.outputs[1], gt.inputs[0])
            if ghost < 1.0:
                mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = ghost
                nt.links.new(gt.outputs[0], mu.inputs[0]); nt.links.new(mu.outputs[0], b.inputs["Alpha"])
            else: nt.links.new(gt.outputs[0], b.inputs["Alpha"])
        return m
    go.data.materials.append(mat("__bl_gm", col=(0.35, 0.33, 0.28)))
    for rep in reps:
        ends = [e for e in rep["ends"] if e["length"] >= END_FAIL]; runs = list(rep["runs"])
        key = lambda e: (e.get("interior", False), -e["length"])  # outside-the-crown spots first
        spots = [("end", e) for e in sorted(ends, key=key)][:maxspots] + [("run", e) for e in sorted(runs, key=key)][:maxspots]
        if rep.get("float_show") and (rep["floating_pct"] > FLOAT_FAIL or rep["volume_crown"] or rep.get("render_float")):
            spots.append(("float", rep["float_show"]))
        if rep.get("render_good") and rep.get("good_card"): spots.append(("good", rep["good_card"]))
        if not spots: continue
        sp = rep["species"]; path = rep["blend"]
        with bpy.data.libraries.load(path) as (src, dst):
            dst.objects = [o for o in src.objects if o in (f"{sp}_Tree", f"{sp}_Tree_LOD1")]
        ob = [o for o in dst.objects if o is not None][0]; sc.collection.objects.link(ob)
        me = ob.data; uvd = me.uv_layers["UVMap"].data
        atlas = os.path.join(os.path.dirname(os.path.dirname(path)), "tex",
                             re.sub(r"\.\d+$", "", me.materials[0].name)[:-5] + "_Atlas_RGBA.png") if len(me.materials) == 1 else None
        img = bpy.data.images.load(atlas) if atlas and os.path.exists(atlas) else None
        two = len(me.materials) >= 2
        if two and img is None:
            img = next((n.image for n in me.materials[1].node_tree.nodes if n.type == 'TEX_IMAGE'), None)
        me.materials.clear()
        for m in (mat("__bark", img), mat("__leaf", img), mat("__hl", emit=(1.0, 0.05, 0.02)), mat("__fl", img, tint=(1.0, 0.0, 0.9)),
                  mat("__ok", img, tint=(0.0, 0.9, 1.0)), mat("__ghost", img, ghost=0.12)):
            me.materials.append(m)
        mi0 = [0] * len(me.polygons)
        for p in me.polygons:
            u = min(uvd[l].uv[0] for l in p.loop_indices)
            mi0[p.index] = 1 if (u < (2.0 if any(uvd[l].uv[0] > 2 for l in p.loop_indices) else 0.76)) else 0
        if two: mi0 = [p.material_index for p in me.polygons]
        for k, (kind, e) in enumerate(spots):
            mi = list(mi0)
            if kind in ("float", "good"):  # card views: other cards ghosted so the bark under the painted twig shows
                mi = [5 if v == 1 else v for v in mi]
            for i in e["polys"]: mi[i] = {"end": 2, "run": 2, "float": 3, "good": 4}[kind]
            me.polygons.foreach_set("material_index", mi); me.update()
            pts = [Vector(me.vertices[v].co) for i in e["polys"] for v in me.polygons[i].vertices]
            if not pts: continue
            lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
            if kind in ("float", "good"):
                c = (Vector(e["base"]) + (lo + hi) / 2) / 2; size = max(1.0, (hi - lo).length)
                n = me.polygons[e["polys"][0]].normal.copy(); out = Vector((c.x, c.y, 0)).normalized() if Vector((c.x, c.y)).length > 0.2 else Vector((0, -1, 0))
                n = n if n.dot(out) >= 0 else -n
                v = (n + 0.35 * out).normalized(); dd = max(1.4, 1.5 * size)
                if c.z + v.z * dd < 0.4: v = (-n + 0.35 * out).normalized()  # flat card: view from above, not through the ground
                cam.location = c + v * dd; cam.location.z = max(0.4, cam.location.z)
            else:
                c = (lo + hi) / 2; size = max((hi - lo).length, 1.0)
                out = Vector((c.x, c.y, 0)); out = out.normalized() if out.length > 0.2 else Vector((0, -1, 0))
                dist = max(1.2, 1.6 * size)
                if e.get("interior"):  # inside the crown: look up at it from eye height, standing under it, beside the trunk
                    cam.location = Vector((c.x, c.y, 1.6)) + out * 1.5
                else:
                    cam.location = c + out * dist + Vector((0, 0, -0.25 * dist)); cam.location.z = max(0.4, cam.location.z)
            d = (c - cam.location).length
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.angle = min(2.0, 2 * math.atan(0.75 * size / d) + 0.35)
            f = os.path.join(outdir, f"{sp}_{kind}{k}.png"); sc.render.filepath = f
            bpy.ops.render.render(write_still=True); print("BARE_RENDER", sp, kind, f, flush=True)
        bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)


def main_blender():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    def _opt(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
    out = _opt("--out"); out = os.path.abspath(out) if out else None
    if _opt("--render-json"):
        render(_opt("--render-json"), _opt("--render-out", os.path.join(os.path.dirname(os.path.abspath(_opt("--render-json"))), "renders")))
        return
    npzs = dump([a for a in argv if a.endswith(".blend")], out)
    if not npzs or "--no-analyze" in argv: return
    rj = os.path.join(out or os.path.dirname(npzs[0]), "bare_limbs_report.json")
    r = subprocess.run(["python", HERE, *npzs, "--json", rj], capture_output=True, text=True)
    print(r.stdout + r.stderr, flush=True)
    if "--render" in argv and os.path.exists(rj): render(rj, os.path.join(os.path.dirname(rj), "renders"))


def _safe(f):
    try: return analyze(f)
    except Exception as ex: print("BARELIMBS_ERROR", f, repr(ex), flush=True); return None


def main_python():
    argv = sys.argv[1:]
    rj = argv[argv.index("--json") + 1] if "--json" in argv else None
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 4
    files = [a for a in argv if a.endswith(".npz")]
    if jobs > 1 and len(files) > 1:
        from multiprocessing import Pool
        with Pool(min(jobs, len(files))) as pool: reps = pool.map(_safe, files, chunksize=1)
    else: reps = [_safe(f) for f in files]
    reps = [r for r in reps if r]
    if rj: json.dump(reps, open(rj, "w"), indent=1); print("BARE_REPORT", rj)


if __name__ == "__main__":
    import importlib.util
    if importlib.util.find_spec("bpy"): main_blender()
    else: main_python()

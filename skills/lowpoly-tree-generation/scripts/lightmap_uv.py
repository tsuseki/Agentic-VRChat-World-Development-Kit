"""Hand-built lightmap UV for leaf-card trees: bark gets its own budget instead of an area-weighted unwrap.

Why: Smart UV Project (and Unity's Generate Lightmap UVs) size every chart by 3D surface area and ignore alpha.
Full leaf quads are ~97 % of a tree's area, so bark tubes (cut into one chart per face) came out 92-96 % under
4 lightmap texels wide; a 1-texel limb bakes one irradiance sample and reads evenly black or bright against its
trunk, with a hard line at every fork (a chart border). Stitching can't fix that; texels can.

What it does (only the lightmap layer changes; positions, UVMap, vertex colours, normals, topology stay):
- charts = UVMap islands: one ribbon per limb chain (`tree_uv.cylinder_uvs`), one chart per leaf card;
- each chart is made isotropic in metres (per-chart u/v stretch from its triangles' Jacobians, so a squeezed bark
  column still gets texels around the limb) and scaled to a uniform density per m2, bark x `bark` (linear) over
  leaves x `leaf`;
- shelf-packed into the unit square (long side horizontal, 90 degree rotation, no mirroring) with one uniform
  scale found by bisection; margins per chart type;
- the layer is UV channel 1, named `Lightmap`.

Module:  from lightmap_uv import repack, choose_bark;  stats = repack(ob, bark=5.0)
CLI:     blender --background <tree>.blend --python lightmap_uv.py -- <Object> [--fbx out.fbx] [--bark B | --auto]
                 [--ref 5] [--around 2] [--leaf 1] [--margin 0.010] [--lmargin 0.010] [--u0 0.76] [--dry] [--save]
Prints `LIGHTMAPUV <ob> ...` and `LIGHTMAPOVERLAP <ob> covered N overlapped M` (M must be 0).
Run it on the mesh that ships, after every geometry step (LOD thinning, card cull, base-cone clamp); it is
deterministic from the UVMap, so re-running on the same mesh gives the same layout (idempotent).
"""
import bpy, bmesh, math, os, sys

LAYER = "Lightmap"


def _bark_pred(ob, bm, u0):
    uv0 = bm.loops.layers.uv["UVMap"]
    if len(ob.data.materials) >= 2:            # build stage: slot 0 = bark, slot 1 = leaves
        return lambda f: f.material_index == 0
    return lambda f: min(l[uv0].uv.x for l in f.loops) >= u0   # packed one-atlas column: bark at u >= u0


def _islands(bm, lay):
    parent = list(range(len(bm.faces)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    for e in bm.edges:
        if len(e.link_faces) != 2: continue
        f1, f2 = e.link_faces
        if all(round(next(l for l in f1.loops if l.vert == v)[lay].uv.x, 5) == round(next(l for l in f2.loops if l.vert == v)[lay].uv.x, 5)
               and round(next(l for l in f1.loops if l.vert == v)[lay].uv.y, 5) == round(next(l for l in f2.loops if l.vert == v)[lay].uv.y, 5)
               for v in e.verts):
            a, b = find(f1.index), find(f2.index)
            if a != b: parent[a] = b
    g = {}
    for f in bm.faces: g.setdefault(find(f.index), []).append(f)
    return list(g.values())


def _chart(faces, lay, bark):
    """Isotropic chart in metres: (points per loop index, w, h, 3D area)."""
    su = sv = wsum = a3 = 0.0
    for f in faces:
        L = f.loops
        for t in range(1, len(L) - 1):
            p0, p1, p2 = L[0].vert.co, L[t].vert.co, L[t + 1].vert.co
            q0, q1, q2 = L[0][lay].uv, L[t][lay].uv, L[t + 1][lay].uv
            e1, e2 = p1 - p0, p2 - p0
            du1, dv1, du2, dv2 = q1.x - q0.x, q1.y - q0.y, q2.x - q0.x, q2.y - q0.y
            det = du1 * dv2 - du2 * dv1
            area = e1.cross(e2).length * 0.5
            a3 += area
            if abs(det) < 1e-14 or area < 1e-14: continue
            dpdu = (e1 * dv2 - e2 * dv1) / det; dpdv = (e2 * du1 - e1 * du2) / det
            su += dpdu.length * area; sv += dpdv.length * area; wsum += area
    su = su / wsum if wsum else 1.0; sv = sv / wsum if wsum else 1.0
    pts = {l.index: (l[lay].uv.x * su, l[lay].uv.y * sv) for f in faces for l in f.loops}
    xs = [p[0] for p in pts.values()]; ys = [p[1] for p in pts.values()]
    x0, y0 = min(xs), min(ys)
    pts = {k: (x - x0, y - y0) for k, (x, y) in pts.items()}
    return dict(faces=faces, pts=pts, w=max(xs) - x0, h=max(ys) - y0, a3=a3, bark=bark)


def _pack(charts, margin, lmargin):
    def attempt(g):
        rects = []
        for n, c in enumerate(charts):
            s = g * c["k"]; w, h = c["w"] * s, c["h"] * s; m = margin if c["bark"] else lmargin
            rot = h > w
            if rot: w, h = h, w
            rects.append((n, w + m, h + m, s, rot, m))
        rects.sort(key=lambda r: -r[2])
        shelves, out, ytop = [], {}, 0.0
        for n, w, h, s, rot, m in rects:
            if w > 1.0: return None
            for sh in shelves:
                if sh[1] >= h and sh[2] + w <= 1.0:
                    out[n] = (sh[2], sh[0], rot, s, m); sh[2] += w; break
            else:
                if ytop + h > 1.0: return None
                shelves.append([ytop, h, w]); out[n] = (0.0, ytop, rot, s, m); ytop += h
        return out

    lo, hi, best = 1e-4, 1e4, None
    for _ in range(40):
        mid = (lo * hi) ** 0.5; r = attempt(mid)
        if r is None: hi = mid
        else: lo, best = mid, r
    assert best is not None, "could not pack"
    return best


def _overlap(bm, new, isl_of, N=2048):
    import numpy as np
    owner = np.full((N, N), -1, dtype=np.int32); over = cover = 0
    for f in bm.faces:
        L = list(f.loops); iid = isl_of[f.index]
        for t in range(1, len(L) - 1):
            p = [new[L[0].index], new[L[t].index], new[L[t + 1].index]]
            xs = [q[0] * N for q in p]; ys = [q[1] * N for q in p]
            x0, x1 = max(0, int(min(xs))), min(N - 1, int(max(xs))); y0, y1 = max(0, int(min(ys))), min(N - 1, int(max(ys)))
            if x1 < x0 or y1 < y0: continue
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(d) < 1e-12: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            a = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
            b = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
            inside = (a >= 0) & (b >= 0) & (a + b <= 1)
            sub = owner[y0:y1 + 1, x0:x1 + 1]
            over += int((inside & (sub >= 0) & (sub != iid)).sum()); cover += int(inside.sum())
            sub[inside & (sub < 0)] = iid
    return cover, over


def _layout(ob, bark, leaf, margin, lmargin, u0):
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    uv0 = bm.loops.layers.uv["UVMap"]; is_bark = _bark_pred(ob, bm, u0)
    charts = [_chart(fs, uv0, is_bark(fs[0])) for fs in _islands(bm, uv0)]
    for c in charts:
        c["k"] = bark if c["bark"] else leaf   # charts are already in metres: uniform density x weight
    best = _pack(charts, margin, lmargin)
    new, isl_of = {}, {}
    for n, (px, py, rot, s, m) in best.items():
        c = charts[n]
        for f in c["faces"]: isl_of[f.index] = n
        for li, (u, v) in c["pts"].items():
            u, v = u * s, v * s
            if rot: u, v = v, c["w"] * s - u
            new[li] = (px + m * 0.5 + u, py + m * 0.5 + v)
    assert len(new) == len(me.loops)
    return bm, charts, best, new, isl_of


def _stats(charts, best, ref):
    """Predicted texels at `ref` texels/unit, Scale In Lightmap 1, assuming the lightmapper sizes an instance so its
    mean density over the whole surface equals `ref` (rect side = ref * sqrt(world area / UV fill)). Verify by bake."""
    A = sum(c["a3"] for c in charts); fill = sum(c["w"] * c["h"] * best[n][3] ** 2 for n, c in enumerate(charts))
    side = ref * math.sqrt(A / fill) if fill else 0.0
    bs = sorted(min(c["w"], c["h"]) for c in charts if c["bark"])            # ribbon short side = circumference (m)
    bark_tpm = side * next((best[n][3] for n, c in enumerate(charts) if c["bark"]), 0.0)
    leaf_tpm = side * next((best[n][3] for n, c in enumerate(charts) if not c["bark"]), 0.0)
    thin = bs[len(bs) // 10] if bs else 0.0; trunk = bs[-1] if bs else 0.0
    return dict(fill=fill, side=side, bark_tpm=bark_tpm, leaf_tpm=leaf_tpm, thin_circ=thin, trunk_circ=trunk,
                thin_tex=thin * bark_tpm, trunk_tex=trunk * bark_tpm, bark_share=sum(c["a3"] for c in charts if c["bark"]) / A)


def choose_bark(ob, ref=5.0, around=2.0, trunk=8.0, leaf_floor=0.5, leaf=1.0, margin=0.010, lmargin=0.010, u0=0.76,
                lo=1.0, hi=40.0):
    """Per-tree bark weight: the smallest that gives the p10 limb `around` texels and the trunk `trunk` texels at `ref`
    texels/unit, capped so leaves keep >= leaf_floor * ref texels/m. Returns (weight, reached_targets)."""
    def st(b):
        bm, ch, best, _, _ = _layout(ob, b, leaf, margin, lmargin, u0); s = _stats(ch, best, ref); bm.free(); return s

    def bisect(good, a, b):            # good(a) False, good(b) True -> smallest good
        for _ in range(12):
            m = (a * b) ** 0.5
            if good(m): b = m
            else: a = m
        return b
    need = lambda b: (lambda s: s["thin_tex"] >= around and s["trunk_tex"] >= trunk)(st(b))
    leaf_ok = lambda b: st(b)["leaf_tpm"] >= leaf_floor * ref
    cap = hi if leaf_ok(hi) else (lo if not leaf_ok(lo) else 1.0 / bisect(lambda r: leaf_ok(1.0 / r), 1.0 / hi, 1.0 / lo))
    if need(lo): return lo, True
    if not need(cap): return cap, False
    return bisect(need, lo, cap), True


def repack(ob, bark=5.0, leaf=1.0, margin=0.010, lmargin=0.010, u0=0.76, ref=5.0, check=True):
    me = ob.data
    bm, charts, best, new, isl_of = _layout(ob, bark, leaf, margin, lmargin, u0)
    st = _stats(charts, best, ref); st.update(bark=bark, charts=len(charts), bark_charts=sum(c["bark"] for c in charts))
    if check: st["covered"], st["overlapped"] = _overlap(bm, new, isl_of)
    bm.free()
    nrm = [tuple(n.vector) for n in me.corner_normals] if me.has_custom_normals else None
    # channel 1, named LAYER: rename an existing second layer (old "UV2") or create it
    if len(me.uv_layers) < 2: me.uv_layers.new(name=LAYER)
    lay = me.uv_layers[1]; lay.name = LAYER
    for li, p in new.items(): lay.data[li].uv = p
    me.uv_layers.active = me.uv_layers[0]
    me.update()
    if nrm: me.normals_split_custom_set(nrm)
    return st


def _fmt(name, st):
    s = ("LIGHTMAPUV %s bark x%.2f charts %d (bark %d) | fill %.3f | bark share of area %.3f | @ref: rect %.0f px, "
         "bark %.1f tex/m, leaf %.1f tex/m, p10 limb %.3f m -> %.1f tex around, trunk %.3f m -> %.1f tex"
         % (name, st["bark"], st["charts"], st["bark_charts"], st["fill"], st["bark_share"], st["side"], st["bark_tpm"],
            st["leaf_tpm"], st["thin_circ"], st["thin_tex"], st["trunk_circ"], st["trunk_tex"]))
    if "overlapped" in st: s += "\nLIGHTMAPOVERLAP %s covered %d overlapped %d" % (name, st["covered"], st["overlapped"])
    return s


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    opt = lambda k, d: float(a[a.index(k) + 1]) if k in a else d
    ob = bpy.data.objects[a[0]]
    kw = dict(leaf=opt("--leaf", 1.0), margin=opt("--margin", 0.010), lmargin=opt("--lmargin", 0.010), u0=opt("--u0", 0.76))
    ref = opt("--ref", 5.0)
    reached = None
    if "--auto" in a:
        b, reached = choose_bark(ob, ref=ref, around=opt("--around", 2.0), trunk=opt("--trunk", 8.0),
                                 leaf_floor=opt("--leaf-floor", 0.5), **kw)
    else:
        b = opt("--bark", 5.0)
    if reached is not None: print("LIGHTMAPAUTO %s bark x%.2f targets %s" % (ob.name, b, "MET" if reached else "SHORT (leaf floor)"))
    if "--dry" in a:
        bm, ch, best, _, _ = _layout(ob, b, kw["leaf"], kw["margin"], kw["lmargin"], kw["u0"])
        st = _stats(ch, best, ref); st.update(bark=b, charts=len(ch), bark_charts=sum(c["bark"] for c in ch)); bm.free()
        print(_fmt(ob.name, st))
    else:
        print(_fmt(ob.name, repack(ob, bark=b, ref=ref, **kw)))
        if "--fbx" in a:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from tree_wind_data import export_fbx
            export_fbx(ob, os.path.abspath(a[a.index("--fbx") + 1]))
        if "--save" in a: bpy.ops.wm.save_mainfile()

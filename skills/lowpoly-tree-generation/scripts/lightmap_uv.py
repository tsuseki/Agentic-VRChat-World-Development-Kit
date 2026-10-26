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
- bark ribbons longer than ~0.45 x the layout side are cut into pieces along the limb (at face borders, no new
  geometry), so one long thin limb chain can't force a tiny uniform scale;
- packed in chart units on shelves (long side horizontal, 90 degree rotation, no mirroring), shelf width tried over a
  range for the best fill (aspect <= 2), then scaled into 0-1. Margins are lightmap texels at the reference
  resolution: >= 2 x MARGIN_PX between bark charts, MARGIN_PX between bark and leaves, LEAF_MARGIN_PX between leaves;
- the layer is UV channel 1, named `Lightmap`.

How the engine sizes it: Unity's Progressive lightmapper (measured 2026-10-26 on 15 trees, within 1 %) gives an instance
a rect whose side is ref * sqrt(world area / UV bounding-box area) * Scale In Lightmap (an earlier Bakery bake reading
0.57x the area-only prediction fits the same model). So the texels a chart gets depend on the
fill (triangle area / bounding box) as well as on the weights: texels per metre = ref * sqrt(A / bbox) * UV scale.
`_stats` and `choose_bark` use that model.

Module:  from lightmap_uv import repack, choose_bark;  stats = repack(ob, bark=5.0, ref=10)
CLI:     blender --background <tree>.blend --python lightmap_uv.py -- <Object> [--fbx out.fbx] [--bark B | --auto]
                 [--ref 10] [--around 2] [--trunk 8] [--leaf-floor 0.5] [--leaf 1] [--margin-px 2] [--leaf-margin-px 0.5]
                 [--u0 0.76] [--dry] [--save]
Prints `LIGHTMAPUV <ob> ...` and `LIGHTMAPOVERLAP <ob> covered N overlapped M` (M must be 0).
Run it on the mesh that ships, after every geometry step (LOD thinning, card cull, base-cone clamp, pack scale); it is
deterministic from the UVMap, so re-running on the same mesh gives the same layout (idempotent).
"""
import bpy, bmesh, math, os, sys

LAYER = "Lightmap"
REF = 10.0           # reference resolution (texels/unit, Scale In Lightmap 1) for the targets and margins
MARGIN_PX = 2.0      # gap around every bark chart, lightmap texels at the reference resolution (tuned on test bakes)
LEAF_MARGIN_PX = 0.5  # gap between two leaf cards (leaves tolerate a shared rim texel; bark never shares one)


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


def _split(charts, limit):
    """Cut bark ribbons longer than `limit` (weighted chart units) into pieces along their long axis, at face borders
    (no new geometry: the cut ring's vertices just get one lightmap UV per side). Pieces stay >= 3 x the short side."""
    out = []
    for c in charts:
        L, S = max(c["w"], c["h"]) * c["k"], min(c["w"], c["h"]) * c["k"]
        n = int(math.ceil(L / limit)) if c["bark"] else 1
        n = max(1, min(n, int(L / max(3.0 * S, 1e-9))))
        if n == 1: out.append(c); continue
        ax = 0 if c["w"] >= c["h"] else 1; step = max(c["w"], c["h"]) / n
        groups = {}
        for f in c["faces"]:
            lo = min(c["pts"][l.index][ax] for l in f.loops)
            groups.setdefault(min(n - 1, int(lo / step)), []).append(f)
        for fs in groups.values():
            pts = {l.index: c["pts"][l.index] for f in fs for l in f.loops}
            xs = [q[0] for q in pts.values()]; ys = [q[1] for q in pts.values()]; x0, y0 = min(xs), min(ys)
            out.append(dict(faces=fs, pts={i: (x - x0, y - y0) for i, (x, y) in pts.items()}, w=max(xs) - x0,
                            h=max(ys) - y0, a3=sum(f.calc_area() for f in fs), bark=True, k=c["k"]))
    return out


def _shelf(rects, W):
    """First-fit decreasing-height shelves of width W. rects: (n, w, h) with w >= h. -> ({n: (x, y)}, height)."""
    shelves, out, ytop = [], {}, 0.0
    for n, w, h in rects:
        for sh in shelves:
            if sh[2] + w <= W:
                out[n] = (sh[2], sh[0]); sh[2] += w; break
        else:
            shelves.append([ytop, h, w]); out[n] = (0.0, ytop); ytop += h
    return out, ytop


def _pack(charts, A, ref, margin_px, leaf_margin_px):
    """Pack in weighted chart units (metres x k). Unity (and Bakery) size an instance's lightmap rect from world area /
    UV bounding-box area (checked on a Progressive bake, 2026-10-26: rect side = ref * sqrt(world area / bbox area)
    within 1 %), so the texels per chart unit are ref * sqrt(A / (W * H)) for a W x H layout: margins are set in
    texels at `ref` from that (two passes), and the layout is scale-free, so it packs once and is scaled to fit 0-1.
    Shelf width tried over a range; the best fill with aspect <= 2 wins. -> (placements, W, H, texels per unit)."""
    area = sum(c["w"] * c["h"] * c["k"] ** 2 for c in charts)
    longest = max(max(c["w"], c["h"]) * c["k"] for c in charts)
    tpu = ref * math.sqrt(A / (area / 0.7))
    best = None
    for _ in range(2):
        ml = leaf_margin_px / tpu; mb = max(ml, 2.0 * margin_px / tpu - ml)   # bark-bark gap >= 2 x, bark-leaf >= 1 x
        rects, mar = [], {}
        for n, c in enumerate(charts):
            m = mar[n] = mb if c["bark"] else ml
            w, h = c["w"] * c["k"] + m, c["h"] * c["k"] + m
            rects.append((n, max(w, h), min(w, h), h > w))
        rot = {n: r for n, _, _, r in rects}
        rects = sorted(((n, w, h) for n, w, h, _ in rects), key=lambda r: (-r[2], -r[1]))
        tot = sum(w * h for _, w, h in rects); side = math.sqrt(tot)
        best = None
        for f in (0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3, 1.45):
            Wt = max(side * f, longest + mb)
            pl, H = _shelf(rects, Wt)
            Wu = max(pl[n][0] + w for n, w, h in rects)
            if max(Wu, H) > 2.0 * min(Wu, H) and best is not None: continue
            fill = tot / (Wu * H)
            if best is None or fill > best[0]: best = (fill, pl, Wu, H)
        tpu = ref * math.sqrt(A / (best[2] * best[3]))
    fill, pl, Wu, H = best
    g = 1.0 / max(Wu, H)
    return {n: (x * g, y * g, rot[n], charts[n]["k"] * g, mar[n] * g) for n, (x, y) in pl.items()}, Wu * g, H * g, tpu


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


def _layout(ob, bark, leaf, margin_px, u0, ref, leaf_margin_px=LEAF_MARGIN_PX, split=0.45):
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    uv0 = bm.loops.layers.uv["UVMap"]; is_bark = _bark_pred(ob, bm, u0)
    whole = [_chart(fs, uv0, is_bark(fs[0])) for fs in _islands(bm, uv0)]
    for c in whole:
        c["k"] = bark if c["bark"] else leaf   # charts are already in metres: uniform density x weight
    A = sum(c["a3"] for c in whole)
    charts = _split(whole, split * math.sqrt(sum(c["w"] * c["h"] * c["k"] ** 2 for c in whole)))
    best, W, H, tpu = _pack(charts, A, ref, margin_px, leaf_margin_px)
    new, isl_of = {}, {}
    for n, (px, py, rot, s, m) in best.items():
        c = charts[n]
        for f in c["faces"]: isl_of[f.index] = n
        for li, (u, v) in c["pts"].items():
            u, v = u * s, v * s
            if rot: u, v = v, c["w"] * s - u
            new[li] = (px + m * 0.5 + u, py + m * 0.5 + v)
    assert len(new) == len(me.loops)
    return bm, dict(whole=whole, charts=charts, A=A, W=W, H=H, tpu=tpu, best=best), new, isl_of


def _stats(L, ref):
    """Texels at `ref` texels/unit with Scale In Lightmap 1, for a lightmapper that sizes the rect from world area /
    UV bounding-box area (Unity Progressive, Bakery): texels per metre = ref * sqrt(A / bbox) * scale."""
    whole, charts, A, W, H, best = L["whole"], L["charts"], L["A"], L["W"], L["H"], L["best"]
    side = ref * math.sqrt(A / (W * H))                        # rect side of the 0-1 square, texels
    uv_tri = sum(c["a3"] * best[n][3] ** 2 for n, c in enumerate(charts))
    kb = next((c["k"] for c in whole if c["bark"]), 0.0); kl = next((c["k"] for c in whole if not c["bark"]), 0.0)
    g = best[0][3] / charts[0]["k"]
    bark_tpm, leaf_tpm = side * g * kb, side * g * kl
    bs = sorted(min(c["w"], c["h"]) for c in whole if c["bark"])            # ribbon short side = circumference (m)
    thin = bs[len(bs) // 10] if bs else 0.0; trunk = bs[-1] if bs else 0.0
    return dict(fill=uv_tri / (W * H), bbox=W * H, side=side, bark_tpm=bark_tpm, leaf_tpm=leaf_tpm, thin_circ=thin,
                trunk_circ=trunk, thin_tex=thin * bark_tpm, trunk_tex=trunk * bark_tpm, charts=len(charts),
                bark_charts=sum(c["bark"] for c in charts), bark_share=sum(c["a3"] for c in whole if c["bark"]) / A)


def choose_bark(ob, ref=REF, around=2.0, trunk=8.0, leaf_floor=0.5, leaf=1.0, margin_px=MARGIN_PX, u0=0.76,
                lo=1.0, hi=60.0, leaf_margin_px=LEAF_MARGIN_PX):
    """Per-tree bark weight: the smallest that gives the p10 limb `around` texels and the trunk `trunk` texels at `ref`
    texels/unit, capped so leaves keep >= leaf_floor * ref texels/m. Returns (weight, reached_targets)."""
    memo = {}

    def st(b):
        if b not in memo:
            bm, L, _, _ = _layout(ob, b, leaf, margin_px, u0, ref, leaf_margin_px); memo[b] = _stats(L, ref); bm.free()
        return memo[b]

    def bisect(good, a, b):            # good(a) False, good(b) True -> smallest good
        for _ in range(12):
            m = (a * b) ** 0.5
            if good(m): b = m
            else: a = m
        return b
    need = lambda b: st(b)["thin_tex"] >= around and st(b)["trunk_tex"] >= trunk
    leaf_ok = lambda b: st(b)["leaf_tpm"] >= leaf_floor * ref
    cap = hi if leaf_ok(hi) else (lo if not leaf_ok(lo) else 1.0 / bisect(lambda r: leaf_ok(1.0 / r), 1.0 / hi, 1.0 / lo))
    if need(lo): return lo, True
    if not need(cap): return cap, False
    return bisect(need, lo, cap), True


def repack(ob, bark=5.0, leaf=1.0, margin_px=MARGIN_PX, u0=0.76, ref=REF, check=True, leaf_margin_px=LEAF_MARGIN_PX):
    me = ob.data
    bm, L, new, isl_of = _layout(ob, bark, leaf, margin_px, u0, ref, leaf_margin_px)
    st = _stats(L, ref); st.update(bark=bark)
    if check: st["covered"], st["overlapped"] = _overlap(bm, new, isl_of)
    bm.free()
    # channel 1, named LAYER: rename an existing second layer (old "UV2") or create it. Only UV data is written, so the
    # custom normals are left exactly as they were (re-setting them would re-quantise them by ~0.05 degrees).
    if len(me.uv_layers) < 2: me.uv_layers.new(name=LAYER)
    lay = me.uv_layers[1]; lay.name = LAYER
    for li, p in new.items(): lay.data[li].uv = p
    me.uv_layers.active = me.uv_layers[0]
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
    kw = dict(leaf=opt("--leaf", 1.0), margin_px=opt("--margin-px", MARGIN_PX), u0=opt("--u0", 0.76),
              leaf_margin_px=opt("--leaf-margin-px", LEAF_MARGIN_PX))
    ref = opt("--ref", REF)
    reached = None
    if "--auto" in a:
        b, reached = choose_bark(ob, ref=ref, around=opt("--around", 2.0), trunk=opt("--trunk", 8.0),
                                 leaf_floor=opt("--leaf-floor", 0.5), **kw)
    else:
        b = opt("--bark", 5.0)
    if reached is not None: print("LIGHTMAPAUTO %s bark x%.2f targets %s" % (ob.name, b, "MET" if reached else "SHORT (leaf floor)"))
    if "--dry" in a:
        bm, L, _, _ = _layout(ob, b, kw["leaf"], kw["margin_px"], kw["u0"], ref, kw["leaf_margin_px"])
        st = _stats(L, ref); st.update(bark=b); bm.free()
        print(_fmt(ob.name, st))
    else:
        print(_fmt(ob.name, repack(ob, bark=b, ref=ref, **kw)))
        if "--fbx" in a:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from tree_wind_data import export_fbx
            export_fbx(ob, os.path.abspath(a[a.index("--fbx") + 1]))
        if "--save" in a: bpy.ops.wm.save_mainfile()

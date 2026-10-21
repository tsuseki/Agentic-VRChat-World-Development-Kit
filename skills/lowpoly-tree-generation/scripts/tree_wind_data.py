# Wind data for SoftCrown.shader, in the vertex colour "Col" (byte, face corner; read in Unity as Color32 / 255):
#   R  tree height / 32 m (one value per tree)
#   G  leaf tremble weight = min(1, d / L), d = distance from the vertex to the nearest anchor (bark surface or any
#      card's stem edge): 0 where cards attach, a rigid hinge swing near them, full tremble L out. L is set per tree
#      (bisection, 0.75-5 m) so the leaves' area-weighted mean G matches the old per-card weight's ((stem-to-tip
#      fraction)^1.5 x card length / 1.5 m) where it can: palm fronds get L ~4 m and keep their tremble, dense crowns
#      stop at the 0.75 m floor (reason at the bisection below)
#   B  tremble phase: smooth 3-D value noise of the position (3 m cells; 0 on bark)
#   A  bend weight: (height above the trunk base / tree height)^2 on bark; on leaves raised toward the local mean of
#      the stem heights of the cards around (Gaussian, sigma 0.75 m), blended in by min(1, d / 0.75 m), so hanging
#      strands swing from above and every stem edge keeps the bark's value
# Every leaf weight is a function of position only (user 2026-10-21: "leaves are sometimes passing through each other
# in the wind ... make the areas near each other move in the same direction"): two cards that cross get the same
# G, B and A where they cross, so they move together. The old per-card random phase, per-card length scale and per-card
# stem A made crossing cards move apart. A is a smooth field over bark (nothing detaches when the tree bends) and also
# the one sway mask a generic foliage shader can use (e.g. Crispy Foliage "Wind Pinning Source: Vertex Colour (A)").
# Bark = faces with u >= tag / 2 (quadrant packs shift bark UVs by the tag) or u >= 0.76 (column atlas). A leaf card = a connected island
# of leaf faces; its stem enters at the bottom edge of its UV rect (branch_atlas.py pins it there), its tip is the top.
#   Module: write_wind(ob, tag=100) -> report dict;  export_fbx(ob, path)
#   CLI (re-export an existing tree object named <Species>_Tree):
#     blender -b <file>.blend -P tree_wind_data.py -- <Species> --out <dir> [--tag 100]
import bpy, sys, os, math
from mathutils import Vector
from mathutils.kdtree import KDTree

HMAX = 32.0       # metres encoded by R = 1
A_BLEND = 0.75    # distance from an anchor over which A blends from the bark field to the local stem mean (m)
L_MIN = 0.75      # floor of the per-tree tremble distance L (m)
PHASE_CELL = 3.0  # value-noise cell of the tremble phase B (m): cards in a clump share a phase, it drifts across a crown
A_SIGMA = 0.75    # Gaussian radius of the local stem-height mean in A (m)
BARK_STEP = 0.05  # bark surface sampling for the anchor distance (m)


def export_fbx(ob, path):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='OFF', path_mode='STRIP',
        use_mesh_modifiers=True, add_leaf_bones=False, object_types={'MESH'}, colors_type='SRGB')


def _hash3(x, y, z):
    h = (x * 73856093 ^ y * 19349663 ^ z * 83492791) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return ((h ^ (h >> 16)) & 0xffffff) / float(0x1000000)


def value_noise(p, cell):
    """Smooth 3-D value noise in [0, 1): random lattice values, quintic-smoothed trilinear blend."""
    q = [c / cell for c in p]; i = [math.floor(c) for c in q]
    f = [c - k for c, k in zip(q, i)]; f = [t * t * t * (t * (t * 6 - 15) + 10) for t in f]
    n = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[0] if dx else 1 - f[0]) * (f[1] if dy else 1 - f[1]) * (f[2] if dz else 1 - f[2])
                n += w * _hash3(i[0] + dx, i[1] + dy, i[2] + dz)
    return n


def write_wind(ob, tag=100.0, bark=None):
    """bark: per-polygon flags; default = detect from the UVs (quadrant layout: u >= tag / 2; column layout:
    u >= 0.76, the bark column; leaf cells end at 0.75)."""
    m = ob.data
    uv = m.uv_layers["UVMap"].data
    co = [v.co.copy() for v in m.vertices]
    if bark is None:
        u_of = [uv[p.loop_start].uv[0] for p in m.polygons]
        cut = tag * 0.5 if max(u_of) >= tag * 0.5 else 0.76
        bark = [u >= cut for u in u_of]
    bz = [co[i].z for p, b in zip(m.polygons, bark) if b for i in p.vertices] or [c.z for c in co]
    z0 = min(bz); H = max(max(c.z for c in co) - z0, 1e-3)
    r = min(1.0, H / HMAX)
    def own_a(z): return max(0.0, min(1.0, (z - z0) / H)) ** 2

    # leaf islands: union-find over the vertices of leaf faces
    par = {}
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for p, b in zip(m.polygons, bark):
        if b: continue
        vs = list(p.vertices)
        for v in vs: par.setdefault(v, v)
        for v in vs[1:]:
            ra, rb = find(vs[0]), find(v)
            if ra != rb: par[rb] = ra
    isl = {}  # root -> [u0, v0, u1, v1]
    for p, b in zip(m.polygons, bark):
        if b: continue
        e = isl.setdefault(find(p.vertices[0]), [9e9, 9e9, -9e9, -9e9])
        for li in p.loop_indices:
            u, v = uv[li].uv
            e[0] = min(e[0], u); e[1] = min(e[1], v); e[2] = max(e[2], u); e[3] = max(e[3], v)
    # stem edge (UV bottom row) of every card: its mean height gives the card's stem A, its vertices are anchors
    stem_v, ends = set(), {k: [Vector(), 0, Vector(), 0] for k in isl}  # per card: stem edge and tip edge positions
    loop_dv = {}  # leaf corner -> (card, dv): the old per-card tremble weight sets the target amount of tremble
    for p, b in zip(m.polygons, bark):
        if b: continue
        k = find(p.vertices[0]); e = isl[k]; s = ends[k]
        for li, vi in zip(p.loop_indices, p.vertices):
            dv = (uv[li].uv[1] - e[1]) / max(e[3] - e[1], 1e-6)
            loop_dv[li] = (k, max(0.0, min(1.0, dv)))
            if dv < 0.02:
                if vi not in stem_v: s[0] += co[vi]; s[1] += 1
                stem_v.add(vi)
            elif dv > 0.98: s[2] += co[vi]; s[3] += 1
    stem_a, card_g = {}, {}
    for k, s in ends.items():
        st = s[0] / max(s[1], 1); tp = s[2] / max(s[3], 1)
        stem_a[k] = own_a(st.z) if s[1] else None
        card_g[k] = min(1.0, (tp - st).length / 1.5) if s[1] and s[3] else 1.0
    old_g = {li: dv ** 1.5 * card_g[k] for li, (k, dv) in loop_dv.items()}

    # anchors: bark surface (grid samples per triangle) + stem-edge vertices
    anchors = [co[vi] for vi in stem_v]
    m.calc_loop_triangles()
    for t in m.loop_triangles:
        if not bark[t.polygon_index]: continue
        a, b_, c = (co[i] for i in t.vertices)
        n = max(1, math.ceil(max((b_ - a).length, (c - a).length, (c - b_).length) / BARK_STEP))
        for i in range(n + 1):
            for j in range(n + 1 - i):
                anchors.append(a + (b_ - a) * (i / n) + (c - a) * (j / n))
    kd = KDTree(len(anchors))
    for i, pnt in enumerate(anchors): kd.insert(pnt, i)
    kd.balance()

    leaf_v = sorted(par)
    dist = {vi: 0.0 if vi in stem_v else kd.find(co[vi])[2] for vi in leaf_v}
    # L: the area-weighted mean tremble weight over the leaves matches the old one, but L >= 0.75 m. In dense crowns
    # most leaf area lies within a few cm of some card's stem edge, so matching there would need L of a few cm: G
    # would jump from 0 to 1 inside each card, the GPU's linear interpolation over the card's 1-2 big triangles would
    # differ between crossing cards again, and they'd pass through each other. With the floor those crowns tremble
    # ~70-85 % as far as before; trees with long cards (palm fronds) get L of several metres and keep their amount.
    ltris = [(t.area, t.loops, t.vertices) for t in m.loop_triangles if not bark[t.polygon_index]]
    area = sum(a for a, _, _ in ltris) or 1.0
    g_target = sum(a * sum(old_g[li] for li in lp) / 3 for a, lp, _ in ltris) / area
    tri_d = [(a, [dist[vi] for vi in vs]) for a, _, vs in ltris]
    lo, hi = L_MIN, 5.0  # the area mean of min(1, d / L) falls as L grows
    for _ in range(40):
        L = 0.5 * (lo + hi)
        if sum(a * sum(min(1.0, d / L) for d in ds) / 3 for a, ds in tri_d) / area > g_target: lo = L
        else: hi = L
    # local mean of the stem A of the cards around each leaf vertex (cards without a stem edge use their own A)
    kl = KDTree(len(leaf_v))
    for i, vi in enumerate(leaf_v): kl.insert(co[vi], i)
    kl.balance()
    sv = [stem_a[find(vi)] if stem_a[find(vi)] is not None else own_a(co[vi].z) for vi in leaf_v]
    G, B, A = {}, {}, {}
    for vi in leaf_v:
        d = dist[vi]
        sw = ss = 0.0
        for _, j, dd in kl.find_range(co[vi], 2 * A_SIGMA):
            g = math.exp(-dd * dd / (2 * A_SIGMA * A_SIGMA)); sw += g; ss += g * sv[j]
        oa = own_a(co[vi].z)
        G[vi] = min(1.0, d / L)
        B[vi] = value_noise(co[vi], PHASE_CELL)
        A[vi] = oa + (max(oa, ss / sw) - oa) * min(1.0, d / A_BLEND)

    ca = m.color_attributes.get("Col")
    if ca is not None and (ca.domain != 'CORNER' or ca.data_type != 'BYTE_COLOR'):
        m.color_attributes.remove(ca); ca = None
    if ca is None: ca = m.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    gsum = n = 0
    for p, b in zip(m.polygons, bark):
        for li, vi in zip(p.loop_indices, p.vertices):
            if b:
                ca.data[li].color_srgb = (r, 0.0, 0.0, own_a(co[vi].z))  # bytes as written: Unity reads them unconverted
            else:
                ca.data[li].color_srgb = (r, G[vi], B[vi], A[vi]); gsum += G[vi]; n += 1
    m.color_attributes.active_color = ca
    return dict(height=round(H, 2), R=round(r, 3), cards=len(isl), tremble_L=round(L, 3),
                flutter_mean=round(gsum / max(n, 1), 3), flutter_target=round(g_target, 3), anchors=len(anchors))


if __name__ == "__main__" and "--" in sys.argv:
    argv = sys.argv[sys.argv.index("--") + 1:]
    def _opt(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
    NAME = argv[0]; OUT = os.path.abspath(_opt("--out")) + os.sep; TAG = float(_opt("--tag", "100"))
    ob = bpy.data.objects[f"{NAME}_Tree"]
    rep = write_wind(ob, TAG)
    export_fbx(ob, OUT + f"{NAME}_Tree.fbx")
    bpy.ops.wm.save_mainfile()
    print("WIND", NAME, rep)

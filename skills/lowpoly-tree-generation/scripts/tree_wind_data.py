# Wind data for SoftCrown.shader, in the vertex colour "Col" (byte, face corner; read in Unity as Color32 / 255):
#   R  tree height / 32 m (one value per tree)
#   G  leaf flutter weight: 0 on bark and along the card's stem edge, rising to the tip; scaled by card length / 1.5 m
#      (capped at 1), so every card flutters through about the same angle
#   B  per-card random phase (0 on bark)
#   A  bend weight ((height above the trunk base / tree height)^2); a leaf card never gets less than its stem's value
# A is a smooth field over bark (nothing detaches when the tree bends); leaf cards take max(own, stem) so hanging
# strands swing from their stems. A is also the one sway mask a generic foliage shader can use (e.g. Crispy Foliage
# "Wind Pinning Source: Vertex Colour (A)").
# Bark = faces with u >= tag / 2 (quadrant packs shift bark UVs by the tag) or u >= 0.76 (column atlas). A leaf card = a connected island
# of leaf faces; its stem enters at the bottom edge of its UV rect (branch_atlas.py pins it there), its tip is the top.
#   Module: write_wind(ob, tag=100) -> report dict;  export_fbx(ob, path)
#   CLI (re-export an existing tree object named <Species>_Tree):
#     blender -b <file>.blend -P tree_wind_data.py -- <Species> --out <dir> [--tag 100]
import bpy, sys, os, math
from mathutils import Vector

HMAX = 32.0  # metres encoded by R = 1
LREF = 1.5   # card length (m) that gets the full flutter weight


def export_fbx(ob, path):
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='OFF', path_mode='STRIP',
        use_mesh_modifiers=True, add_leaf_bones=False, object_types={'MESH'}, colors_type='SRGB')


def write_wind(ob, tag=100.0, bark=None):
    """bark: per-polygon flags; default = detect from the UVs (quadrant layout: u >= tag / 2; column layout:
    u >= 0.76, the bark column; leaf cells end at 0.75)."""
    m = ob.data
    uv = m.uv_layers["UVMap"].data
    co = [v.co for v in m.vertices]
    if bark is None:
        u_of = [uv[p.loop_start].uv[0] for p in m.polygons]
        cut = tag * 0.5 if max(u_of) >= tag * 0.5 else 0.76
        bark = [u >= cut for u in u_of]
    bz = [co[i].z for p, b in zip(m.polygons, bark) if b for i in p.vertices] or [c.z for c in co]
    z0 = min(bz); H = max(max(c.z for c in co) - z0, 1e-3)
    r = min(1.0, H / HMAX)

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
    isl = {}  # root -> [u0, v0, u1, v1, sum xyz]
    for p, b in zip(m.polygons, bark):
        if b: continue
        k = find(p.vertices[0]); e = isl.setdefault(k, [9e9, 9e9, -9e9, -9e9, 0.0, 0.0, 0.0])
        for li in p.loop_indices:
            u, v = uv[li].uv
            e[0] = min(e[0], u); e[1] = min(e[1], v); e[2] = max(e[2], u); e[3] = max(e[3], v)
        c = p.center; e[4] += c.x; e[5] += c.y; e[6] += c.z
    phase = {}
    for k, e in isl.items():  # deterministic per-card random from the card's position
        h = math.sin(e[4] * 12.9898 + e[5] * 78.233 + e[6] * 37.719) * 43758.5453
        phase[k] = h - math.floor(h)
    ends = {k: [Vector(), 0, Vector(), 0] for k in isl}  # per card: stem edge and tip edge positions
    for p, b in zip(m.polygons, bark):
        if b: continue
        k = find(p.vertices[0]); e = isl[k]; s = ends[k]
        for li, vi in zip(p.loop_indices, p.vertices):
            dv = (uv[li].uv[1] - e[1]) / max(e[3] - e[1], 1e-6)
            if dv < 0.02: s[0] += co[vi]; s[1] += 1
            elif dv > 0.98: s[2] += co[vi]; s[3] += 1
    stem_a, card_g = {}, {}
    for k, s in ends.items():
        st = s[0] / max(s[1], 1); tp = s[2] / max(s[3], 1)
        stem_a[k] = max(0.0, min(1.0, (st.z - z0) / H)) ** 2
        card_g[k] = min(1.0, (tp - st).length / LREF) if s[1] and s[3] else 1.0

    ca = m.color_attributes.get("Col")
    if ca is not None and (ca.domain != 'CORNER' or ca.data_type != 'BYTE_COLOR'):
        m.color_attributes.remove(ca); ca = None
    if ca is None: ca = m.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    gmax = 0.0
    for p, b in zip(m.polygons, bark):
        k = None if b else find(p.vertices[0])
        e = None if b else isl[k]
        for li, vi in zip(p.loop_indices, p.vertices):
            a = max(0.0, min(1.0, (co[vi].z - z0) / H)) ** 2
            if b:
                g = ph = 0.0
            else:
                a = max(a, stem_a[k])
                dv = max(0.0, (uv[li].uv[1] - e[1]) / max(e[3] - e[1], 1e-6))  # 0 along the stem edge, 1 at the tip
                g = min(1.0, dv) ** 1.5 * card_g[k]  # the card hinges on its stem edge
                ph = phase[k]
            gmax = max(gmax, g)
            ca.data[li].color_srgb = (r, g, ph, a)  # bytes as written: Unity reads them unconverted
    m.color_attributes.active_color = ca
    return dict(height=round(H, 2), R=round(r, 3), cards=len(isl), flutter_max=round(gmax, 3))


if __name__ == "__main__" and "--" in sys.argv:
    argv = sys.argv[sys.argv.index("--") + 1:]
    def _opt(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
    NAME = argv[0]; OUT = os.path.abspath(_opt("--out")) + os.sep; TAG = float(_opt("--tag", "100"))
    ob = bpy.data.objects[f"{NAME}_Tree"]
    rep = write_wind(ob, TAG)
    export_fbx(ob, OUT + f"{NAME}_Tree.fbx")
    bpy.ops.wm.save_mainfile()
    print("WIND", NAME, rep)

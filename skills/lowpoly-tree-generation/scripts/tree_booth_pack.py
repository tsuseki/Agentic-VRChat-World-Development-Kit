# Package a built tree for sale/distribution: one material per LOD mesh and a billboard LOD2.
#   blender -b <src>/<Species>_Tree.blend -P tree_booth_pack.py -- <Species> --atlas <Tex> --out <dir>
#           [--src <dir>] [--bb 512] [--tag 100]
# Input: the .blend written by tree_family_build.py --lod1 (objects <Species>_Tree_LOD0 / _LOD1, materials
# [bark, leaves], bark UVs in tile space). Output:
#   <out>/<Species>_Tree.fbx         LOD0, LOD1 (material <Tex>_Tree) + LOD2 (material <Species>_Billboard)
#   <out>/<Species>_Billboard_raw.png  2 orthographic albedo views side by side (front | side), alpha;
#                                      finish with tree_billboard_fix.py (colour dilation into alpha 0)
#   <src>/<Species>_Booth.blend
# Bark faces get u += tag (TreeAtlas.shader wraps them into the atlas bark rect); leaf UVs are unchanged
# (tree_atlas.py keeps the leaf cells where they were). LOD2 = two crossed vertical quads (3x3 grid each)
# with crown-ellipsoid normals, so it shades like the LOD0/LOD1 canopy.
import bpy, bmesh, math, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
def _opt(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
NAME = argv[0]

ATL = _opt("--atlas")
OUT = os.path.abspath(_opt("--out")) + os.sep
SRC = os.path.abspath(_opt("--src", os.path.dirname(bpy.data.filepath))) + os.sep
BB = int(_opt("--bb", "512"))
TAG = float(_opt("--tag", "100"))
os.makedirs(OUT, exist_ok=True); os.makedirs(SRC, exist_ok=True)

lods = [bpy.data.objects[f"{NAME}_Tree_LOD{i}"] for i in (0, 1)]
L0 = lods[0]
sc = bpy.context.scene

# ---------------------------------------------------------------- billboard render (albedo, unlit)
def emission_mat(name, image, alpha):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = image; tx.interpolation = 'Linear'
    nt.links.new(tx.outputs[0], em.inputs[0])
    if alpha:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        mt = nt.nodes.new("ShaderNodeMath"); mt.operation = 'GREATER_THAN'; mt.inputs[1].default_value = 0.45
        nt.links.new(tx.outputs[1], mt.inputs[0])
        nt.links.new(mt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs[0])
    else:
        nt.links.new(em.outputs[0], out.inputs[0])
    return m

orig = [s.material for s in L0.material_slots]
bark_img = leaf_img = None
for n in orig[0].node_tree.nodes:  # the bark albedo the builder used (tile-space UVs, REPEAT)
    if n.type == 'TEX_IMAGE' and "Albedo" in n.image.name: bark_img = n.image
for n in orig[1].node_tree.nodes:
    if n.type == 'TEX_IMAGE': leaf_img = n.image
L0.material_slots[0].material = emission_mat("__bb_bark", bark_img, False)
L0.material_slots[1].material = emission_mat("__bb_leaf", leaf_img, True)
for o in sc.objects: o.hide_render = o is not L0

vs = [L0.matrix_world @ v.co for v in L0.data.vertices]
mn = Vector((min(v.x for v in vs), min(v.y for v in vs), 0.0)); mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
c = (mn + mx) / 2
H = mx.z
S = max(mx.x - mn.x, mx.y - mn.y, H) * 1.02  # square view; quads use the same square

cam_d = bpy.data.cameras.new("__bb_cam"); cam_d.type = 'ORTHO'; cam_d.ortho_scale = S
cam = bpy.data.objects.new("__bb_cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.clip_start = 0.01; cam_d.clip_end = 200
sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = False
sc.render.film_transparent = True; sc.render.filter_size = 0.8
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.resolution_x = sc.render.resolution_y = BB; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
if sc.world is None: sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True; sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
mid = Vector((c.x, c.y, S / 2))
views = [("front", mid + Vector((0, -50, 0)), (math.radians(90), 0, 0)),          # looks along +Y: XZ plane
         ("side", mid + Vector((50, 0, 0)), (math.radians(90), 0, math.radians(90)))]  # looks along -X: YZ plane
paths = []
for tag, pos, rot in views:
    cam.location = pos; cam.rotation_euler = rot
    p = OUT + f"__bb_{tag}.png"; sc.render.filepath = p; bpy.ops.render.render(write_still=True); paths.append(p)
sheet = bpy.data.images.new("__bb_sheet", BB * 2, BB, alpha=True)
px = [0.0] * (BB * 2 * BB * 4)
for k, p in enumerate(paths):
    im = bpy.data.images.load(p); src = list(im.pixels)
    for y in range(BB):
        row = src[y * BB * 4:(y + 1) * BB * 4]
        o = (y * BB * 2 + k * BB) * 4
        px[o:o + BB * 4] = row
    bpy.data.images.remove(im); os.remove(p)
sheet.pixels = px; sheet.filepath_raw = OUT + f"{NAME}_Billboard_raw.png"; sheet.file_format = 'PNG'; sheet.save()
for s, m in zip(L0.material_slots, orig): s.material = m
for o in sc.objects: o.hide_render = False
bpy.data.objects.remove(cam, do_unlink=True)

# ---------------------------------------------------------------- LOD2 mesh
leafv = [L0.matrix_world @ L0.data.vertices[i].co for p in L0.data.polygons if p.material_index == 1 for i in p.vertices]
lmn = Vector((min(v.x for v in leafv), min(v.y for v in leafv), min(v.z for v in leafv)))
lmx = Vector((max(v.x for v in leafv), max(v.y for v in leafv), max(v.z for v in leafv)))
cc = (lmn + lmx) / 2; rr = (lmx - lmn) / 2 * 1.05
me = bpy.data.meshes.new(f"{NAME}_Tree_LOD2"); bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap"); uv2 = bm.loops.layers.uv.new("UV2")
G = 3
for k in range(2):  # k 0: XZ quad (front view, u cell 0); k 1: YZ quad (side view, u cell 1)
    grid = {}
    for i in range(G + 1):
        for j in range(G + 1):
            s, t = i / G, j / G
            h = (s - 0.5) * S
            p = Vector((c.x + h, c.y, t * S)) if k == 0 else Vector((c.x, c.y + h, t * S))  # side camera: image right = +Y
            grid[i, j] = (bm.verts.new(p), (k * 0.5 + s * 0.5, t))
    for i in range(G):
        for j in range(G):
            q = [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
            f = bm.faces.new([v for v, _ in q])
            for lp, (_, u) in zip(f.loops, q):
                lp[uvl].uv = u; lp[uv2].uv = (u[0], u[1] * 0.5 + 0.5 * k)  # simple non-overlapping lightmap UVs
bm.to_mesh(me); bm.free()
L2 = bpy.data.objects.new(f"{NAME}_Tree_LOD2", me); sc.collection.objects.link(L2)
for p in me.polygons: p.use_smooth = True
loops = []
for p in me.polygons:
    for li in p.loop_indices:
        v = me.vertices[me.loops[li].vertex_index].co
        d = v - cc
        loops.append(Vector((d.x / rr.x ** 2, d.y / rr.y ** 2, d.z / rr.z ** 2)).normalized())
me.normals_split_custom_set(loops)
mbb = bpy.data.materials.new(f"{NAME}_Billboard"); me.materials.append(mbb)

# ---------------------------------------------------------------- one material on LOD0/LOD1, tagged bark UVs
mt = bpy.data.materials.get(f"{ATL}_Tree") or bpy.data.materials.new(f"{ATL}_Tree")
for o in lods:
    m = o.data; uv = m.uv_layers["UVMap"].data
    for p in m.polygons:
        if p.material_index == 0:
            for li in p.loop_indices: uv[li].uv = (uv[li].uv[0] + TAG, uv[li].uv[1])
        p.material_index = 0
    m.materials.clear(); m.materials.append(mt)

bpy.ops.object.select_all(action='DESELECT')
for o in lods + [L2]: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT + f"{NAME}_Tree.fbx", use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
    axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='OFF', path_mode='STRIP',
    use_mesh_modifiers=True, add_leaf_bones=False, object_types={'MESH'})
bpy.ops.wm.save_as_mainfile(filepath=SRC + f"{NAME}_Booth.blend", relative_remap=False)
tri = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
print("PACK", NAME, "tris", [tri(o) for o in lods + [L2]], "billboard", f"{BB * 2}x{BB}", "square_m", round(S, 2))

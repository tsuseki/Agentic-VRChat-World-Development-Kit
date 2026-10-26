"""Headless Blender: Tripo FBX (+ .fbm texture) -> collapse-decimated triangle FBX at a triangle budget, UV0 kept.
Fallback only, for a strict triangle budget (the default recipe keeps the generated mesh as-is). Runs BEFORE retopo_prep.py. Writes <out_dir>/<name>.fbx and <out_dir>/<name>.fbm/ (texture copy).
Usage: blender -b --factory-startup --python protected_decimate.py -- <in.fbx> <out_dir> <name> <target_tris> [protect_face=0]
protect_face=1 keeps the front of the head (verts facing -Y, FACE_Z0-FACE_Z1 of the height, centre FACE_W of the width) at full source
resolution through an inverted decimate vertex group, so the embroidered eyes, glasses and mouth keep their UV mapping; the rest takes the cut."""
import bpy, bmesh, sys, os, shutil
argv = sys.argv[sys.argv.index("--") + 1:]
src, out, name, target = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2], int(argv[3])
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
for o in list(bpy.context.scene.objects):
    if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
bm.to_mesh(ob.data); bm.free()
t0 = len(ob.data.polygons)
PROTECT = len(argv) > 4 and argv[4] == "1"
Z0, Z1, XW = (float(os.environ.get(k, d)) for k, d in (("FACE_Z0", "0.45"), ("FACE_Z1", "0.82"), ("FACE_W", "0.6")))
if PROTECT:
    me = ob.data; me.update(); vs = [v.co for v in me.vertices]
    zmin, zmax = min(v.z for v in vs), max(v.z for v in vs); xmin, xmax = min(v.x for v in vs), max(v.x for v in vs); xc = (xmin + xmax) / 2; xw = xmax - xmin
    idx = [v.index for v in me.vertices if v.normal.y < -0.3 and Z0 < (v.co.z - zmin) / (zmax - zmin) < Z1 and abs(v.co.x - xc) < XW / 2 * xw]
    vg = ob.vertex_groups.new(name="face"); vg.add(idx, 1.0, "REPLACE"); print("FACE_VERTS", len(idx))
md = ob.modifiers.new("dec", "DECIMATE"); md.decimate_type = "COLLAPSE"; md.ratio = min(1.0, target / t0); md.use_collapse_triangulate = True
if PROTECT: md.vertex_group = "face"; md.invert_vertex_group = True
bpy.ops.object.modifier_apply(modifier="dec")
print(f"PREDEC {t0} -> {len(ob.data.polygons)} tris")
bpy.ops.object.shade_smooth()
fbx = os.path.join(out, name + ".fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, axis_forward="-Z", axis_up="Y", object_types={"MESH"}, path_mode="STRIP", embed_textures=False, mesh_smooth_type="FACE")
fbm = os.path.join(out, name + ".fbm"); os.makedirs(fbm, exist_ok=True)
sfbm = os.path.splitext(src)[0] + ".fbm"
for f in os.listdir(sfbm): shutil.copy(os.path.join(sfbm, f), os.path.join(fbm, f))

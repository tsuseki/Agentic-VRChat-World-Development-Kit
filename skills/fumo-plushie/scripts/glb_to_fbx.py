"""Headless Blender: image-to-3D GLB -> Unity-ready FBX + base-colour PNG.
Scales to the seated height (m), origin at bottom centre, front = -Y, transforms applied.
Usage: python .omp/scripts/tool.py blender --script glb_to_fbx.py -- <in.glb> <out_dir> <name> <height_m>
Writes <out>/<name>.fbx and <name>_BaseColor.png (the next scripts expect the texture beside the FBX).
"""
import bpy, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out, name, height = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2], float(argv[3])
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
# Blender 5 defaults to AgX, which desaturates saved images; Standard writes the pixels unchanged.
_vs = bpy.context.scene.view_settings; _vs.view_transform = "Standard"; _vs.look = "None"; _vs.exposure = 0; _vs.gamma = 1
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert len(meshes) == 1, f"expected 1 mesh, got {len(meshes)}"
ob = meshes[0]
# unparent + bake world transform
mw = ob.matrix_world.copy()
ob.parent = None
ob.matrix_world = mw
for o in list(bpy.context.scene.objects):
    if o is not ob:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

vs = [v.co for v in ob.data.vertices]
mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
k = height / (mx.z - mn.z)
off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
for v in ob.data.vertices:
    v.co = (v.co - off) * k
ob.name = ob.data.name = name
bpy.ops.object.shade_smooth()

# texture out
mat = ob.material_slots[0].material
mat.name = "M_" + name
img = None
for n in mat.node_tree.nodes:
    if n.type == "TEX_IMAGE" and n.image:
        links = [l for l in mat.node_tree.links if l.from_node == n and l.to_socket.name == "Base Color"]
        if links or img is None:
            img = n.image
tex_path = os.path.join(out, f"{name}_BaseColor.png")
img.filepath_raw = tex_path
img.file_format = "PNG"
img.save()
others = [n.image.name for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and n.image != img]

fbx = os.path.join(out, f"{name}.fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_scale_options="FBX_SCALE_ALL",
                         axis_forward="-Z", axis_up="Y", object_types={"MESH"}, path_mode="STRIP",
                         embed_textures=False, mesh_smooth_type="FACE")
d = mx - mn
print(f"REPORT {name} tris={sum(len(p.vertices)-2 for p in ob.data.polygons)} size={tuple(round(c*k,3) for c in d)} tex={img.size[:]} other_tex={others} -> {fbx}")

"""Headless Blender: bake an existing texture from the old UV layout onto a new UV layout of the same surface
(e.g. a Tripo Studio Smart UV re-unwrap, which drops the texture).
Usage: ... -- <old.fbx> <old_tex.png> <new.(fbx|glb)> <out_dir> <name> [size=2048]
The old mesh stays in its own frame; the new one is fitted onto it (bbox height and bottom-centre, then the best of
the 90-degree turns and a mirror about Z by nearest-vertex distance). Cycles emit bake, selected (old) -> active (new),
small ray distance, on the GPU. Writes <out>/<name>_BaseColor_<size>.png and <out>/<name>.fbx (new mesh in the old
frame, UV0 'UVMap') and a REPORT line: faces, turn, meanSurfaceGap (should be ~0 for the same surface), old height."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from cycles_gpu import use_gpu
a = sys.argv[sys.argv.index("--") + 1:]
old_fbx, old_tex, new_path, out, name = [os.path.abspath(x) if i < 4 else x for i, x in enumerate(a[:5])]
SIZE = int(a[5]) if len(a) > 5 else 2048
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def imp(path):
    before = set(bpy.context.scene.objects)
    (bpy.ops.import_scene.fbx if path.lower().endswith(".fbx") else bpy.ops.import_scene.gltf)(filepath=path)
    new = [o for o in bpy.context.scene.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for v in ob.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
    while len(ob.data.uv_layers) > 1: ob.data.uv_layers.remove(ob.data.uv_layers[1])
    ob.data.uv_layers[0].name = "UVMap"
    return ob, lo, hi


old, olo, ohi = imp(old_fbx); old.name = "old"
new, nlo, nhi = imp(new_path); new.name = "new"
o_bc = Vector(((olo.x + ohi.x) / 2, (olo.y + ohi.y) / 2, olo.z)); n_bc = Vector(((nlo.x + nhi.x) / 2, (nlo.y + nhi.y) / 2, nlo.z))
s = (ohi.z - olo.z) / (nhi.z - nlo.z)
for v in new.data.vertices: v.co = (v.co - n_bc) * s      # bottom-centre at origin, old height
for v in old.data.vertices: v.co = v.co - o_bc               # moved back after the bake
d_old = ohi - olo; d_new = (nhi - nlo) * s
# the service may export with another facing: try 90-degree turns (and a mirror) about Z, keep the one that fits
kd = KDTree(len(old.data.vertices))
for i, v in enumerate(old.data.vertices): kd.insert(v.co, i)
kd.balance()
base = [v.co.copy() for v in new.data.vertices]
step = max(1, len(base) // 600)
best = None
for mirror in (1, -1):
    for k in range(4):
        R = Matrix.Rotation(math.radians(90 * k), 3, "Z") @ Matrix.Diagonal((mirror, 1, 1))
        err = sum(kd.find(R @ c)[2] for c in base[::step]) / len(base[::step])
        if best is None or err < best[0]: best = (err, R, k, mirror)
err, R, k, mirror = best
for v, c in zip(new.data.vertices, base): v.co = R @ c
if mirror < 0: new.data.flip_normals()
mismatch = err
# old: emission of the old texture
img_old = bpy.data.images.load(old_tex)
m = bpy.data.materials.new("src"); m.use_nodes = True; nt = m.node_tree
for n in list(nt.nodes):
    if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img_old; tn.interpolation = "Cubic"
em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(tn.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs[0])
old.data.materials.clear(); old.data.materials.append(m)
# new: target image node (active) on the new UV
tgt = bpy.data.images.new(f"{name}_bake", SIZE, SIZE, alpha=False); tgt.colorspace_settings.name = "sRGB"
m2 = bpy.data.materials.new(f"M_{name}"); m2.use_nodes = True; nt2 = m2.node_tree
t2 = nt2.nodes.new("ShaderNodeTexImage"); t2.image = tgt; nt2.nodes.active = t2
nt2.links.new(t2.outputs[0], nt2.nodes["Principled BSDF"].inputs["Base Color"])
new.data.materials.clear(); new.data.materials.append(m2)

sc = bpy.context.scene
use_gpu(sc); sc.cycles.samples = 4
sc.view_settings.view_transform = "Standard"
bk = sc.render.bake; bk.use_selected_to_active = True; bk.cage_extrusion = 0.002; bk.max_ray_distance = 0.004; bk.margin = 16
bpy.ops.object.select_all(action="DESELECT"); old.select_set(True); new.select_set(True); bpy.context.view_layer.objects.active = new
bpy.ops.object.bake(type="EMIT")
tgt.filepath_raw = f"{out}/{name}_BaseColor_{SIZE}.png"; tgt.file_format = "PNG"; tgt.save()
# export the new mesh with the baked texture
bpy.data.objects.remove(old, do_unlink=True)
for v in new.data.vertices: v.co = v.co + o_bc             # back into the old mesh's frame
bpy.ops.object.select_all(action="DESELECT"); new.select_set(True); bpy.context.view_layer.objects.active = new
new.name = name; new.data.name = name
bpy.ops.export_scene.fbx(filepath=f"{out}/{name}.fbx", use_selection=True, apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP")
sides = [len(p.vertices) for p in new.data.polygons]
print(f"REPORT {name} newFaces={len(sides)} quads={sides.count(4)} tris={sides.count(3)} turn={90 * k}deg mirror={mirror < 0} "
      f"meanSurfaceGap={mismatch * 1000:.3f}mm oldHeight={d_old.z:.4f} dimsOld={tuple(round(x, 4) for x in d_old)} "
      f"dimsNew={tuple(round(x, 4) for x in d_new)}", flush=True)

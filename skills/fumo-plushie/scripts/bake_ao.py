"""Headless Blender: soft ambient occlusion for a Light-Volume-lit plush, baked to the existing UV0 (no cage, no UV change).
Per-vertex AO is ray-cast against a watertight voxel proxy (layered hair/cloth shells self-occlude into blotches under Cycles AO), on a once-subdivided
copy of the final mesh for density, stored as a point colour attribute and emit-baked to UV0 with an 8 px margin.
Usage: blender -b --factory-startup --python bake_ao.py -- <in.fbx> <out.npy> [size=2048] [dist_m=0.02]
Writes a float32 (size, size) array, image row 0 = top, 1 = unoccluded."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from cycles_gpu import use_gpu
a = sys.argv[sys.argv.index("--") + 1:]; src, out = os.path.abspath(a[0]), os.path.abspath(a[1])
N = int(a[2]) if len(a) > 2 else 2048; DIST = float(a[3]) if len(a) > 3 else 0.02
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.view_settings.view_transform = "Standard"
bpy.ops.import_scene.fbx(filepath=src)
ob = [o for o in sc.objects if o.type == "MESH"][0]
mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[1])
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free(); me.update()
# watertight proxy
prox = ob.copy(); prox.data = me.copy(); sc.collection.objects.link(prox)
rm = prox.modifiers.new("vox", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.0015
sm = prox.modifiers.new("sm", "CORRECTIVE_SMOOTH"); sm.iterations = 4; sm.use_only_smooth = True
bvh = BVHTree.FromObject(prox, bpy.context.evaluated_depsgraph_get())
rng = np.random.default_rng(1); NR = 96
u1, u2 = rng.random(NR), rng.random(NR); rr = np.sqrt(u1); th = 2 * math.pi * u2
hemi = np.stack([rr * np.cos(th), rr * np.sin(th), np.sqrt(1 - u1)], 1)
ao = np.ones(len(me.vertices))
for i, v in enumerate(me.vertices):
    co, n, _, _ = bvh.find_nearest(v.co)
    if co is None: continue
    n = n.normalized(); t = n.orthogonal().normalized(); b = n.cross(t); o = co + n * 0.0008
    hit = sum(1 for d in hemi if bvh.ray_cast(o, t * d[0] + b * d[1] + n * d[2], DIST)[0] is not None)
    ao[i] = 1 - hit / NR
bpy.data.objects.remove(prox, do_unlink=True)
ca = me.color_attributes.new("AO", "FLOAT_COLOR", "POINT")
for i, v in enumerate(ao): ca.data[i].color = (v, v, v, 1)
use_gpu(sc); sc.cycles.samples = 4
img = bpy.data.images.new("ao", N, N, alpha=False, float_buffer=True); img.colorspace_settings.name = "Non-Color"
m = bpy.data.materials.new("bake"); m.use_nodes = True; nt = m.node_tree
for nd in list(nt.nodes): nt.nodes.remove(nd)
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "AO"; em = nt.nodes.new("ShaderNodeEmission"); mo = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(at.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], mo.inputs["Surface"])
bn = nt.nodes.new("ShaderNodeTexImage"); bn.image = img; nt.nodes.active = bn
me.materials.clear(); me.materials.append(m)
sc.render.bake.margin = 8; sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type="EMIT")
px = np.empty(N * N * 4, np.float32); img.pixels.foreach_get(px)
arr = px.reshape(N, N, 4)[..., 0][::-1].copy()    # Blender rows are bottom-up
np.save(out, arr)
print("AO_OK", out, "vertAO mean", round(float(ao.mean()), 3), "min", round(float(ao.min()), 3), "texAO mean", round(float(arr.mean()), 3))

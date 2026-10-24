"""Headless Blender: prepare a plush for probe / Light Volume lighting (no lightmap UVs needed).
FBX (texture beside it as <stem>_BaseColor.png) -> collapse-decimate to a triangle budget
(keeps UV0 and the original texture; target >= current tris skips decimation) -> per-vertex AO against a
watertight voxel proxy -> AO baked to UV0 -> BaseColor x AO -> <tex>² PNG.
Also renders unlit previews (original / decimated / decimated + AO) for checking texture warp.
Usage: python .omp/scripts/tool.py blender --script fumo_lv_prep.py -- <in.fbx> <out_dir> <name> <target_tris> [tex=512] [ao_strength=0.8] [ao_dist_m=0.02]
Writes <out>/<name>.fbx, <name>_BaseColor.png (with AO), <name>_AO.png, previews <name>_prev_{orig,dec,decao}_{front,34}.png
"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
src, out, name, target = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2], int(argv[3])
TEX = int(argv[4]) if len(argv) > 4 else 512
AO_STR = float(argv[5]) if len(argv) > 5 else 0.8
AO_DIST = float(argv[6]) if len(argv) > 6 else 0.02
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
vs = sc.view_settings; vs.view_transform = "Standard"; vs.look = "None"; vs.exposure = 0; vs.gamma = 1  # AgX would desaturate saved textures
bpy.ops.import_scene.fbx(filepath=src)
ob = [o for o in sc.objects if o.type == "MESH"][0]
mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
for o in list(sc.objects):
    if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.context.selected_objects: o.select_set(False)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[1])
src_img = bpy.data.images.load(os.path.splitext(src)[0] + "_BaseColor.png")
def tex_mat(nm, img):
    m = bpy.data.materials.new(nm); m.use_nodes = True
    t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = img
    m.node_tree.links.new(t.outputs[0], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"]); return m
me.materials.clear(); me.materials.append(tex_mat("src", src_img))
tris0 = sum(len(p.vertices) - 2 for p in me.polygons)
# --- previews (Workbench, texture colour, flat) from front and 3/4
vs_ = [v.co for v in me.vertices]; mn = Vector([min(v[i] for v in vs_) for i in range(3)]); mx = Vector([max(v[i] for v in vs_) for i in range(3)])
h = mx.z - mn.z; c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + h / 2))
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = sc.render.resolution_y = 800
sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.25, 0.25, 0.27)
cd = bpy.data.cameras.new("cam"); cd.lens = 70; cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
def previews(tag):
    for nm, ang in [("front", 0), ("34", 35)]:
        a = math.radians(ang); cam.location = c + Vector((math.sin(a) * h * 2.7, -math.cos(a) * h * 2.7, 0.12 * h))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, f"{name}_prev_{tag}_{nm}.png"); bpy.ops.render.render(write_still=True)
previews("orig")
# --- AO per vertex, ray-cast against a watertight voxel proxy (generated plushes have layered, intersecting
# hair/cloth shells; Cycles AO on them self-occludes into per-chart blotches). Stored as a colour attribute
# on the full-res mesh so decimation interpolates it, then baked to UV0 after decimation.
from mathutils.bvhtree import BVHTree
prox = ob.copy(); prox.data = me.copy(); sc.collection.objects.link(prox)
rm = prox.modifiers.new("vox", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.0015 * max(1.0, h / 0.25)
sm = prox.modifiers.new("sm", "CORRECTIVE_SMOOTH"); sm.iterations = 4; sm.use_only_smooth = True
dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(prox, dg)
rng = np.random.default_rng(1); NR = 96
u1, u2 = rng.random(NR), rng.random(NR); rr = np.sqrt(u1); th = 2 * math.pi * u2   # cosine-weighted hemisphere
hemi = np.stack([rr * np.cos(th), rr * np.sin(th), np.sqrt(1 - u1)], 1)
aov_ = np.ones(len(me.vertices))
for i, v in enumerate(me.vertices):
    co, n, _, _ = bvh.find_nearest(v.co)
    if co is None: continue
    n = n.normalized(); t = n.orthogonal().normalized(); b = n.cross(t); o = co + n * 0.0008
    hit = 0
    for d in hemi:
        if bvh.ray_cast(o, t * d[0] + b * d[1] + n * d[2], AO_DIST)[0] is not None: hit += 1
    aov_[i] = 1 - hit / NR
bpy.data.objects.remove(prox, do_unlink=True)
ca = me.color_attributes.new("AO", "FLOAT_COLOR", "POINT")
for i, a in enumerate(aov_): ca.data[i].color = (a, a, a, 1)
# --- decimate (collapse) to the triangle budget; Blender collapse keeps UV seams intact
dm = ob.modifiers.new("dec", "DECIMATE"); dm.decimate_type = "COLLAPSE"; dm.use_collapse_triangulate = True
dm.ratio = min(1.0, target / tris0)
bpy.ops.object.modifier_apply(modifier="dec")
tris1 = sum(len(p.vertices) - 2 for p in me.polygons)
previews("dec")
# --- bake the AO attribute to UV0 (emission bake), then BaseColor x AO
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 4
ao_img = bpy.data.images.new(name + "_AO", TEX, TEX, alpha=False, float_buffer=True)
bake_mat = bpy.data.materials.new("bake"); bake_mat.use_nodes = True; nt = bake_mat.node_tree
for nd in list(nt.nodes): nt.nodes.remove(nd)
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "AO"; em = nt.nodes.new("ShaderNodeEmission"); mo = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(at.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], mo.inputs["Surface"])
bn = nt.nodes.new("ShaderNodeTexImage"); bn.image = ao_img; nt.nodes.active = bn
me.materials.clear(); me.materials.append(bake_mat)
sc.render.bake.margin = 6; sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type="EMIT")
ao = np.array(ao_img.pixels[:]).reshape(TEX, TEX, 4)[..., 0]
# source texture resampled to TEX
s2 = src_img.copy(); s2.scale(TEX, TEX); base = np.array(s2.pixels[:]).reshape(TEX, TEX, 4)
mul = 1.0 - AO_STR * (1.0 - np.clip(ao, 0, 1))
outpx = base.copy(); outpx[..., :3] = base[..., :3] * mul[..., None]  # pixels are linear floats in Blender; multiply is space-correct
res = bpy.data.images.new(name + "_BaseColor", TEX, TEX, alpha=False); res.pixels = outpx.ravel().tolist()
res.filepath_raw = os.path.join(out, name + "_BaseColor.png"); res.file_format = "PNG"; res.save()
aov = bpy.data.images.new(name + "_AOview", TEX, TEX, alpha=False); av = np.ones((TEX, TEX, 4)); av[..., :3] = ao[..., None]; aov.pixels = av.ravel().tolist()
aov.filepath_raw = os.path.join(out, name + "_AO.png"); aov.file_format = "PNG"; aov.save()
me.materials.clear(); me.materials.append(tex_mat("M_" + name, res))
sc.render.engine = "BLENDER_WORKBENCH"; previews("decao")
# --- export
for p in me.polygons: p.use_smooth = True
for o in bpy.context.selected_objects: o.select_set(False)
ob.select_set(True); bpy.context.view_layer.objects.active = ob; ob.name = me.name = name
bpy.data.objects.remove(cam, do_unlink=True)
fbx = os.path.join(out, name + ".fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                         object_types={"MESH"}, path_mode="STRIP", embed_textures=False, mesh_smooth_type="FACE", use_tspace=True)
print(f"LVPREP {name} tris {tris0}->{tris1} tex={TEX} aoMean={ao.mean():.3f} -> {fbx}")

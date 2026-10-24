"""Headless Blender: smooth remesh of a generated plush + texture bake from the original (fallback path).
Use when the generated mesh is noisy (hundreds of tiny lightmap charts, blotchy bake) or when an approved
older mesh must keep its shape at a lower triangle count. Fine detail softens (hair strands, ear tips, ahoge).
Source FBX (glb_to_fbx output, texture beside it as <stem>_BaseColor.png) ->
  voxel remesh (watertight) -> corrective smooth -> keep largest shell -> QuadriFlow quads
  (collapse-decimate to the same budget if QuadriFlow refuses) -> xatlas UV0 ->
  Cycles bake of the source colour (selected-to-active) -> <out>/<name>.fbx + <name>_BaseColor.png
Blender 5 defaults to the AgX view transform, which desaturates a baked colour texture on save
(238,198,156 -> 191,171,152); the script forces Standard before baking.
Needs xatlas in Blender's Python (see retopo_prep.py).
Usage: python .omp/scripts/tool.py blender --script fumo_remesh_bake.py -- <in.fbx> <out_dir> <name> <target_faces> [voxel_mm=1.2] [smooth_iter=6] [tex=1024]
target_faces is quads: 1,400 quads ~= 2,800 tris.
"""
import bpy, bmesh, sys, os, math
import site; sys.path.append(site.getusersitepackages())
import xatlas, numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
src, out, name, target = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2], int(argv[3])
voxel = float(argv[4]) / 1000 if len(argv) > 4 else 0.0012
smooth_iter = int(argv[5]) if len(argv) > 5 else 6
TEX = int(argv[6]) if len(argv) > 6 else 1024
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
hi = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
mw = hi.matrix_world.copy(); hi.parent = None; hi.matrix_world = mw
for o in list(bpy.context.scene.objects):
    if o is not hi: bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.context.selected_objects: o.select_set(False)
bpy.context.view_layer.objects.active = hi; hi.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
hi.name = "hi"
# source material with the original texture
img = bpy.data.images.load(os.path.splitext(src)[0] + "_BaseColor.png")
m = bpy.data.materials.new("src"); m.use_nodes = True
tn = m.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img
m.node_tree.links.new(tn.outputs[0], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
hi.data.materials.clear(); hi.data.materials.append(m)
# --- low: copy, voxel remesh, smooth, quadriflow
lo = hi.copy(); lo.data = hi.data.copy(); lo.name = "lo"; bpy.context.scene.collection.objects.link(lo)
for o in bpy.context.selected_objects: o.select_set(False)
bpy.context.view_layer.objects.active = lo; lo.select_set(True)
lo.data.remesh_voxel_size = voxel; lo.data.use_remesh_preserve_volume = True
bpy.ops.object.voxel_remesh()
sm = lo.modifiers.new("smooth", "CORRECTIVE_SMOOTH"); sm.iterations = smooth_iter; sm.factor = 0.5; sm.use_only_smooth = True
bpy.ops.object.modifier_apply(modifier="smooth")
v_vox = len(lo.data.polygons)
# QuadriFlow needs one manifold shell with consistent normals: keep the largest piece, fix normals
bm = bmesh.new(); bm.from_mesh(lo.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=voxel * 0.01)
seen, shells = set(), []
for f in bm.faces:
    if f.index in seen: continue
    st, sh = [f], []; seen.add(f.index)
    while st:
        x = st.pop(); sh.append(x)
        for e in x.edges:
            for g in e.link_faces:
                if g.index not in seen: seen.add(g.index); st.append(g)
    shells.append(sh)
shells.sort(key=len, reverse=True)
for sh in shells[1:]: bmesh.ops.delete(bm, geom=sh, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
nm_pre = sum(1 for e in bm.edges if len(e.link_faces) != 2)
bm.to_mesh(lo.data); bm.free()
print(f"VOXEL faces={v_vox} shells={len(shells)} keptFaces={len(lo.data.polygons)} nonManifoldOrBoundary={nm_pre}")
n_before = len(lo.data.polygons)
bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False, use_preserve_sharp=False, use_preserve_boundary=False,
                                 preserve_attributes=False, smooth_normals=False, mode="FACES", target_faces=target, seed=0)
method = "quadriflow"
if len(lo.data.polygons) == n_before:  # QuadriFlow refused (manifold check): collapse-decimate to the same tri budget
    dm = lo.modifiers.new("dec", "DECIMATE"); dm.decimate_type = "COLLAPSE"; dm.ratio = (2 * target) / (2 * n_before)
    dm.use_symmetry = False; dm.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier="dec"); method = "decimate"
print(f"LOWPOLY method={method} faces={len(lo.data.polygons)}")
lo.data.materials.clear()
# --- UV0 by xatlas on the (triangulated) low mesh; texture and lightmap can share this layout
bm = bmesh.new(); bm.from_mesh(lo.data)
nm_edges = sum(1 for e in bm.edges if len(e.link_faces) > 2); quads = sum(1 for f in bm.faces if len(f.verts) == 4); faces = len(bm.faces)
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY"); bm.to_mesh(lo.data); bm.free()
me = lo.data
pos = np.array([v.co[:] for v in me.vertices], dtype=np.float32); tri = np.array([p.vertices[:] for p in me.polygons], dtype=np.uint32)
atlas = xatlas.Atlas(); atlas.add_mesh(pos, tri)
co = xatlas.ChartOptions(); co.max_iterations = 4
po = xatlas.PackOptions(); po.resolution = TEX; po.padding = 4; po.bilinear = True; po.bruteForce = True; po.rotate_charts = True
atlas.generate(co, po); vmap, idx, uvs = atlas[0]
while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
uv = me.uv_layers.new(name="UVMap")
for fi, p in enumerate(me.polygons):
    for k, li in enumerate(p.loop_indices): uv.data[li].uv = uvs[idx[fi][k]]
charts = atlas.chart_count
# --- bake source colour onto the low mesh
bimg = bpy.data.images.new(name + "_BaseColor", TEX, TEX, alpha=False)
lm = bpy.data.materials.new("M_" + name); lm.use_nodes = True
bn = lm.node_tree.nodes.new("ShaderNodeTexImage"); bn.image = bimg; lm.node_tree.nodes.active = bn
me.materials.append(lm)
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.device = "CPU"
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
sc.render.bake.use_selected_to_active = True; sc.render.bake.cage_extrusion = 0.004; sc.render.bake.max_ray_distance = 0.008
sc.render.bake.margin = 8; sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False; sc.render.bake.use_pass_color = True
for o in bpy.context.selected_objects: o.select_set(False)
hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
bimg.filepath_raw = os.path.join(out, name + "_BaseColor.png"); bimg.file_format = "PNG"; bimg.save()
# --- export low only
bpy.data.objects.remove(hi, do_unlink=True)
lo.name = lo.data.name = name
for p in me.polygons: p.use_smooth = True
for o in bpy.context.selected_objects: o.select_set(False)
lo.select_set(True); bpy.context.view_layer.objects.active = lo
fbx = os.path.join(out, name + ".fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                         object_types={"MESH"}, path_mode="STRIP", embed_textures=False, mesh_smooth_type="FACE", use_tspace=True)
print(f"REMESH {name} voxelFaces={v_vox} quadFaces={faces} quads={quads} nonManifold={nm_edges} tris={len(me.polygons)} uvCharts={charts} -> {fbx}")

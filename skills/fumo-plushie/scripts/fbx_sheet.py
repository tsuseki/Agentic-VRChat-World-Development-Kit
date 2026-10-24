"""Headless Blender: FBX + texture -> 4-view renders: flat textured, and clay + wire + red UV0 seams.
Texture: <stem>.fbm/ (an image-to-3D service's FBX export) or <stem>_BaseColor.png beside the FBX.
Also writes <name>_uv.json (UV0 polygons) for a UV sheet.
Usage: python .omp/scripts/tool.py blender --script fbx_sheet.py -- <in.fbx> <out_dir> <name>
Writes <out>/<name>_{tex,seams}_{front,34,side,back}.png"""
import bpy, bmesh, sys, os, math, json
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
src, out, name = os.path.abspath(argv[0]), os.path.abspath(argv[1]), argv[2]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in obs:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
for o in list(bpy.context.scene.objects):
    if o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action="SELECT"); bpy.context.view_layer.objects.active = obs[0]
if len(obs) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
vs = [v.co for v in me.vertices]
mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
h = mx.z - mn.z
# texture: the .fbm image, else <stem>_BaseColor.png
fbm = os.path.splitext(src)[0] + ".fbm"
img = None
for f in os.listdir(fbm) if os.path.isdir(fbm) else []:
    if f.lower().endswith((".jpg", ".png")) and "normal" not in f.lower(): img = bpy.data.images.load(os.path.join(fbm, f))
sib = os.path.splitext(src)[0] + "_BaseColor.png"
if img is None and os.path.isfile(sib): img = bpy.data.images.load(sib)
mat = bpy.data.materials.new("tex"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
if img:
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img; nt.links.new(tn.outputs[0], bsdf.inputs["Base Color"])
me.materials.clear(); me.materials.append(mat)
# UV dump (before welding: loop UVs are what the texture uses)
uv = me.uv_layers[0]
json.dump({"polys": [[list(uv.data[li].uv) for li in p.loop_indices] for p in me.polygons],
           "quads": sum(1 for p in me.polygons if len(p.vertices) == 4), "faces": len(me.polygons)},
          open(os.path.join(out, f"{name}_uv.json"), "w"))
# seams = UV island borders on the welded surface
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=h * 1e-5); bm.to_mesh(me); bm.free()
me.uv_layers.active = me.uv_layers[0]
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)
bpy.ops.object.mode_set(mode="OBJECT")
seams = [e for e in me.edges if e.use_seam]
for p in me.polygons: p.use_smooth = True
def tube(edges, nm, r, col):
    m = bpy.data.meshes.new(nm); vmap, verts, ed = {}, [], []
    for e in edges:
        ids = []
        for vi in e.vertices:
            if vi not in vmap: vmap[vi] = len(verts); verts.append(me.vertices[vi].co.copy())
            ids.append(vmap[vi])
        ed.append(ids)
    m.from_pydata(verts, ed, []); o = bpy.data.objects.new(nm, m); bpy.context.scene.collection.objects.link(o)
    for x in bpy.context.selected_objects: x.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.convert(target="CURVE"); o.data.bevel_depth = r; o.data.bevel_resolution = 1; o.color = col
    return o
wire = tube([e for e in me.edges if not e.use_seam], "wire", h * 0.0008, (0.12, 0.12, 0.14, 1))
seam = tube(seams, "seams", h * 0.0025, (0.92, 0.07, 0.07, 1))
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.show_cavity = False
sc.render.resolution_x = sc.render.resolution_y = 900; sc.view_settings.view_transform = "Standard"
sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.55, 0.55, 0.57)
cd = bpy.data.cameras.new("cam"); cd.lens = 70
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + h / 2)); dist = h * 2.7
# FBX exports from glb_to_fbx / retopo_prep face -Y after import
views = [("front", 0), ("34", 35), ("side", 90), ("back", 180)]
for mode in ("tex", "seams"):
    show = mode == "seams"
    wire.hide_render = seam.hide_render = not show
    sc.display.shading.color_type = "OBJECT" if show else "TEXTURE"
    sc.display.shading.light = "STUDIO" if show else "FLAT"
    ob.color = (0.75, 0.75, 0.77, 1)
    for nm, ang in views:
        a = math.radians(ang)
        cam.location = c + Vector((math.sin(a) * dist, -math.cos(a) * dist, 0.12 * h))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, f"{name}_{mode}_{nm}.png")
        bpy.ops.render.render(write_still=True)
print(f"SHEET {name} faces={len(me.polygons)} seamEdges={len(seams)} tex={'yes' if img else 'no'}")

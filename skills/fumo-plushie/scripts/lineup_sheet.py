"""Headless Blender: line up the new plush beside the world's existing plushies and a 1.4 m person.
Every FBX is placed as exported (no rescale), bottom on the floor, facing the camera (-Y), so size,
proportions, style and colour can be judged side by side before anything goes into Unity.
Texture per FBX: <stem>_BaseColor.png beside it, else <stem>.fbm/.
Usage: python .omp/scripts/tool.py blender --script lineup_sheet.py -- <out_dir> <new.fbx> [<existing.fbx> ...] [--person 1.4]
Writes <out>/lineup_scale.png (row + person), lineup_front.png and lineup_34.png (plushies only, close),
and prints HEIGHT <name> <m> per plush plus SPREAD <max/min height>.
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
person = 1.4
if "--person" in argv:
    i = argv.index("--person"); person = float(argv[i + 1]); del argv[i:i + 2]
out, files = os.path.abspath(argv[0]), [os.path.abspath(p) for p in argv[1:]]
assert files, "give at least the new plush FBX"
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
vs = sc.view_settings; vs.view_transform = "Standard"; vs.look = "None"


def texture_for(path):
    stem = os.path.splitext(path)[0]
    if os.path.isfile(stem + "_BaseColor.png"): return bpy.data.images.load(stem + "_BaseColor.png")
    fbm = stem + ".fbm"
    for f in os.listdir(fbm) if os.path.isdir(fbm) else []:
        if f.lower().endswith((".png", ".jpg", ".jpeg")) and "normal" not in f.lower():
            return bpy.data.images.load(os.path.join(fbm, f))
    return None


plush, x, gap = [], 0.0, 0.06
for path in files:
    before = set(sc.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in sc.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [v.co for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    w = mx.x - mn.x
    ob.location = Vector((x - mn.x, -(mn.y + mx.y) / 2, -mn.z))
    x += w + gap
    img = texture_for(path)
    m = bpy.data.materials.new("M_" + ob.name); m.use_nodes = True
    if img:
        t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = img
        m.node_tree.links.new(t.outputs[0], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.clear(); ob.data.materials.append(m)
    for p in ob.data.polygons: p.use_smooth = True
    name = os.path.splitext(os.path.basename(path))[0]
    plush.append((name, mx.z - mn.z))
    print(f"HEIGHT {name} {mx.z - mn.z:.3f} tris={sum(len(p.vertices) - 2 for p in ob.data.polygons)} tex={'yes' if img else 'NO'}")
row_w = x - gap
hs = [h for _, h in plush]
print(f"SPREAD {max(hs) / min(hs):.2f} (heights {min(hs):.3f}-{max(hs):.3f} m)")

# 1.4 m person: body cylinder + head sphere, grey, left of the row
body_h, head_r = person * 0.84, person * 0.08
bpy.ops.mesh.primitive_cylinder_add(radius=person * 0.11, depth=body_h, location=(-0.35, 0, body_h / 2))
bpy.ops.mesh.primitive_uv_sphere_add(radius=head_r, location=(-0.35, 0, person - head_r))
for o in bpy.context.selected_objects: o.select_set(False)
figure = [o for o in sc.objects if o.type == "MESH" and o.name.startswith(("Cylinder", "Sphere"))]
grey = bpy.data.materials.new("figure"); grey.diffuse_color = (0.6, 0.6, 0.62, 1)
for o in figure: o.data.materials.append(grey)
bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0))

sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
sc.display.shading.show_shadows = True
sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.5, 0.5, 0.52)
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam


def shot(fname, cx, cz, width, height, yaw=0.0, rx=1600, ry=900):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    cd.ortho_scale = max(width, height * rx / ry) * 1.12
    a = math.radians(yaw); d = 6.0
    cam.location = Vector((cx + math.sin(a) * d, -math.cos(a) * d, cz))
    cam.rotation_euler = (Vector((cx, 0, cz)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, fname); bpy.ops.render.render(write_still=True)


shot("lineup_scale.png", (row_w - 0.35 - 0.2) / 2, person / 2, row_w + 0.6, person + 0.05)
for o in figure: o.hide_render = True
hmax = max(hs)
shot("lineup_front.png", row_w / 2, hmax / 2, row_w, hmax, 0, 1600, 700)
shot("lineup_34.png", row_w / 2, hmax / 2, row_w, hmax, 35, 1600, 700)
print(f"LINEUP {len(plush)} plush, row {row_w:.2f} m -> {out}")

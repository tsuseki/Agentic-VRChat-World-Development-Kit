"""Headless Blender (Cycles): lit 3/4 renders of FBX+texture pairs, transparent background with a shadow-catcher floor.
Usage: blender -b --factory-startup --python lineup_shaded.py -- <out_dir> <name>=<fbx>=<tex> ...   env: SH_YAW (deg, 22), SH_PITCH (deg down, 10), SH_PX (600), SH_SAMPLES (64)"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; out = os.path.abspath(a[0]); os.makedirs(out, exist_ok=True)
YAW = float(os.environ.get("SH_YAW", "22")); PITCH = float(os.environ.get("SH_PITCH", "10")); PX = int(os.environ.get("SH_PX", "600")); SMP = int(os.environ.get("SH_SAMPLES", "64"))
def area(name, loc, target, size, energy, color=(1, 1, 1), shadow=True):
    d = bpy.data.lights.new(name, "AREA"); d.use_shadow = shadow; d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
for spec in a[1:]:
    name, fbx, tex = spec.split("=")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    sc = bpy.context.scene
    ob = [o for o in sc.objects if o.type == "MESH"][0]
    mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
    for o in list(sc.objects):
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for p in ob.data.polygons: p.use_smooth = True
    img = bpy.data.images.load(os.path.abspath(tex)); img.colorspace_settings.name = "sRGB"
    m = bpy.data.materials.new("m"); m.use_nodes = True; bs = m.node_tree.nodes["Principled BSDF"]
    tn = m.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img; m.node_tree.links.new(tn.outputs[0], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.8
    for k in ("Specular IOR Level", "Specular"):
        if k in bs.inputs: bs.inputs[k].default_value = 0.25
    ob.data.materials.clear(); ob.data.materials.append(m)
    # shadow-catcher floor
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); fl = bpy.context.active_object; fl.is_shadow_catcher = True
    # world: dim neutral ambient
    sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.55, 0.56, 0.6, 1); bg.inputs[1].default_value = 0.25
    # lights (doll faces -Y; camera sits at +X side of front, so key comes from camera-left = -X, front, above)
    area("key", (-0.7, -0.8, 1.1), (0, 0, 0.12), 0.9, 30, (1.0, 0.97, 0.93))
    area("fill", (0.9, -0.7, 0.4), (0, 0, 0.12), 1.2, 7, (0.9, 0.95, 1.0))
    area("rim", (0.35, 0.9, 0.7), (0, 0, 0.14), 0.5, 16, (1, 1, 1), False)
    cd = bpy.data.cameras.new("c"); cd.lens = 85; cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    c = Vector((0, 0, 0.115)); r = math.radians(YAW); p = math.radians(PITCH); d = 0.95
    cam.location = c + Vector((math.sin(r) * math.cos(p) * d, -math.cos(r) * math.cos(p) * d, math.sin(p) * d))
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SMP; sc.cycles.use_denoising = True
    sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = PX
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = f"{out}/{name}.png"; bpy.ops.render.render(write_still=True)
print("SHADED_OK")

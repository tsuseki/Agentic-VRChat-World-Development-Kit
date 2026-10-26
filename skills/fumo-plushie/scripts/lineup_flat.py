"""Headless Blender: ortho renders of FBX+texture pairs at identical scale, with a grey floor line. Blender import: Z up, front = -Y.
Usage: blender -b --factory-startup --python lineup_flat.py -- <out_dir> <name>=<fbx>=<tex> ... ; writes <out_dir>/<name>_{front,side,q34}.png and prints bbox/tris.
Env: SHOT_OS (ortho scale, default 0.36), SHOT_ZC (view-centre height m, default 0.12), SHOT_PX (default 700)"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; out = os.path.abspath(a[0]); os.makedirs(out, exist_ok=True)
OS = float(os.environ.get("SHOT_OS", "0.36")); ZC = float(os.environ.get("SHOT_ZC", "0.12")); PX = int(os.environ.get("SHOT_PX", "700"))
for spec in a[1:]:
    name, fbx, tex = spec.split("=")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
    for o in list(bpy.context.scene.objects):
        if o is not ob and o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    img = bpy.data.images.load(os.path.abspath(tex))
    m = bpy.data.materials.new("m"); m.use_nodes = True
    tn = m.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img
    m.node_tree.links.new(tn.outputs[0], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.clear(); ob.data.materials.append(m)
    vs = [v.co for v in ob.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    ob.data.calc_loop_triangles()
    print("BBOX", name, [round(x, 4) for x in mn], [round(x, 4) for x in mx], "tris", len(ob.data.loop_triangles), "mats", len(ob.data.materials))
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = PX
    sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"
    sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.93, 0.93, 0.95)
    cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = OS
    cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    c = Vector((0, 0, ZC))
    for nm, ang in (("front", 0), ("side", 90), ("q34", 35), ("back", 180), ("side2", -90)):
        r = math.radians(ang); d = 2.0
        cam.location = c + Vector((math.sin(r) * d, -math.cos(r) * d, 0))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"{out}/{name}_{nm}.png"; bpy.ops.render.render(write_still=True)
print("SHOT_OK")

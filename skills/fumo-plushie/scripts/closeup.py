"""Headless Blender: front + 3/4 face close-ups for several fbx+texture pairs in ONE run (one Blender slot).
Usage: blender -b --factory-startup --python closeup.py -- <out_dir> <HZ> <DF> <name>=<fbx>=<tex> ..."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; out = os.path.abspath(a[0]); os.makedirs(out, exist_ok=True); HZ = float(a[1]); DF = float(a[2])
for spec in a[3:]:
    name, fbx, tex = spec.split("=")
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    sc = bpy.context.scene; ob = [o for o in sc.objects if o.type == "MESH"][0]
    mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
    img = bpy.data.images.load(os.path.abspath(tex)); m = bpy.data.materials.new("m"); m.use_nodes = True
    tn = m.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img; m.node_tree.links.new(tn.outputs[0], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    ob.data.materials.clear(); ob.data.materials.append(m)
    sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = sc.render.resolution_y = 900
    sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"; sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.9, 0.9, 0.92)
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    h = mx.z - mn.z; c = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + h * HZ))
    cd = bpy.data.cameras.new("c"); cd.lens = 70; cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    for nm, ang in (("front", 0), ("q34", 35)):
        r = math.radians(ang); d = h * 1.9 * DF
        cam.location = c + Vector((math.sin(r) * d, -math.cos(r) * d, 0)); cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"{out}/{name}_{nm}.png"; bpy.ops.render.render(write_still=True)
print("CLOSE_OK")

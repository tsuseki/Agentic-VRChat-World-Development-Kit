"""Headless Blender (Cycles): render plush texture variants under Light-Volume-style lighting (soft sky/ground ambient from a gradient world, NO key light) so that
"BaseColor without AO" and "BaseColor with AO baked in" can be compared the way VRC Light Volumes will show them: flat, directional-ish ambient with no contact shading.
Usage: blender -b --factory-startup --python lv_ab_render.py -- <out_dir> <name>=<fbx>=<texA>=<texB> ...
Writes <out_dir>/<name>_{A,B}_{front,q34,face}.png (RGBA, transparent background).  Env: LV_PX (700), LV_SAMPLES (64), LV_FACE_Z (head-centre height in m, 0.17), LV_FACE_D (face camera distance, 0.34)
Material mimics the Light Volume PBR plush material: metallic 0, roughness 0.9."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; out = os.path.abspath(a[0]); os.makedirs(out, exist_ok=True)
PX = int(os.environ.get("LV_PX", "700")); SMP = int(os.environ.get("LV_SAMPLES", "64"))
FZ = float(os.environ.get("LV_FACE_Z", "0.17")); FD = float(os.environ.get("LV_FACE_D", "0.34"))
def shots(sc, cam, name, tag):
    for nm, (yaw, pitch, dist, cz, lens) in {"front": (0, 6, 0.95, 0.115, 85), "q34": (35, 8, 0.95, 0.115, 85), "face": (0, 3, FD, FZ, 85)}.items():
        cam.data.lens = lens
        c = Vector((0, 0, cz)); r, p = math.radians(yaw), math.radians(pitch)
        cam.location = c + Vector((math.sin(r) * math.cos(p) * dist, -math.cos(r) * math.cos(p) * dist, math.sin(p) * dist))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"{out}/{name}_{tag}_{nm}.png"; bpy.ops.render.render(write_still=True)
for spec in a[1:]:
    name, fbx, ta, tb = spec.split("=")
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    ob = [o for o in sc.objects if o.type == "MESH"][0]
    mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
    for o in list(sc.objects):
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for pg in ob.data.polygons: pg.use_smooth = True
    m = bpy.data.materials.new("m"); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tn = nt.nodes.new("ShaderNodeTexImage"); nt.links.new(tn.outputs[0], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.9; bs.inputs["Metallic"].default_value = 0
    for k in ("Specular IOR Level", "Specular"):
        if k in bs.inputs: bs.inputs[k].default_value = 0.1
    ob.data.materials.clear(); ob.data.materials.append(m)
    # world: sky-to-ground gradient (what an SH probe sees), no sun
    sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True; wt = sc.world.node_tree
    for nd in list(wt.nodes): wt.nodes.remove(nd)
    tc = wt.nodes.new("ShaderNodeTexCoord"); sp = wt.nodes.new("ShaderNodeSeparateXYZ"); cr = wt.nodes.new("ShaderNodeValToRGB")
    bg = wt.nodes.new("ShaderNodeBackground"); wo = wt.nodes.new("ShaderNodeOutputWorld")
    wt.links.new(tc.outputs["Generated"], sp.inputs[0]); wt.links.new(sp.outputs["Z"], cr.inputs[0]); wt.links.new(cr.outputs[0], bg.inputs[0]); wt.links.new(bg.outputs[0], wo.inputs[0])
    # Generated coords of a world run 0..1 over the direction cube: Z 0.5 = horizon
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.30, 0.27, 0.25, 1)
    cr.color_ramp.elements[1].position = 0.70; cr.color_ramp.elements[1].color = (1.0, 1.0, 1.05, 1)
    bg.inputs[1].default_value = 1.15
    cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SMP; sc.cycles.use_denoising = True
    sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = PX
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    for tag, tex in (("A", ta), ("B", tb)):
        img = bpy.data.images.load(os.path.abspath(tex), check_existing=False); img.colorspace_settings.name = "sRGB"; tn.image = img
        shots(sc, cam, name, tag)
print("LVAB_OK")

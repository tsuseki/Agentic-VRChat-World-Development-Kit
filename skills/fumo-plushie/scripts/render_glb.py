"""Headless Blender: import an image-to-3D GLB, report size/tris, render 5 lit views (front, 3/4, left, back, right).
Usage: python .omp/scripts/tool.py blender --script render_glb.py -- <in.glb> <out_dir>
Writes <out>/render_<view>.png. Look at every view: hidden sides are where generation invents things.
"""
import bpy, sys, math, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
size = mx - mn
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
print(f"REPORT meshes={len(meshes)} tris={tris} size={tuple(round(v,4) for v in size)} min={tuple(round(v,4) for v in mn)} mats={[s.material.name for o in meshes for s in o.material_slots if s.material]}")

center = (mn + mx) / 2
h = size.z
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 900
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.52, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.5

def light(name, loc, energy, size_):
    d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size_
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o)
    o.location = center + Vector(loc) * h
    o.rotation_euler = (center - o.location).to_track_quat("-Z", "Y").to_euler()
light("key", (-1.5, -2.5, 2.0), 90 * h * h, 2 * h)
light("fill", (2.0, -1.5, 0.8), 35 * h * h, 2 * h)
light("rim", (0.5, 2.5, 2.0), 60 * h * h, 2 * h)

cd = bpy.data.cameras.new("cam"); cd.lens = 70
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
dist = h * 2.7
# glTF import: the model front is -Y in Blender; confirm on the renders
for name, ang in [("front", 0), ("34", 35), ("left", 90), ("back", 180), ("right", -90)]:
    a = math.radians(ang)
    cam.location = center + Vector((math.sin(a) * dist, -math.cos(a) * dist, 0.15 * h))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, f"render_{name}.png")
    bpy.ops.render.render(write_still=True)
print("DONE")

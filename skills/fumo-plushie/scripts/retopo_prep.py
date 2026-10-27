"""Headless Blender: generated plush FBX -> Unity FBX with clean lightmap UV2 + UV/seam sheets.

- Scales to seated height (m), origin bottom centre, front -Y, transforms applied.
- UV0 = the generator's texture UVs (kept). UV1 'UVMap_Lightmap' = xatlas charts packed for a small
  chart in the lightmap atlas (import with Generate Lightmap UVs OFF so Unity keeps it).
- Texture: <stem>.fbm/ (service FBX export) or <stem>_BaseColor.png beside the FBX (glb_to_fbx output).
- Writes: <out>/<name>.fbx, <name>_BaseColor.png (+ _Normal.png if present), <name>_edges.json,
  <sheets>/<name>_uv0_tex.png (UV0 wire over texture), <name>_uv1.png (lightmap layout),
  <name>_seams_{front,34,back,side}.png, and prints REPORT with tris, chart count, UV fill.
Needs xatlas in Blender's Python: `<blender>/<ver>/python/bin/python -m pip install --user xatlas`.
Usage: python .omp/scripts/tool.py blender --script retopo_prep.py -- <in.fbx> <out_dir> <sheet_dir> <name> <height_m> [lm_res=256]
Env (optional): XA_MAX_COST (2), XA_NORMAL_W (2), XA_ROUND_W (0.01), XA_STRAIGHT_W (6).
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out, sheets, name, height = (os.path.abspath(argv[0]), os.path.abspath(argv[1]),
                                  os.path.abspath(argv[2]), argv[3], float(argv[4]))
LM_RES = int(argv[5]) if len(argv) > 5 else 256  # xatlas pack resolution (texels across the chart atlas)
os.makedirs(out, exist_ok=True); os.makedirs(sheets, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
# Blender 5 defaults to AgX, and save_render applies it: textures came out desaturated
# (238,198,156 -> 191,171,152). Standard writes the pixels unchanged.
_vs = bpy.context.scene.view_settings; _vs.view_transform = "Standard"; _vs.look = "None"; _vs.exposure = 0; _vs.gamma = 1
bpy.ops.import_scene.fbx(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert len(meshes) == 1, f"meshes={len(meshes)}"
ob = meshes[0]
mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
for o in list(bpy.context.scene.objects):
    if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

vs = [v.co for v in ob.data.vertices]
mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
k = height / (mx.z - mn.z); off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
for v in ob.data.vertices: v.co = (v.co - off) * k
ob.name = name
ob.data.name = os.environ.get("MESH_NAME") or name  # keep an existing Unity asset's mesh name so scene references survive a swap

# --- textures out (service FBX references images in <fbx>.fbm/; load them directly)
if ob.material_slots and ob.material_slots[0].material: ob.material_slots[0].material.name = "M_" + name
fbm = os.path.splitext(src)[0] + ".fbm"
imgs = {}
if os.path.isdir(fbm):
    for f in os.listdir(fbm):
        low = f.lower()
        key = "Normal" if "normal" in low else ("BaseColor" if low.endswith((".jpg", ".jpeg", ".png")) else None)
        if key: imgs[key] = bpy.data.images.load(os.path.join(fbm, f))
else:  # glb_to_fbx output: texture sits beside the FBX as <stem>_BaseColor.png
    sib = os.path.splitext(src)[0] + "_BaseColor.png"
    if os.path.isfile(sib): imgs["BaseColor"] = bpy.data.images.load(sib)
for key, img in imgs.items():
    img.save_render(os.path.join(out, f"{name}_{key}.png"))
# --- lightmap UV (xatlas: organic low-distortion charts, tight lightmap packing)
import site; sys.path.append(site.getusersitepackages())
import bmesh, xatlas, numpy as np
me = ob.data
me.uv_layers[0].name = "UVMap"
while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[1])
QUADS_IN = sum(1 for p in me.polygons if len(p.vertices) == 4)
QUAD_EDGES = [tuple(e.vertices) for e in me.edges]  # source topology (quads), before triangulation
bm = bmesh.new(); bm.from_mesh(me)
V_BEFORE = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=height * 1e-5)  # FBX splits verts on UV0 seams; weld so charts follow the surface
V_AFTER = len(bm.verts)
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
bm.to_mesh(me); bm.free()
pos = np.array([v.co[:] for v in me.vertices], dtype=np.float32)
tri = np.array([p.vertices[:] for p in me.polygons], dtype=np.uint32)
atlas = xatlas.Atlas()
atlas.add_mesh(pos, tri)
co = xatlas.ChartOptions(); co.max_iterations = 4
co.max_cost = float(os.environ.get("XA_MAX_COST", "2"))            # higher = bigger charts, more stretch
co.normal_deviation_weight = float(os.environ.get("XA_NORMAL_W", "2"))
co.roundness_weight = float(os.environ.get("XA_ROUND_W", "0.01"))
co.straightness_weight = float(os.environ.get("XA_STRAIGHT_W", "6"))
po = xatlas.PackOptions(); po.resolution = LM_RES; po.padding = 2; po.bilinear = True; po.bruteForce = True; po.rotate_charts = True
atlas.generate(co, po)
vmap, idx, uvs = atlas[0]
assert idx.shape[0] == tri.shape[0], "xatlas changed triangle count"
lm = me.uv_layers.new(name="UVMap_Lightmap")
for fi, p in enumerate(me.polygons):
    # xatlas keeps triangle order and corner order
    for k, li in enumerate(p.loop_indices):
        assert vmap[idx[fi][k]] == p.vertices[k]
        lm.data[li].uv = uvs[idx[fi][k]]
me.uv_layers.active = lm
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)  # seams = lightmap chart borders
bpy.ops.object.mode_set(mode="OBJECT")
import json  # edges for overlay renders elsewhere (e.g. a Unity line mesh): positions in this mesh's final space
json.dump({"verts": [list(v.co) for v in me.vertices], "wire": QUAD_EDGES,
           "seams": [tuple(e.vertices) for e in me.edges if e.use_seam]},
          open(os.path.join(out, f"{name}_edges.json"), "w"))
me.uv_layers["UVMap"].active_render = True
uv0, lm = me.uv_layers["UVMap"], me.uv_layers["UVMap_Lightmap"]
seam_edges = [e for e in me.edges if e.use_seam]
CHARTS = atlas.chart_count if hasattr(atlas, "chart_count") else -1

def uv_area(layer):
    a = 0.0
    for p in me.polygons:
        pts = [layer.data[li].uv for li in p.loop_indices]
        for i in range(1, len(pts) - 1):
            a += abs((pts[i].x - pts[0].x) * (pts[i + 1].y - pts[0].y) - (pts[i + 1].x - pts[0].x) * (pts[i].y - pts[0].y)) / 2
    return a

# --- UV sheets via a Blender image + manual line draw (no PIL in Blender)
def draw_sheet(layer, base_img, path, size=1024, line=(0.05, 0.05, 0.06, 1), fill_bg=(0.85, 0.85, 0.87, 1)):
    px = [0.0] * (size * size * 4)
    if base_img is not None:
        bi = base_img.copy(); bi.scale(size, size); px = list(bi.pixels)
    else:
        for i in range(size * size): px[i*4:i*4+4] = fill_bg
    def plot(x, y):
        if 0 <= x < size and 0 <= y < size:
            j = (y * size + x) * 4; px[j:j+4] = line
    for p in me.polygons:
        pts = [layer.data[li].uv for li in p.loop_indices]
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            x0, y0, x1, y1 = a.x * (size - 1), a.y * (size - 1), b.x * (size - 1), b.y * (size - 1)
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for t in range(n + 1):
                plot(int(round(x0 + (x1 - x0) * t / n)), int(round(y0 + (y1 - y0) * t / n)))
    img = bpy.data.images.new("sheet", size, size, alpha=True); img.pixels = px
    img.filepath_raw = path; img.file_format = "PNG"; img.save()

draw_sheet(uv0, imgs.get("BaseColor"), os.path.join(sheets, f"{name}_uv0_tex.png"))
draw_sheet(lm, None, os.path.join(sheets, f"{name}_uv1.png"))

# --- 3D seam renders: clay mesh + red tubes along the lightmap seams
def render_seams():
    sm = bpy.data.meshes.new("seams")
    vmap, verts, edges = {}, [], []
    for e in seam_edges:
        ids = []
        for vi in e.vertices:
            if vi not in vmap: vmap[vi] = len(verts); verts.append(me.vertices[vi].co.copy())
            ids.append(vmap[vi])
        edges.append(ids)
    sm.from_pydata(verts, edges, [])
    so = bpy.data.objects.new("seams", sm); bpy.context.scene.collection.objects.link(so)
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = so; so.select_set(True)
    bpy.ops.object.convert(target="CURVE")
    so.data.bevel_depth = height * 0.0035; so.data.bevel_resolution = 2
    so.color = (0.9, 0.08, 0.08, 1); ob.color = (0.72, 0.72, 0.74, 1)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "OBJECT"; sc.display.shading.show_cavity = True
    sc.render.resolution_x = sc.render.resolution_y = 1000; sc.view_settings.view_transform = "Standard"
    sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.55, 0.55, 0.57)
    cd = bpy.data.cameras.new("cam"); cd.lens = 70
    cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    c = Vector((0, 0, height / 2)); dist = height * 2.7
    for nm, ang in [("front", 0), ("34", 35), ("back", 180), ("side", 90)]:
        a = math.radians(ang)
        cam.location = c + Vector((math.sin(a) * dist, -math.cos(a) * dist, 0.15 * height))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(sheets, f"{name}_seams_{nm}.png")
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(so, do_unlink=True); bpy.data.objects.remove(cam, do_unlink=True)
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
render_seams()

bpy.ops.object.shade_smooth()
fbx = os.path.join(out, f"{name}.fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_scale_options="FBX_SCALE_ALL",
                         axis_forward="-Z", axis_up="Y", object_types={"MESH"}, path_mode="STRIP",
                         embed_textures=False, mesh_smooth_type="FACE", use_tspace=True)
tris = sum(len(p.vertices) - 2 for p in me.polygons)
print(f"REPORT {name} quadsIn={QUADS_IN} verts {V_BEFORE}->{V_AFTER} tris={tris} lmCharts={CHARTS} seams={len(seam_edges)} "
      f"uv0Fill={uv_area(uv0):.2f} uv1Fill={uv_area(lm):.2f} tex={list(imgs)} -> {fbx}")

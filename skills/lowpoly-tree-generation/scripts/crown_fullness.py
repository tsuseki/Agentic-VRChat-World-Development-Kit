# Crown fullness (sky fraction inside the crown silhouette at eye level), one definition for every family.
#   python .omp/scripts/tool.py blender --blend <Species>_Tree.blend --script .omp/skills/lowpoly-tree-generation/scripts/crown_fullness.py -- <Species> [--out <dir>] [--px 768] [--atlas <png>]
#   (also works on <Species>_Booth.blend: its material has no image, so the atlas is read from --atlas or from
#   <blend dir>/../tex/<Tex>_Atlas_RGBA.png). Prints per view and
#   FULLNESS <Species> sky_mean <m> sky_max <x> crown_w <m> dist <m>
# Mesh: <Species>_Tree_LOD1 (the culled LOD1 = the shipped mesh) in a _Tree.blend, else <Species>_Tree (pack blend).
# Leaves cut out at alpha 0.45 (the shader cutoff); bark opaque (material slot 0 when there are 2+ slots; with one atlas
# slot, faces with u >= 0.75 are bark, the column layout). Perspective camera at 1.6 m eye height, 2 x crown width from
# the crown centre (leaf-vertex bbox centre), aimed at it, azimuths 0/90/180/270, lens fitted to the whole tree.
# Crown silhouette = coverage (leaves + bark) closed by 0.6 m (world size at the crown centre's distance), holes
# filled, limited to rows above the lowest leaf vertex (projected on the crown axis). sky = 1 - covered / silhouette.
# Stage 2 (numpy + scipy, run automatically with the system python because Blender has no scipy):
#   python crown_fullness.py <masks.npz>   -> report, and <out>/<Species>_fullness.png (white cover, blue sky in crown)
import sys, os, json, subprocess

CUTOFF, EYE, CLOSE_M, VIEWS = 0.45, 1.6, 0.6, (0, 90, 180, 270)


def render():
    import bpy, math
    import numpy as np
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
    argv = sys.argv[sys.argv.index("--") + 1:]
    def _opt(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
    name = argv[0]; px = int(_opt("--px", "768"))
    out = os.path.abspath(_opt("--out", os.path.dirname(bpy.data.filepath))) + os.sep; os.makedirs(out, exist_ok=True)
    ob = bpy.data.objects.get(f"{name}_Tree_LOD1") or bpy.data.objects[f"{name}_Tree"]
    sc = bpy.context.scene
    for o in sc.objects: o.hide_render = o is not ob
    me = ob.data; mw = ob.matrix_world; uv = me.uv_layers["UVMap"].data
    two = len(ob.material_slots) >= 2
    def is_leaf(p):
        return p.material_index >= 1 if two else min(uv[l].uv[0] for l in p.loop_indices) < 0.75
    lv = [mw @ me.vertices[v].co for p in me.polygons if is_leaf(p) for v in p.vertices]
    av = [mw @ v.co for v in me.vertices]
    lmn = Vector([min(v[i] for v in lv) for i in range(3)]); lmx = Vector([max(v[i] for v in lv) for i in range(3)])
    amn = Vector([min(v[i] for v in av) for i in range(3)]); amx = Vector([max(v[i] for v in av) for i in range(3)])
    c = (lmn + lmx) / 2; width = max(lmx.x - lmn.x, lmx.y - lmn.y); dist = 2.0 * width; zlow = lmn.z

    def mat(mname, img, opaque):
        m = bpy.data.materials.new(mname); m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        o = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
        if opaque or img is None:
            nt.links.new(em.outputs[0], o.inputs[0]); return m
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = 'Closest'
        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = CUTOFF
        nt.links.new(tx.outputs[1], gt.inputs[0]); nt.links.new(gt.outputs[0], mx.inputs[0])
        nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o.inputs[0])
        return m
    cd = bpy.data.cameras.new("__cf_cam"); cd.clip_start = 0.05; cd.clip_end = 500; cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("__cf_cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.use_denoising = False; sc.render.filter_size = 0.01
    sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = px; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    def slot_img(s):
        m = ob.material_slots[s].material
        img = next((n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'), None) if m and m.node_tree else None
        if img is None and not (two and s == 0):  # pack blend: material <Tex>_Tree has no image; use the column atlas
            tex = m.name[:-5] if m and m.name.endswith("_Tree") else name
            p = _opt("--atlas") or os.path.join(os.path.dirname(os.path.dirname(bpy.data.filepath)), "tex", f"{tex}_Atlas_RGBA.png")
            if not os.path.exists(p): raise SystemExit(f"crown_fullness: no leaf texture on slot {s}; pass --atlas <Tex>_Atlas_RGBA.png")
            img = bpy.data.images.load(p)
        return img
    for s in range(len(ob.material_slots)):
        ob.material_slots[s].material = mat(f"__cf_{s}", slot_img(s), two and s == 0)

    corners = [Vector((x, y, z)) for x in (amn.x, amx.x) for y in (amn.y, amx.y) for z in (amn.z, amx.z)]
    res = {}; meta = []
    for az in VIEWS:
        a = math.radians(az)
        cam.location = Vector((c.x + math.sin(a) * dist, c.y - math.cos(a) * dist, EYE))
        fwd = (c - cam.location).normalized(); cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        R = cam.matrix_world.to_3x3().inverted()
        ang = max(max(abs(math.atan2(q.x, -q.z)), abs(math.atan2(q.y, -q.z))) for q in (R @ (k - cam.location) for k in corners))
        cd.angle = min(2.6, 2 * ang * 1.06); bpy.context.view_layer.update()
        p = out + f"__cf_{os.getpid()}.png"; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(p); al = np.array(im.pixels[:]).reshape(px, px, 4)[::-1, :, 3] > 0.5
        bpy.data.images.remove(im); os.remove(p)
        d_c = (c - cam.location).length; mpp = 2 * d_c * math.tan(cd.angle / 2) / px
        row = (1.0 - world_to_camera_view(sc, cam, Vector((c.x, c.y, zlow))).y) * px  # image row (y down) of the lowest leaf
        res[f"v{az}"] = al; meta.append(dict(az=az, mpp=mpp, row=row))
    npz = out + f"{name}_fullness_masks.npz"
    np.savez_compressed(npz, name=name, meta=json.dumps(dict(views=meta, width=width, dist=dist, zlow=zlow)), **res)
    print("FULLMASKS", npz)
    r = subprocess.run(["python", os.path.abspath(__file__), npz], capture_output=True, text=True)
    print(r.stdout + r.stderr)


def analyze(path):
    import numpy as np
    from scipy import ndimage as ndi
    from PIL import Image
    z = np.load(path); name = str(z["name"]); M = json.loads(str(z["meta"])); skies = []; tiles = []
    for v in M["views"]:
        al = z[f"v{v['az']}"]; r = CLOSE_M / v["mpp"]; p = int(r) + 2
        m = np.pad(al, p)
        dil = ndi.distance_transform_edt(~m) <= r
        sil = (ndi.binary_fill_holes(ndi.distance_transform_edt(dil) > r)[p:-p, p:-p]) | al
        sil[int(max(0, round(v["row"]))):] = False  # crown only: above the lowest leaf
        cov = al & sil; sky = 1.0 - cov.sum() / max(1, sil.sum()); skies.append(sky)
        print("FULLVIEW", name, "az", v["az"], "sky", round(sky, 3), "silhouette_px", int(sil.sum()))
        t = np.zeros(al.shape + (3,), np.uint8); t[al] = 255; t[sil & ~al] = (60, 110, 230); tiles.append(t)
    print("FULLNESS", name, "sky_mean", round(float(np.mean(skies)), 3), "sky_max", round(float(np.max(skies)), 3),
          "crown_w", round(M["width"], 2), "dist", round(M["dist"], 2))
    Image.fromarray(np.concatenate(tiles, 1)).save(path.replace("_fullness_masks.npz", "_fullness.png"))
    z.close(); os.remove(path)


if __name__ == "__main__" and len(sys.argv) == 2 and sys.argv[1].endswith(".npz"):
    analyze(sys.argv[1])
else:
    render()

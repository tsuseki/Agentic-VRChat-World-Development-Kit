"""Headless Blender: move an existing texture from the old UV layout onto a new UV layout of the same surface
(e.g. a Tripo Studio Smart UV re-unwrap, which drops the texture).
Usage: ... -- <old.fbx> <old_tex.png> <new.(fbx|glb)> <out_dir> <name> [size=2048]
The old mesh stays in its own frame; the new one is fitted onto it (bbox height and bottom-centre, then the best of
the 90-degree turns and a mirror about Z by nearest-vertex distance). Exact transfer, no ray casting: each texel of
each new UV triangle -> its 3D point -> nearest point on the old surface -> old UV -> bilinear sample of the old
texture; then push-pull padding fills every texel outside the islands (no black gutters at low mips).
Writes <out>/<name>_BaseColor_<size>.png and <out>/<name>.fbx (new mesh in the old frame, UV0 'UVMap'), a TRANSFER
line (coverage, farFrac = texels > 0.5 mm from the old surface, should be ~0) and a REPORT line (faces, turn,
meanSurfaceGap ~0 for the same surface, old height). 2048 needs ~2 GB RAM; 4096 needs ~4x that."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:]
old_fbx, old_tex, new_path, out, name = [os.path.abspath(x) if i < 4 else x for i, x in enumerate(a[:5])]
SIZE = int(a[5]) if len(a) > 5 else 2048
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def imp(path):
    before = set(bpy.context.scene.objects)
    (bpy.ops.import_scene.fbx if path.lower().endswith(".fbx") else bpy.ops.import_scene.gltf)(filepath=path)
    new = [o for o in bpy.context.scene.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for v in ob.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
    while len(ob.data.uv_layers) > 1: ob.data.uv_layers.remove(ob.data.uv_layers[1])
    ob.data.uv_layers[0].name = "UVMap"
    return ob, lo, hi


old, olo, ohi = imp(old_fbx); old.name = "old"
new, nlo, nhi = imp(new_path); new.name = "new"
o_bc = Vector(((olo.x + ohi.x) / 2, (olo.y + ohi.y) / 2, olo.z)); n_bc = Vector(((nlo.x + nhi.x) / 2, (nlo.y + nhi.y) / 2, nlo.z))
s = (ohi.z - olo.z) / (nhi.z - nlo.z)
for v in new.data.vertices: v.co = (v.co - n_bc) * s      # bottom-centre at origin, old height
for v in old.data.vertices: v.co = v.co - o_bc               # moved back after the bake
d_old = ohi - olo; d_new = (nhi - nlo) * s
# the service may export with another facing: try 90-degree turns (and a mirror) about Z, keep the one that fits
kd = KDTree(len(old.data.vertices))
for i, v in enumerate(old.data.vertices): kd.insert(v.co, i)
kd.balance()
base = [v.co.copy() for v in new.data.vertices]
step = max(1, len(base) // 600)
best = None
for mirror in (1, -1):
    for k in range(4):
        R = Matrix.Rotation(math.radians(90 * k), 3, "Z") @ Matrix.Diagonal((mirror, 1, 1))
        err = sum(kd.find(R @ c)[2] for c in base[::step]) / len(base[::step])
        if best is None or err < best[0]: best = (err, R, k, mirror)
err, R, k, mirror = best
for v, c in zip(new.data.vertices, base): v.co = R @ c
if mirror < 0: new.data.flip_normals()
mismatch = err
# --- exact transfer, no ray casting: rasterize every new UV triangle, take the nearest point on the old surface
# (the surfaces coincide, so it is the same point), sample the old texture at its old UV. Cycles selected-to-active
# missed on hair strands with inconsistent normals and left black holes (review C1-FumoSmartUV-01).
import numpy as np, bmesh
from mathutils.bvhtree import BVHTree

def tri_data(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    uvl = bm.loops.layers.uv.active; bm.faces.ensure_lookup_table()
    P = np.array([[l.vert.co[:] for l in f.loops] for f in bm.faces], dtype=np.float64)      # (T,3,3)
    U = np.array([[l[uvl].uv[:] for l in f.loops] for f in bm.faces], dtype=np.float64)       # (T,3,2)
    tree = BVHTree.FromBMesh(bm); return P, U, tree, bm

Po, Uo, tree, bm_old = tri_data(old)
Pn, Un, _, bm_new = tri_data(new)
img_old = bpy.data.images.load(old_tex); W0, H0 = img_old.size
src = np.empty(W0 * H0 * 4, dtype=np.float32); img_old.pixels.foreach_get(src); src = src.reshape(H0, W0, 4)[:, :, :3]

def sample(img, uv):                                   # bilinear, wrap, rows bottom-up (Blender pixel order)
    h, w = img.shape[:2]; x = (uv[:, 0] % 1.0) * w - 0.5; y = (uv[:, 1] % 1.0) * h - 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    x0 %= w; y0 %= h; x1 = (x0 + 1) % w; y1 = (y0 + 1) % h
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy) + img[y1, x0] * (1 - fx) * fy + img[y1, x1] * fx * fy)

out_rgb = np.zeros((SIZE, SIZE, 3), dtype=np.float32); cover = np.zeros((SIZE, SIZE), dtype=bool)
pix_tri, pix_xy, pix_bary = [], [], []
for t in range(len(Un)):                               # rasterize (conservative: half-texel tolerance covers edge texels)
    uv = Un[t] * SIZE; lo = np.floor(uv.min(0) - 0.5).astype(int); hi = np.ceil(uv.max(0) + 0.5).astype(int)
    lo = np.clip(lo, 0, SIZE - 1); hi = np.clip(hi, 0, SIZE - 1)
    xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1)); px = xs.ravel() + 0.5; py = ys.ravel() + 0.5
    a, b, c = uv; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12: continue
    l1 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
    l2 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den; l3 = 1 - l1 - l2
    tol = 0.75 / max(1e-9, np.sqrt(abs(den)))          # ~ half a texel in barycentric units
    m = (l1 > -tol) & (l2 > -tol) & (l3 > -tol)
    if not m.any(): continue
    L = np.stack([l1[m], l2[m], l3[m]], 1); L = np.clip(L, 0, None); L /= L.sum(1, keepdims=True)
    pix_tri.append(np.full(m.sum(), t)); pix_xy.append(np.stack([xs.ravel()[m], ys.ravel()[m]], 1)); pix_bary.append(L)
pix_tri = np.concatenate(pix_tri); pix_xy = np.concatenate(pix_xy); pix_bary = np.concatenate(pix_bary)
pts = np.einsum("nk,nkd->nd", pix_bary, Pn[pix_tri])  # 3D point of each texel on the new surface
fidx = np.empty(len(pts), dtype=np.int64); near = np.empty((len(pts), 3)); dist = np.empty(len(pts))
fn = tree.find_nearest
for i, p in enumerate(pts):
    co, _, f, d = fn(Vector(p)); fidx[i] = f; near[i] = co; dist[i] = d
A, B, C = Po[fidx, 0], Po[fidx, 1], Po[fidx, 2]       # barycentric of the nearest point in its old triangle
v0, v1, v2 = B - A, C - A, near - A
d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
dn = d00 * d11 - d01 * d01; dn[dn == 0] = 1e-30
bv = (d11 * d20 - d01 * d21) / dn; bw = (d00 * d21 - d01 * d20) / dn; bu = 1 - bv - bw
uv_old = bu[:, None] * Uo[fidx, 0] + bv[:, None] * Uo[fidx, 1] + bw[:, None] * Uo[fidx, 2]
out_rgb[pix_xy[:, 1], pix_xy[:, 0]] = sample(src, uv_old); cover[pix_xy[:, 1], pix_xy[:, 0]] = True

def push_pull(rgb, a):                                 # fill every uncovered texel from the islands (no black gutters)
    if a.all() or rgb.shape[0] < 2: return rgb
    h, w = a.shape; aw = a.astype(np.float32)
    s = (rgb * aw[..., None]).reshape(h // 2, 2, w // 2, 2, 3).sum((1, 3)); n = aw.reshape(h // 2, 2, w // 2, 2).sum((1, 3))
    small = np.where(n[..., None] > 0, s / np.maximum(n, 1e-6)[..., None], 0); small = push_pull(small, n > 0)
    up = small.repeat(2, 0).repeat(2, 1)
    return np.where(a[..., None], rgb, up)

out_rgb = push_pull(out_rgb, cover)
tgt = bpy.data.images.new(f"{name}_bake", SIZE, SIZE, alpha=False); tgt.colorspace_settings.name = "sRGB"
rgba = np.concatenate([out_rgb, np.ones((SIZE, SIZE, 1), np.float32)], 2)
tgt.pixels.foreach_set(rgba.ravel()); tgt.filepath_raw = f"{out}/{name}_BaseColor_{SIZE}.png"; tgt.file_format = "PNG"; tgt.save()
far = float((dist > 0.0005).mean())                    # texels whose nearest old point is > 0.5 mm away: should be ~0
print(f"TRANSFER texels={len(pts)} coverage={cover.mean():.3f} farFrac={far:.5f} maxDist={dist.max() * 1000:.3f}mm", flush=True)
# export the new mesh with the baked texture
bpy.data.objects.remove(old, do_unlink=True)
for v in new.data.vertices: v.co = v.co + o_bc             # back into the old mesh's frame
bpy.ops.object.select_all(action="DESELECT"); new.select_set(True); bpy.context.view_layer.objects.active = new
new.name = name; new.data.name = name
bpy.ops.export_scene.fbx(filepath=f"{out}/{name}.fbx", use_selection=True, apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP")
sides = [len(p.vertices) for p in new.data.polygons]
print(f"REPORT {name} newFaces={len(sides)} quads={sides.count(4)} tris={sides.count(3)} turn={90 * k}deg mirror={mirror < 0} "
      f"meanSurfaceGap={mismatch * 1000:.3f}mm oldHeight={d_old.z:.4f} dimsOld={tuple(round(x, 4) for x in d_old)} "
      f"dimsNew={tuple(round(x, 4) for x in d_new)}", flush=True)

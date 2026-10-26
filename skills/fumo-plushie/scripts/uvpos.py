"""Headless Blender: rasterise a fumo FBX's UV0 into per-texel data for texture cleanup.
Usage: blender -b --factory-startup --python uvpos.py -- <in.fbx> <out.npz> [size=2048]
Writes npz: tri (H,W int32, -1 = outside every UV island), pos (H,W,3 float32, metres, Blender Z-up frame, front = -Y), nrm (H,W,3).
Image row 0 = top (v = 1)."""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; src, out = os.path.abspath(a[0]), os.path.abspath(a[1]); N = int(a[2]) if len(a) > 2 else 2048
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=src)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
mw = ob.matrix_world.copy(); ob.parent = None; ob.matrix_world = mw
bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data; me.calc_loop_triangles(); uv = me.uv_layers[0].data
tri = -np.ones((N, N), np.int32); pos = np.zeros((N, N, 3), np.float32); nrm = np.zeros((N, N, 3), np.float32)
for ti, t in enumerate(me.loop_triangles):
    P = np.array([me.vertices[i].co[:] for i in t.vertices]); Nn = np.array([me.vertices[i].normal[:] for i in t.vertices])
    U = np.array([[uv[l].uv[0] * N, (1 - uv[l].uv[1]) * N] for l in t.loops])
    x0, x1 = int(max(0, np.floor(U[:, 0].min()))), int(min(N - 1, np.ceil(U[:, 0].max())))
    y0, y1 = int(max(0, np.floor(U[:, 1].min()))), int(min(N - 1, np.ceil(U[:, 1].max())))
    if x1 < x0 or y1 < y0: continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (U[1, 1] - U[2, 1]) * (U[0, 0] - U[2, 0]) + (U[2, 0] - U[1, 0]) * (U[0, 1] - U[2, 1])
    if abs(d) < 1e-9: continue
    l0 = ((U[1, 1] - U[2, 1]) * (xs - U[2, 0]) + (U[2, 0] - U[1, 0]) * (ys - U[2, 1])) / d
    l1 = ((U[2, 1] - U[0, 1]) * (xs - U[2, 0]) + (U[0, 0] - U[2, 0]) * (ys - U[2, 1])) / d
    l2 = 1 - l0 - l1; m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
    if not m.any(): continue
    yy, xx = ys[m].astype(int) - 0, xs[m].astype(int) - 0
    yy = (ys[m] - 0.5).astype(int); xx = (xs[m] - 0.5).astype(int)
    tri[yy, xx] = ti
    pos[yy, xx] = l0[m][:, None] * P[0] + l1[m][:, None] * P[1] + l2[m][:, None] * P[2]
    nrm[yy, xx] = l0[m][:, None] * Nn[0] + l1[m][:, None] * Nn[1] + l2[m][:, None] * Nn[2]
np.savez_compressed(out, tri=tri, pos=pos, nrm=nrm)
print("UVPOS_OK", out, "coverage", round(float((tri >= 0).mean()), 3), "tris", len(me.loop_triangles))

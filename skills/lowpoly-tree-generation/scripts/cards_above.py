"""Leaf cards (UVMap u < 0.75: one-texture column atlas, bark at u >= 0.76) of a packed tree FBX whose faces lie above
given points within a horizontal radius: count per radius (0.6 / 1.0 / 1.5 / 2.5 m) and the lowest card height.
Use it on a point bare_limbs.py flags under the canopy (its rule: opaque leaves above within 0.6 m) before adding cards:
if cards are already there, the checker's classification is the problem, not the crown.
  python .omp/scripts/tool.py blender --script .omp/skills/lowpoly-tree-generation/scripts/cards_above.py -- <pack.fbx> x,y,z [x,y,z ...]
Points in Blender coordinates of the imported FBX (as bare_limbs.py prints them). Prints ABOVE <pt> R <r> faces N lowest Z."""
import bpy, sys, os, math
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.abspath(a[0]))
ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]; me = ob.data; W = ob.matrix_world
uv = me.uv_layers[0].data
cards = []
for p in me.polygons:
    if sum(uv[i].uv.x for i in p.loop_indices) / p.loop_total >= 0.75: continue
    cards.append(W @ p.center)
for q in a[1:]:
    x, y, z = map(float, q.split(","))
    for R in (0.6, 1.0, 1.5, 2.5):
        c = [v for v in cards if math.hypot(v.x - x, v.y - y) < R and v.z > z]
        print("ABOVE", q, "R", R, "faces", len(c), "lowest", round(min((v.z for v in c), default=-1), 2))

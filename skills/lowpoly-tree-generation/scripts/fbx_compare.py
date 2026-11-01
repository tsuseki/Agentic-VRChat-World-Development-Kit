"""Compare two exported tree FBX files vertex by vertex and loop by loop.

  python .omp/scripts/tool.py blender --script .omp/skills/lowpoly-tree-generation/scripts/fbx_compare.py -- <a.fbx> <b.fbx> [<a2.fbx> <b2.fbx> ...]

Prints `FBXCMP <name> verts N polys N loops N | moved_verts N max_move_mm X | uv {ch0 name/name: D, ch1 name/name: D} col {..} |
normal_max_deg D | topology_same Y/N` per pair (same exporter => same order). UV channels are compared by index (channel 0
`UVMap`, channel 1 `Lightmap`; the key shows both files' names). A base-cone fix must report topology_same Y and every uv/col
diff 0; a lightmap-UV pass changes channel 1 only.
"""
import bpy, sys, os, math

argv = sys.argv[sys.argv.index("--") + 1:]


def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(p))
    ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]; me = ob.data
    W = ob.matrix_world
    d = dict(co=[tuple(W @ v.co) for v in me.vertices], polys=[tuple(p.vertices) for p in me.polygons],
             loops=len(me.loops), uvs=[(u.name, [tuple(x.uv) for x in u.data]) for u in me.uv_layers],
             col={c.name: [tuple(x.color) for x in c.data] for c in me.color_attributes},
             nrm=[tuple(n.vector) for n in me.corner_normals] if me.has_custom_normals else None, name=ob.name,
             mats=[m.name for m in me.materials])
    return d


for a, b in zip(argv[0::2], argv[1::2]):
    A = load(a); Bm = load(b)
    same = A["polys"] == Bm["polys"] and len(A["co"]) == len(Bm["co"]) and A["loops"] == Bm["loops"] and A["mats"] == Bm["mats"]
    if not same: print("FBXCMP", os.path.basename(a), "topology_same N"); continue
    mv = [math.dist(p, q) for p, q in zip(A["co"], Bm["co"])]
    mx = lambda X, Y: max([max(abs(u - v) for u, v in zip(p, q)) for p, q in zip(X, Y)] or [0])
    uvd = {"%d %s/%s" % (i, ua[0], ub[0]): mx(ua[1], ub[1]) for i, (ua, ub) in enumerate(zip(A["uvs"], Bm["uvs"]))}
    if len(A["uvs"]) != len(Bm["uvs"]): uvd["channels"] = "%d/%d" % (len(A["uvs"]), len(Bm["uvs"]))
    cd = {k: mx(A["col"][k], Bm["col"][k]) for k in A["col"]}
    nd = 0.0
    if A["nrm"]:
        for p, q in zip(A["nrm"], Bm["nrm"]):
            dot = max(-1.0, min(1.0, sum(u * v for u, v in zip(p, q)))); nd = max(nd, math.degrees(math.acos(dot)))
    print("FBXCMP %s verts %d polys %d loops %d | moved_verts %d max_move_mm %.2f | uv %s col %s | normal_max_deg %.3f | topology_same Y" % (
        os.path.basename(a), len(A["co"]), len(A["polys"]), A["loops"], sum(1 for d in mv if d > 1e-6), max(mv) * 1000,
        {k: (round(v, 7) if isinstance(v, float) else v) for k, v in uvd.items()}, {k: round(v, 5) for k, v in cd.items()}, nd))

# Finishing stage for an already-built tree .blend (re-run on an approved .blend after hand edits,
# or to retrofit UVs/normals). Headless:
#   blender -b --factory-startup <Species>_Tree.blend -P tree_finish.py -- <Species> <proxy> --out <dir> [--sprig]
# <proxy>: ellipsoid | capsule | cone | hull. Works on <Species>_Tree, or <Species>_Tree_LOD0/LOD1 if present.
# Steps:
#   1. (--sprig) cap every branch end with a short pointed cone (no open/flat ends) and add leaf
#      cards on any branch end that no card covers, so no limb ends bare in the air
#   2. (--sprig) centre the leaf cards on their anchor point (atlas = one centred cluster)
#   3. bark UVs: uniform-density cylinders (tree_uv.cylinder_uvs), Lightmap UV re-laid (lightmap_uv.repack)
#   4. crown-proxy normals + outward card winding (tree_normals.transfer_crown_normals)
#   5. export <out>/<Species>_Tree.fbx and save the .blend
import bpy, bmesh, sys, os, math, random
from mathutils import Vector
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree_normals import transfer_crown_normals, leaf_normal_spread
from tree_uv import cylinder_uvs, stretch_stats, tubes
import lightmap_uv

args = sys.argv[sys.argv.index("--") + 1:]
NAME, KIND = args[0], args[1]
OLIVE = "--sprig" in args
OUT = os.path.abspath(args[args.index("--out") + 1] if "--out" in args else ".") + "/"
CARD_CENTRE = 0.42  # fraction of the card height the card is pulled back so the cluster sits on its anchor


def leaf_islands(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f.material_index != 1 or f.index in seen:
            continue
        isl, stack = [], [f]; seen.add(f.index)
        while stack:
            g = stack.pop(); isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.material_index == 1 and h.index not in seen:
                        seen.add(h.index); stack.append(h)
        out.append(isl)
    return out


def card_axis(isl, uvl):
    """3D vector from the card's v=0 edge to its v=1 edge (card 'up', length = card height)."""
    lo, hi = [], []
    for f in isl:
        for l in f.loops:
            (hi if l[uvl].uv.y > 0.5 else lo).append(l.vert.co)
    return sum(hi, Vector()) / len(hi) - sum(lo, Vector()) / len(lo)


def add_card(bm, uvl, base, d, s):
    d = d.normalized(); side = d.orthogonal().normalized()
    n = d.cross(side); w = side * s * 0.5; fv = n * s * 0.12; top = base + d * s
    vs = [bm.verts.new(x) for x in (base - w, base + fv, base + w, top + w, top + fv, top - w)]
    for idx, us in (((0, 1, 4, 5), (0, .5, .5, 0)), ((1, 2, 3, 4), (.5, 1, 1, .5))):
        f = bm.faces.new([vs[k] for k in idx]); f.material_index = 1
        for loop, u, v in zip(f.loops, us, (0, 0, 1, 1)):
            loop[uvl].uv = (u, v)


def finish_olive(ob, rng):
    me = ob.data
    ends = []  # (tip centre, direction, radius) of every tube
    for rings, _ in tubes(me):
        c1 = sum((me.vertices[k].co for k in rings[-1]), Vector()) / len(rings[-1])
        c0 = sum((me.vertices[k].co for k in rings[-2]), Vector()) / len(rings[-2])
        r = sum((me.vertices[k].co - c1).length for k in rings[-1]) / len(rings[-1])
        ends.append((rings[-1], c1, (c1 - c0).normalized(), r))
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    uvl = bm.loops.layers.uv["UVMap"]
    # 1a. pointed cone caps
    vlist = list(bm.verts)  # bm.verts[i] goes stale once new verts are added
    for ring, c, d, r in ends:
        apex = bm.verts.new(c + d * max(r * 2.5, 0.02))
        n = len(ring)
        for s in range(n):
            a, b = vlist[ring[s]], vlist[ring[(s + 1) % n]]
            f = bm.faces.new((a, b, apex)); f.material_index = 0; f.smooth = True
            if f.normal.dot((a.co + b.co) / 2 - c) < 0:
                f.normal_flip()
    # 2. centre existing cards on their anchors
    islands = leaf_islands(bm)
    size = sorted(card_axis(i, uvl).length for i in islands)[len(islands) // 2]
    for isl in islands:
        ax = card_axis(isl, uvl)
        for v in {v for f in isl for v in f.verts}:
            v.co -= ax * CARD_CENTRE
    # 1b. cover bare branch ends (thin ends must sit in foliage; thick ends are hidden by children)
    kd = KDTree(sum(len(i) for i in islands) * 6)
    k = 0
    for isl in islands:
        for v in {v for f in isl for v in f.verts}:
            kd.insert(v.co, k); k += 1
    kd.balance()
    added = 0
    for ring, c, d, r in ends:
        if r > 0.03 or c.z < 0.8:
            continue
        if kd.find(c)[2] is not None and kd.find(c)[2] < size * 0.45:
            continue
        for _ in range(2):
            dd = (d + Vector((rng.uniform(-.5, .5), rng.uniform(-.5, .5), rng.uniform(0, .6)))).normalized()
            add_card(bm, uvl, c - dd * size * CARD_CENTRE, dd, size); added += 1
    bm.to_mesh(me); bm.free()
    return len(ends), added


def finish(ob, rng):
    stats = {}
    if OLIVE:
        stats["tips_capped"], stats["cards_added"] = finish_olive(ob, rng)
    stats["stretch_before"] = stretch_stats(ob)
    cylinder_uvs(ob)
    stats["stretch_after"] = stretch_stats(ob)
    me = ob.data
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    stats["lightmap"] = lightmap_uv.repack(ob, check=False)
    ob.select_set(False)
    stats["proxy"] = transfer_crown_normals(ob, KIND)
    stats["leaf_ndot"] = leaf_normal_spread(ob)
    stats["tris"] = sum(len(p.vertices) - 2 for p in me.polygons)
    return stats


lods = [o for n in (f"{NAME}_Tree", f"{NAME}_Tree_LOD0", f"{NAME}_Tree_LOD1") if (o := bpy.data.objects.get(n))]
for i, o in enumerate(lods):
    print("STAT", o.name, finish(o, random.Random(i + 5)))
bpy.ops.object.select_all(action='DESELECT')
for o in lods:
    o.hide_render = False; o.location = (0, 0, 0); o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT + f"{NAME}_Tree.fbx", use_selection=True,
    apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Z', axis_up='Y', bake_space_transform=True,
    mesh_smooth_type='OFF', path_mode='STRIP', use_mesh_modifiers=True, add_leaf_bones=False, object_types={'MESH'})
bpy.ops.wm.save_mainfile()
print("FINISH_OK", NAME)

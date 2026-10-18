"""Bark connectivity check for built trees (Blender).

floating_bark_components(ob) -> (n, islands): bark (material 0) faces split into connected islands (each tube and
each buried base cone is its own island). Islands reaching z <= GROUND are rooted; two islands are joined when their
surfaces intersect (BVH face overlap) or any vertex of one lies on or inside the other (nearest-face test against the
outward face normal, TOL m slack), so a child whose base cone is buried in its parent counts as connected. n = islands not
reachable from a rooted island (floating bark); islands = [(z_min, z_max, faces, gap_m)] of those, highest first,
gap = the island's smallest vertex distance to the rooted bark.
CLI (one Blender process for many files):
  blender -b --python tree_checks.py -- <a_Tree.blend> [<b_Tree.blend> ...] [--lod LOD1]
prints `FLOAT <object> floating_bark_components N [islands]` for every *_Tree_<lod> object in each file.
"""
import sys
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

GROUND, TOL = 0.02, 0.01


def floating_bark_components(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
    fl = [(round(i["lo"].z, 2), round(i["hi"].z, 2), i["n"], round(i["gap"], 3)) for i in floating_islands(bm)]
    bm.free()
    return len(fl), sorted(fl, reverse=True)


def floating_islands(bm):
    """Floating bark islands of a bmesh: dicts with faces (bark face indices), lo, hi (bbox), n, gap."""
    bm.faces.index_update(); bm.verts.index_update(); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    faces = [f for f in bm.faces if f.material_index == 0]
    parent = {}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for f in faces:
        vs = [v.index for v in f.verts]
        for v in vs: parent.setdefault(v, v)
        r0 = find(vs[0])
        for v in vs[1:]:
            rv = find(v)
            if rv != r0: parent[rv] = r0
    groups = {}
    for f in faces: groups.setdefault(find(f.verts[0].index), []).append(f)
    isl = []
    for fs in groups.values():
        vids = sorted({v.index for f in fs for v in f.verts})
        co = [bm.verts[i].co.copy() for i in vids]
        lo = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
        hi = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
        remap = {i: j for j, i in enumerate(vids)}
        tree = BVHTree.FromPolygons(co, [[remap[v.index] for v in f.verts] for f in fs])
        isl.append(dict(co=co, lo=lo, hi=hi, tree=tree, n=len(fs), faces=[f.index for f in fs]))
    def touches(a, b):  # any vertex of a on/inside b
        if any(a["lo"][k] > b["hi"][k] + TOL or a["hi"][k] < b["lo"][k] - TOL for k in range(3)): return False
        for p in a["co"]:
            if any(p[k] < b["lo"][k] - TOL or p[k] > b["hi"][k] + TOL for k in range(3)): continue
            loc, nrm, _, dist = b["tree"].find_nearest(p)
            if loc is not None and (dist <= TOL or (p - loc).dot(nrm) < 0.0): return True
        return False
    n = len(isl)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            a, b = isl[i], isl[j]
            if any(a["lo"][k] > b["hi"][k] + TOL or a["hi"][k] < b["lo"][k] - TOL for k in range(3)): continue
            if a["tree"].overlap(b["tree"]) or touches(a, b) or touches(b, a): adj[i].add(j); adj[j].add(i)
    seen = {i for i in range(n) if isl[i]["lo"].z <= GROUND}
    st = list(seen)
    while st:
        for j in adj[st.pop()]:
            if j not in seen: seen.add(j); st.append(j)
    def gap(i):
        return min((min(isl[j]["tree"].find_nearest(p)[3] for p in isl[i]["co"]) for j in seen), default=-1.0)
    out = [isl[i] for i in range(n) if i not in seen]
    for i in range(n):
        if i not in seen: isl[i]["gap"] = gap(i)
    return out


if __name__ == "__main__":
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    lod = argv[argv.index("--lod") + 1] if "--lod" in argv else "LOD1"
    files = [a for a in argv if a.endswith(".blend")]
    for path in files:
        with bpy.data.libraries.load(path) as (src, dst):
            dst.objects = [o for o in src.objects if o.endswith(f"_Tree_{lod}")]
        for ob in dst.objects:
            if ob is None: continue
            n, fl = floating_bark_components(ob)
            print("FLOAT", path, ob.name, "floating_bark_components", n, fl[:8], flush=True)
            me = ob.data; bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)

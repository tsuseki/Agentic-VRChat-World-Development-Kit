"""Crown-proxy normal transfer for leaf cards (used by tree_family_build.py and tree_finish.py).

The leaf cards (material index 1) receive the normals of a smooth proxy volume fitted to the crown,
so the canopy shades as one soft mass instead of hundreds of flat cards. Bark keeps its own normals.
Proxy kinds:
  'ellipsoid' : UV sphere scaled to the leaf-vertex bounding box (spherical / flattened crowns)
  'capsule'   : tall ellipsoid for columnar crowns (same fit, kept separate for clarity in reports)
  'hull'      : icosphere shrink-wrapped onto the convex hull of the leaf vertices, then smoothed
                (clumpy, irregular crowns)
The Data Transfer modifier is applied, so the custom split normals live in the mesh and are written
by the FBX exporter; Unity must import them with ModelImporter normals = Import.
"""
import bpy, bmesh
from mathutils import Vector


def _leaf_points(ob):
    me = ob.data
    vids = {v for p in me.polygons if p.material_index == 1 for v in p.vertices}
    return vids, [me.vertices[i].co.copy() for i in vids]


def _new_obj(name, me):
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


def make_proxy(ob, kind, inflate=1.05):
    vids, pts = _leaf_points(ob)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c, half = (lo + hi) / 2, (hi - lo) / 2
    me = bpy.data.meshes.new(ob.name + "_proxy")
    bm = bmesh.new()
    if kind in ("ellipsoid", "capsule"):
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
        for v in bm.verts:
            v.co = c + Vector((v.co.x * half.x, v.co.y * half.y, v.co.z * half.z)) * inflate
        bm.to_mesh(me); bm.free()
        return _new_obj(ob.name + "_proxy", me)
    # hull: convex hull of the leaf points, then an icosphere shrink-wrapped onto it and smoothed
    hb = bmesh.new()
    for p in pts:
        hb.verts.new(p)
    bmesh.ops.convex_hull(hb, input=hb.verts[:])
    hme = bpy.data.meshes.new(ob.name + "_hull"); hb.to_mesh(hme); hb.free()
    hull = _new_obj(ob.name + "_hull", hme)
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=max(half) * 2.0)
    for v in bm.verts:
        v.co += c
    bm.to_mesh(me); bm.free()
    px = _new_obj(ob.name + "_proxy", me)
    sw = px.modifiers.new("sw", 'SHRINKWRAP'); sw.target = hull; sw.wrap_method = 'NEAREST_SURFACEPOINT'
    sm = px.modifiers.new("sm", 'SMOOTH'); sm.factor = 1.0; sm.iterations = 8
    _apply_all(px)
    bpy.data.objects.remove(hull, do_unlink=True)
    for v in px.data.vertices:  # gentle inflation so smoothing does not pull it inside the cards
        v.co = c + (v.co - c) * inflate
    return px


def _apply_all(o):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    o.select_set(False)


def align_card_winding(ob, proxy):
    """Flip every leaf card whose front face points into the crown, so its geometric front agrees with
    the transferred (outward) normal. Otherwise renderers that flip the shading normal on back faces
    (Cycles; a VFACE-flipping two-sided foliage shader) turn half the cards' volume normals inward
    and the crown renders near-black. Cards are the connected islands of leaf faces (1-2 quads)."""
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromObject(proxy, bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    seen, flip = set(), []
    for f in bm.faces:
        if f.material_index != 1 or f.index in seen: continue
        island, stack = [], [f]; seen.add(f.index)
        while stack:
            g = stack.pop(); island.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.material_index == 1 and h.index not in seen:
                        seen.add(h.index); stack.append(h)
        n = sum((g.normal * g.calc_area() for g in island), Vector())
        c = sum((g.calc_center_median() for g in island), Vector()) / len(island)
        loc, pn, _, _ = tree.find_nearest(c)
        if pn is not None and n.dot(pn) < 0:
            flip.extend(island)
    bmesh.ops.reverse_faces(bm, faces=flip, flip_multires=False)
    bm.to_mesh(ob.data); bm.free()
    return len(flip)


def transfer_crown_normals(ob, kind, inflate=1.05, cluster=None, crown_mix=0.35):
    """Apply proxy normals to leaf cards of `ob`; returns the proxy dimensions for reporting.
    cluster (m, ellipsoid/capsule only): cards are binned into cells of that size and each leaf vertex's
    normal points out of ITS cell's card centroid, mixed with crown_mix of the crown ellipsoid and a little
    up, so every leaf clump shades as its own small dome instead of the whole crown as one bubble."""
    proxy = make_proxy(ob, kind, inflate)
    for p in proxy.data.polygons:
        p.use_smooth = True
    if ob.data.has_custom_normals:  # re-run on a finished mesh: zero vectors = back to default normals
        ob.data.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(ob.data.loops))
    align_card_winding(ob, proxy)
    vids, pts = _leaf_points(ob)
    if kind in ("ellipsoid", "capsule"):
        # analytic: each leaf loop gets the ellipsoid gradient direction at its vertex,
        # (p - c) / r^2 with c / r = leaf-bounds centre / half extents; bark keeps its own normals
        lo = Vector((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
        hi = Vector((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
        c, r = (lo + hi) / 2, (hi - lo) / 2
        me = ob.data
        loops = [n.vector.copy() for n in me.corner_normals]
        for p in me.polygons:
            p.use_smooth = True
        cent = {}
        if cluster:
            key = lambda q: (int(q.x // cluster), int(q.y // cluster), int(q.z // cluster))
            acc = {}
            for p in me.polygons:
                if p.material_index == 1:
                    k = key(p.center); a = acc.setdefault(k, [Vector(), 0]); a[0] += p.center; a[1] += 1
            cent = {k: v / n for k, (v, n) in acc.items()}
        for p in me.polygons:
            if p.material_index != 1:
                continue
            cc = cent.get(key(p.center)) if cluster else None
            for li in p.loop_indices:
                q = me.vertices[me.loops[li].vertex_index].co; d = q - c
                n = Vector((d.x / r.x ** 2, d.y / r.y ** 2, d.z / r.z ** 2)).normalized()
                if cc is not None:
                    o = q - cc
                    o = o.normalized() if o.length > 1e-4 else n
                    n = (n * crown_mix + o * (1 - crown_mix) + Vector((0, 0, 0.25))).normalized()
                loops[li] = n
        me.normals_split_custom_set(loops)
        dims = tuple(round(2 * x, 2) for x in r)
        bpy.data.objects.remove(proxy, do_unlink=True)
        return dims
    vg = ob.vertex_groups.new(name="leaves"); vg.add(list(vids), 1.0, 'REPLACE')
    for p in ob.data.polygons:
        p.use_smooth = True  # bark was smooth already; leaf cards must be smooth to hold custom normals
    dt = ob.modifiers.new("crown_normals", 'DATA_TRANSFER')
    dt.object = proxy
    dt.use_loop_data = True
    dt.data_types_loops = {'CUSTOM_NORMAL'}
    dt.loop_mapping = 'POLYINTERP_NEAREST'
    dt.vertex_group = "leaves"
    dt.mix_mode = 'REPLACE'; dt.mix_factor = 1.0
    _apply_all(ob)
    ob.vertex_groups.remove(ob.vertex_groups["leaves"])
    dims = tuple(round(x, 2) for x in proxy.dimensions)
    bpy.data.objects.remove(proxy, do_unlink=True)
    return dims


def leaf_normal_spread(ob):
    """Sanity metric: mean |dot| between each leaf loop normal and its face normal. Flat cards = 1.0."""
    me = ob.data
    tot = n = 0.0
    for p in me.polygons:
        if p.material_index != 1:
            continue
        for li in p.loop_indices:
            tot += abs(me.corner_normals[li].vector.dot(p.normal)); n += 1
    return round(tot / max(1, n), 3)

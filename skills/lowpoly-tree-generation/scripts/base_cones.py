"""Base cones that stay inside their parent tube (kit module; bpy-free, needs mathutils + bmesh meshes only).

A child limb's base ring is closed by a cone buried in the parent (tree_family_build.py `tube`, `bury`). On a thin lobed or
4/3-sided parent the cone apex and the ring corners can leave the parent on its far side, where the cone faces show as light
triangular bark wedges (BoothAssets olives, user 2026-10-23: "branches on the other side of the trunk"). This module works on
the meshed tubes only (no skeleton), so the builder (`clamp(bm)` before the cards) and the shipped meshes (BoothAssets
`Tools/trees/basecone_fix.py`, `basecone_check.py`) use the same code.

Tubes = connected components of the mesh that contain triangles (cards are lone quads). A tube's two apex vertices (all faces
triangles) end its ring chain; the apex whose first ring is wider is the base cone, the other is the tapered tip. A tube whose
base apex lies below the ground (the root skirt) is a ground stem: no parent. The parent is the other tube whose ring-centroid
axis passes closest (in local radii) to the child's base ring centre and is wider there than the child (siblings at one fork
have equal radii and are never parents). "Outside" = signed distance to the UNION of every other tube > 0 (nearest-surface
distance, negative inside by ray parity): a cone point hidden in a sibling or grandparent is fine, only what a player can see
counts. Samples per child: the apex, every ring vertex, the ring->apex edges at 0.5 and 0.8, and a barycentric grid inside every cone
triangle (10 points each; edge samples alone miss a face that crosses a crease between equal limbs).

`scan(bm, fix=False, k=1.0)` returns the report; with fix=True it also moves vertices:
  1. ring vertices > TRIGGER outside are pulled toward the parent axis to TARGET inside (nothing else moves; UVs are per
     loop and untouched);
  2. the apex slides along the line to the ring centre (the cone gets shallower: "apex depth clamped") to the smallest
     depth at which the apex is TARGET inside and every edge sample is within EDGE_OK.
TOL, TRIGGER, TARGET, EDGE_OK are metres at the SHIPPED scale (the pack scales every mesh by SHIP_SCALE 0.7). `k` = mesh
units per shipped metre: 1.0 on a packed mesh, 1 / SHIP_SCALE on the builder's mesh (`clamp` default).
"""
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOL = 0.003      # checker: flagged when any cone sample lies more than this outside the other tubes (m, shipped scale)
TRIGGER = 0.002  # fix: a child is touched when a sample is more than this outside
TARGET = 0.001   # fix: pulled vertices / apex end this far inside
EDGE_OK = 0.0015  # fix: edge samples must be within this of the surface after the apex slide
SHIP_SCALE = 0.7  # the pack scales every mesh by this: builder-size tolerances are the shipped ones / SHIP_SCALE

_RAYS = [Vector(v).normalized() for v in ((1, 0.31, 0.17), (-0.23, 1, 0.41), (0.19, -0.37, 1))]


def _components(bm):
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; seen.add(v.index); cur = [v]
        while stack:
            x = stack.pop()
            for e in x.link_edges:
                w = e.other_vert(x)
                if w.index not in seen: seen.add(w.index); stack.append(w); cur.append(w)
        comps.append(cur)
    return comps


def _ring_chain(apex, apexes):
    ring0 = [e.other_vert(apex) for e in apex.link_edges]
    rs = set(v.index for v in ring0); order = [ring0[0]]; prev = None
    while len(order) < len(ring0):
        cur = order[-1]
        nb = [e.other_vert(cur) for e in cur.link_edges if e.other_vert(cur).index in rs and (prev is None or e.other_vert(cur) is not prev)]
        nb = [w for w in nb if w not in order]
        if not nb: return None
        prev = cur; order.append(nb[0])
    rings = [order]; before = {apex.index}; cur_set = set(v.index for v in order)
    while True:
        nxt = []
        for v in rings[-1]:
            c = [e.other_vert(v) for e in v.link_edges if e.other_vert(v).index not in cur_set and e.other_vert(v).index not in before]
            if len(c) != 1: return rings
            nxt.append(c[0])
        if any(w.index in apexes for w in nxt): return rings
        before = cur_set; cur_set = set(w.index for w in nxt); rings.append(nxt)
        if len(rings) > 600: return None


def _centroid(vs): return sum((v.co for v in vs), Vector()) / len(vs)


class _Tubes:
    def __init__(self, bm):
        bm.verts.index_update(); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        self.bm = bm; self.tubes = []; self.bad = []
        for comp in _components(bm):
            if not any(len(f.verts) == 3 for v in comp for f in v.link_faces): continue
            apexes = [v for v in comp if v.link_faces and all(len(f.verts) == 3 for f in v.link_faces)
                      and any(len(f.verts) == 4 for e in v.link_edges for f in e.other_vert(v).link_faces)]
            ids = set(v.index for v in apexes)
            if len(apexes) != 2: self.bad.append(len(apexes)); continue   # open-based ground stem (no base cone): not a child
            chains = [_ring_chain(a, ids) for a in apexes]
            if None in chains: self.bad.append(-1); continue
            rad = lambda rg: sum((v.co - _centroid(rg)).length for v in rg) / len(rg)
            k = 0 if rad(chains[0][0]) >= rad(chains[1][0]) else 1
            rings = chains[k]
            t = dict(comp=comp, apex=apexes[k], rings=rings, axis=[(_centroid(rg), rad(rg)) for rg in rings],
                     tri=[f for f in {f for v in comp for f in v.link_faces} if len(f.verts) == 3],
                     faces=list({f for v in comp for f in v.link_faces}), bvh=None, id=len(self.tubes))
            self.tubes.append(t)
        for t in self.tubes: self.refresh_box(t)

    def refresh_box(self, t):
        cs = [v.co for v in t["comp"]]
        t["lo"] = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
        t["hi"] = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
        t["bvh"] = None

    def bvh(self, t):
        """Two surfaces per tube: every quad split along corner diagonal 0-2 (what Blender and Unity draw from the FBX
        corner order) and along 1-3 (the other split, in case an importer flips it). Built from explicit triangles in the
        mesh's own corner order, never `FromPolygons` (it splits quads the other way and the 0-2 wedge was missed)."""
        if t["bvh"] is None:
            vs = t["comp"]; idx = {v.index: j for j, v in enumerate(vs)}; co = [v.co.copy() for v in vs]; out = []
            for split in (0, 1):
                tris = []
                for f in t["faces"]:
                    v = [idx[x.index] for x in f.verts]
                    if len(v) == 4 and split == 1: tris += [[v[1], v[2], v[3]], [v[1], v[3], v[0]]]
                    else: tris += [[v[0], v[i], v[i + 1]] for i in range(1, len(v) - 1)]
                out.append(BVHTree.FromPolygons(co, tris, all_triangles=True))
            t["bvh"] = out
        return t["bvh"]

    @staticmethod
    def _bbdist(t, q):
        return Vector((max(t["lo"].x - q.x, 0, q.x - t["hi"].x), max(t["lo"].y - q.y, 0, q.y - t["hi"].y), max(t["lo"].z - q.z, 0, q.z - t["hi"].z))).length

    def sd(self, t, q):
        """signed distance to tube t: the worse (larger) of the two quad splits; negative = inside"""
        best = -1e9
        for b in self.bvh(t):
            r = b.find_nearest(q)
            if r[0] is None: return 1e9
            d = (q - r[0]).length; ins = 0
            for rv in _RAYS:
                n = 0; o = q + rv * 1e-5
                for _ in range(60):
                    h = b.ray_cast(o, rv)
                    if h[0] is None: break
                    n += 1; o = h[0] + rv * 1e-5
                ins += n & 1
            best = max(best, -d if ins >= 2 else d)
        return best

    def usd(self, excl, q):
        """signed distance to the union of every tube but `excl` (negative = hidden inside another tube)"""
        best = 1e9
        for o in self.tubes:
            if o is excl or self._bbdist(o, q) >= best: continue
            best = min(best, self.sd(o, q))
        return best

    @staticmethod
    def axis_dist(t, c):
        best = (1e9, 0.0, c)
        for (a, ra), (b, rb) in zip(t["axis"], t["axis"][1:]):
            ab = b - a; L2 = ab.length_squared
            s = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, (c - a).dot(ab) / L2))
            P = a + ab * s; d = (c - P).length; r = ra + (rb - ra) * s
            if d / max(r, 1e-4) < best[0]: best = (d / max(r, 1e-4), r, P)
        return best


def _face_pts(ring, apex, n=4):
    """Barycentric grid inside every cone triangle (ring[s], ring[s+1], apex): where three equal limbs meet, a cone face can
    cross the crease between two of them with its middle outside while every edge point is inside."""
    out = []; m = len(ring)
    for s in range(m):
        a, b = ring[s], ring[(s + 1) % m]
        out += [a + (b - a) * (i + 0.33) / n + (apex - a) * (j + 0.33) / n for i in range(n) for j in range(n - i)]
    return out


def _samples(t, apex=None):
    ap = (t["apex"].co if apex is None else apex).copy(); ring0 = t["rings"][0]; rc = [v.co.copy() for v in ring0]
    return ([("apex", ap)] + [("ring", c) for c in rc] + [("edge", c.lerp(ap, f)) for c in rc for f in (0.5, 0.8)]
            + [("face", q) for q in _face_pts(rc, ap)])


def _pick_parent(T, t, c, r0):
    """The wider tube nearest (in its local radii, up to 4) to the child's base ring centre, or None: a child on a tube
    that is not wider than itself (bamboo nodes, a limb on a thin twig) has no parent to hide its cone in."""
    best = None
    for p in T.tubes:
        if p is t: continue
        nd, pr, P = T.axis_dist(p, c)
        if nd < 4.0 and pr > r0 * 1.01 and (best is None or nd < best[0]): best = (nd, p, P, pr)
    return best


def scan(bm, fix=False, k=1.0):
    """Report on every child tube's base cone; fix=True also moves the offending vertices (bm in place).
    A child with a wider parent tube nearby: the cone must lie inside the other tubes (ring corners pulled toward the
    parent axis by at most 1.5 x the child radius, then the apex slid toward the ring centre). A child with no wider tube
    around it ("flush"): nothing can hide the cone, so it is closed flat on its own tube (apex moved onto the ring
    plane). Any child whose cone cannot be hidden in the parent after the pull and slide is closed flush the same way
    (counted in `unfixed`). A child is flagged only while a cone sample is > TOL outside the other tubes AND its apex stands
    more than TOL off the ring plane.
    Returns dict(tubes, roots, children, flush, bad, flagged=[...], clamped=n, unfixed=n)."""
    T = _Tubes(bm); tol, trig, tgt, eok = TOL * k, TRIGGER * k, TARGET * k, EDGE_OK * k
    flagged = []; roots = flush = children = clamped = unfixed = 0
    for t in T.tubes:
        ap = t["apex"].co
        if ap.z < -0.01: roots += 1; continue
        ring0 = t["rings"][0]; c = _centroid(ring0); r0 = t["axis"][0][1]
        par = _pick_parent(T, t, c, r0); children += 1
        if par is None: flush += 1
        p, Q = (par[1], par[2]) if par else (None, c)
        res = [(kind, T.usd(t, q)) for kind, q in _samples(t)]
        depth = (ap - c).length; worst = max(d for _, d in res)
        moved = False
        if fix and worst > trig and depth > tol:
            if par is None:
                t["apex"].co = c.copy(); moved = True
            else:
                reach = (1.5 if par[3] >= 1.5 * r0 else 0.5) * r0   # a parent barely wider than the child (equal forks): the ring moves little, the cone closes flush
                for v in ring0:                  # 1. ring corners that leave the other tubes: pulled toward the parent axis
                    d = T.usd(t, v.co)
                    if d <= trig: continue
                    v0 = v.co.copy(); lo, hi = 0.0, None; best = (d, 0.0)
                    smax = min(1.0, reach / max((Q - v0).length, 1e-9))
                    for i in range(1, 21):
                        s_ = smax * i / 20
                        v.co = v0.lerp(Q, s_); dd = T.usd(t, v.co)
                        if dd < best[0]: best = (dd, s_)
                        if dd <= -tgt: hi = s_; break
                        lo = s_
                    if hi is None:   # a thin twig on a thinner parent: the best reachable point, never worse than where it was
                        v.co = v0.lerp(Q, best[1])
                        if best[1] > 0: moved = True
                        continue
                    for _ in range(8):
                        mid = (lo + hi) / 2; v.co = v0.lerp(Q, mid)
                        if T.usd(t, v.co) <= -tgt: hi = mid
                        else: lo = mid
                    v.co = v0.lerp(Q, hi); moved = True
                c2 = _centroid(ring0); a0 = t["apex"].co.copy()   # 2. apex depth clamped: slide toward the (new) ring centre
                def ok(s_):
                    a = a0.lerp(c2, s_)
                    if T.usd(t, a) > -tgt: return False
                    return all(T.usd(t, q) <= eok for q in [v.co.lerp(a, f) for v in ring0 for f in (0.5, 0.8)] + _face_pts([v.co.copy() for v in ring0], a))
                if not ok(0.0):
                    hi = None
                    for i in range(1, 21):
                        if ok(i / 20): hi = i / 20; break
                    if hi is None: t["apex"].co = a0.lerp(c2, 1.0); moved = True
                    else:
                        lo = max(0.0, hi - 0.05)
                        for _ in range(6):
                            mid = (lo + hi) / 2
                            if ok(mid): hi = mid
                            else: lo = mid
                        t["apex"].co = a0.lerp(c2, hi); moved = True
            if par is not None and max(d for _, d in [(kk, T.usd(t, q)) for kk, q in _samples(t)]) > tol and (t["apex"].co - _centroid(ring0)).length > tol:
                t["apex"].co = _centroid(ring0); unfixed += 1; moved = True   # cannot hide in the parent: closed flush instead
            if moved: clamped += 1; T.refresh_box(t)
            ap = t["apex"].co; c = _centroid(ring0); depth = (ap - c).length
            res = [(kind, T.usd(t, q)) for kind, q in _samples(t)]; worst = max(d for _, d in res)
        if worst > tol and depth > tol:
            exp = 0.0
            for f in t["tri"]:
                a, b, cc = [v.co for v in f.verts]
                sm = [a + (b - a) * (i + 0.33) / 4 + (cc - a) * (j + 0.33) / 4 for i in range(4) for j in range(4 - i)]
                exp += f.calc_area() * sum(1 for q in sm if T.usd(t, q) > 0.001 * k) / len(sm)
            flagged.append(dict(child=t["id"], parent=p["id"] if p else None, flush=par is None,
                                parent_axis_pt=[round(x, 4) for x in Q], base=[round(x, 4) for x in c], apex=[round(x, 4) for x in t["apex"].co],
                                r0=round(r0, 4), parent_local_r=round(par[3], 4) if par else 0.0,
                                apex_out_mm=round(res[0][1] * 1000 / k, 1),
                                ring_out_mm=round(max(d for kk, d in res if kk == "ring") * 1000 / k, 1),
                                edge_out_mm=round(max(d for kk, d in res if kk == "edge") * 1000 / k, 1),
                                face_out_mm=round(max(d for kk, d in res if kk == "face") * 1000 / k, 1),
                                worst_mm=round(worst * 1000 / k, 1), exposed_cm2=round(exp * 1e4 / (k * k), 1),
                                cone_faces=sorted(f.index for f in t["tri"])))
    return dict(tubes=len(T.tubes), roots=roots, children=children, orphans=flush, flush=flush, bad=T.bad,
                flagged=flagged, clamped=clamped, unfixed=unfixed)


def settle(bm, k=1.0 / SHIP_SCALE, passes=6):
    """scan(fix=True) until a pass moves nothing (a later child's move can uncover an earlier one); returns
    (cones moved in total, last report)."""
    total = 0
    for _ in range(passes):
        r = scan(bm, fix=True, k=k); total += r["clamped"]
        if not r["clamped"]: break
    return total, r


def clamp(bm, k=1.0 / SHIP_SCALE):
    """Builder hook: pull every offending base cone inside its parent tube (or close it flush); returns the number of
    cone moves (0 = mesh untouched). k converts the shipped-scale tolerances to the builder's mesh units."""
    return settle(bm, k)[0]

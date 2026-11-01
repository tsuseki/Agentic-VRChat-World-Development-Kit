"""Bark self-intersection check on a meshed tree (kit module; bpy-free, needs mathutils + bmesh meshes only).

Every bark tube (a merge chain: stem, limb, twig, K3 pillar or aerial root) is its own closed component with a cone at
each end (`base_cones._Tubes`). Two tubes may only overlap where the tree really joins them:
  * socket: a tube end buried in another tube (its host: a limb's base in its parent, a K3 pillar's top in its limb).
    Host = among the tubes whose axis passes within 1.3 x their local radius of the end's ring centre and that are
    wider there than the end's ring, a stem / trunk under a limb first, else the widest; pillars (ground tubes thinner
    than 0.5 x the thickest ground tube) never host. Overlap of the pair is allowed within the socket zone, the arc
    length the tube needs to leave its host at its own angle: Z = (R_host + r) / max(sin(angle to the host axis), 0.35)
    + 0.05 m (declip's fork zone), from where the tube's axis passes nearest the host's axis (within 2 R_host of the
    end: a whorl limb's base cone runs on through the trunk centre to its apex on the far side);
  * crotch: two siblings in one host, each within its own socket zone (the fork itself);
  * buried: a point inside a tube that hosts either tube of the pair (siblings crossing inside their parent);
  * root plate: two ground tubes (an end below the ground) below `plate` m (the flare: fused stems share one foot);
  * fused pillar group: K3 pillars hung side by side from one limb (both tops in the same host within `fuse_gap` x
    the host radius of each other), the designed fused pairs / triples.
Anything else is a CLASH: surface samples of one tube (a 3 x 3 grid per face, corners included) lying inside another
tube (signed distance by nearest surface + ray parity on both quad splits, as base_cones). Its depth = the deepest such
sample. A POKE is the reverse failure at a socket: a tube that leaves its host on one side but shows on the far side of
the host's axis (a hanging pillar whose top comes out through the top of its limb), outside every other tube.
`scan(bm, k=1.0, plate=0.35)` -> dict(tubes, clashes=[...], pokes=[...], fused=[...], plate_top=z) in shipped metres
(k = mesh units per shipped metre: 1 on a packed mesh, 1 / 0.7 on the builder's mesh). Pairs whose deepest sample is
under TOL are not reported.
`silhouettes(bm, k, plate, views, az=True)` -> per view: stems / big limbs crossing each other ON SCREEN near the fork
and stem tops clear / hidden / partial (a clean mesh can still read as one trunk through another: the user judges the
picture). 8 eye-height azimuths by default plus any set camera (a vignette); positive control: the BanyanGrove of
BoothAssets 87c9724a, 0 clashes in 3D but an X from the vignette 05 camera (2 crossings there).
"""
import math
from mathutils import Vector
from base_cones import _Tubes, _centroid

TOL = 0.01        # m shipped: interpenetration below this is a touching seam, not a clash
POKE_TOL = 0.01   # m shipped: a socket end may stand this far out of its host on the far side
FUSE_GAP = 3.0    # x host radius: pillar tops this close in the same host form one fused group
GRID = 3


def _polyline(t):
    """axis of a tube from its base apex to its tip apex: points, radii, cumulative arc length"""
    P = [t["apex"].co.copy()] + [c for c, _ in t["axis"]] + [t["alt"][0].co.copy()]
    R = [0.0] + [r for _, r in t["axis"]] + [0.0]
    S = [0.0]
    for a, b in zip(P, P[1:]): S.append(S[-1] + (b - a).length)
    return P, R, S


def _near(P, R, S, q):
    """(distance to axis, radius there, arc length there, axis point, tangent)"""
    best = None
    for i in range(len(P) - 1):
        a, e = P[i], P[i + 1] - P[i]; ll = e.length_squared
        s = 0.0 if ll < 1e-12 else max(0.0, min(1.0, (q - a).dot(e) / ll))
        X = a + e * s; d = (q - X).length
        if best is None or d < best[0]:
            best = (d, R[i] + (R[i + 1] - R[i]) * s, S[i] + (S[i + 1] - S[i]) * s, X,
                    e.normalized() if ll > 1e-12 else Vector((0, 0, 1)))
    return best


def _grid(f, n=GRID):
    v = [x.co for x in f.verts]
    if len(v) == 4:
        return [(v[0].lerp(v[1], i / n)).lerp(v[3].lerp(v[2], i / n), j / n) for i in range(n + 1) for j in range(n + 1)]
    return [v[0] * (1 - i / n - j / n) + v[1] * (i / n) + v[2] * (j / n) for i in range(n + 1) for j in range(n + 1 - i)]


class _Check:
    def __init__(self, bm, k):
        self.T = _Tubes(bm); self.k = k; self.tubes = self.T.tubes
        for t in self.tubes:
            t["P"], t["R"], t["S"] = _polyline(t); t["L"] = t["S"][-1]; t["rmax"] = max(t["R"])
            t["ground"] = min(t["P"][0].z, t["P"][-1].z) < -0.01 * k
            t["RP"] = [c for c, _ in t["axis"]]; t["RR"] = [r for _, r in t["axis"]]   # ring axis (no apex ends)
            t["RS"] = [0.0]
            for a, b in zip(t["RP"], t["RP"][1:]): t["RS"].append(t["RS"][-1] + (b - a).length)
        gr = [max(t["RR"]) for t in self.tubes if t["ground"]]
        self.stem_r = 0.5 * max(gr) if gr else 1e9   # ground tubes at least half the thickest one are stems, the rest pillars
        self._hosts(k)

    def _hung(self, h):
        return h["ground"] and max(h["RR"]) < self.stem_r

    def _hosts(self, k):
        self.hosts = {}   # (tube id, end 0|1) -> (host tube, zone length, leave direction)
        for t in self.tubes:
            for end in (0, 1):
                E = t["P"][0] if end == 0 else t["P"][-1]
                if E.z < -0.01 * k: continue
                # host (base_cones' parent rule, widened): among the tubes whose ring axis passes within 1.3 of their
                # local radii (inside or touching) and that are wider there than this end's ring (or are a trunk under
                # a limb), the WIDEST: a limb's base in its trunk (not in an unequal sibling that starts beside it),
                # a pillar top in its limb (pillars host nothing: not in a fused neighbour's collar), a narrow trunk
                # top in its widest limb
                rr0 = t["R"][1] if end == 0 else t["R"][-2]; best = None
                for h in self.tubes:
                    if h is t or self._hung(h) or self.T._bbdist(h, E) > 1.3 * h["rmax"]: continue
                    if len(h["RP"]) < 2: continue
                    d, rh = _near(h["RP"], h["RR"], h["RS"], E)[:2]
                    trunk = h["ground"] and not t["ground"]   # a limb on a trunk: the trunk first, then the widest
                    if (rh > rr0 * 1.01 or trunk) and d <= 1.3 * rh and (best is None or (trunk, rh) > best[2]):
                        best = (h, rh, (trunk, rh))
                if best is None: continue
                h, Rh = best[0], best[1]
                s_in = min(t["L"], 0.25 * t["L"] + 0.5 * k)   # the tube's direction as it leaves the host
                Q = self._at(t, s_in if end == 0 else t["L"] - s_in)
                lv = (Q - E); lv = lv.normalized() if lv.length > 1e-9 else Vector((0, 0, -1))
                _, _, _, _, tan = _near(h["P"], h["R"], h["S"], E)
                sn = lv.cross(tan).length
                rr = t["R"][1] if end == 0 else t["R"][-2]
                # from where the tube's axis passes the host's axis (a whorl limb's base cone runs on through the
                # trunk centre to its apex on the far side: the socket starts at the centre, not at that apex)
                s0, dmin = 0.0, None
                for i in range(len(t["P"])):
                    s = t["S"][i] if end == 0 else t["L"] - t["S"][i]
                    if s > 2.0 * Rh: continue
                    dd = _near(h["RP"], h["RR"], h["RS"], t["P"][i])[0]
                    if dmin is None or dd < dmin: s0, dmin = s, dd
                zone = s0 + (Rh + rr) / max(sn, 0.35) + 0.05 * k
                self.hosts[(t["id"], end)] = (h, zone, lv, E)

    def _at(self, t, s):
        P, S = t["P"], t["S"]
        for i in range(len(P) - 1):
            if S[i + 1] >= s: return P[i].lerp(P[i + 1], (s - S[i]) / max(S[i + 1] - S[i], 1e-9))
        return P[-1].copy()

    def inside(self, h, q):
        """signed distance to tube h, cheap reject first (a point inside is at most rmax from the surface)"""
        if self.T._bbdist(h, q) > 0: return 1.0
        r = self.T.bvh(h)[0].find_nearest(q, h["rmax"] * 1.05 + 1e-4)
        if r[0] is None: return 1.0
        return self.T.sd(h, q)

    def _zone_hit(self, a, end, q):
        H = self.hosts.get((a["id"], end))
        if not H: return None
        s = _near(a["P"], a["R"], a["S"], q)[2]
        return H[0] if (s if end == 0 else a["L"] - s) <= H[1] else None

    def in_socket(self, t, h, q):
        """q (on t or h) inside the socket zone of an end of t hosted by h, or of an end of h hosted by t; or in the
        crotch of two siblings: both within their socket zones of ends hosted by one tube"""
        ht = [self._zone_hit(t, e, q) for e in (0, 1)]; hh = [self._zone_hit(h, e, q) for e in (0, 1)]
        if any(x is h for x in ht) or any(x is t for x in hh): return True
        return any(x is not None and any(x is y for y in hh) for x in ht)

    def buried(self, t, h, q):
        for x in (t, h):
            for end in (0, 1):
                H = self.hosts.get((x["id"], end))
                if H and H[0] is not t and H[0] is not h and self.inside(H[0], q) < 0: return True
        return False

    def fused(self, t, h):
        for et in (0, 1):
            A = self.hosts.get((t["id"], et))
            if not A: continue
            for eh in (0, 1):
                B = self.hosts.get((h["id"], eh))
                if B and B[0] is A[0] and t["ground"] and h["ground"]:
                    if (A[3] - B[3]).length <= FUSE_GAP * _near(A[0]["P"], A[0]["R"], A[0]["S"], A[3])[1] + 1e-6: return True
        return False


def _label(t, C):
    ends = [C.hosts.get((t["id"], e)) for e in (0, 1)]
    kind = ("pillar" if C._hung(t) else "stem") if t["ground"] else "limb"
    host = next((H[0]["id"] for H in ends if H), None)
    return dict(id=t["id"], kind=kind, host=host, r=round(t["R"][1] / C.k, 3),
                base=[round(x / C.k, 2) for x in t["P"][0]], tip=[round(x / C.k, 2) for x in t["P"][-1]])


def scan(bm, k=1.0, plate=0.35):
    C = _Check(bm, k); tol = TOL * k; pairs = {}; fused = {}; plate_top = 0.0
    for t in C.tubes:
        pts = [q for f in t["faces"] for q in _grid(f)]
        for h in C.tubes:
            if h is t: continue
            if any(t["hi"][i] < h["lo"][i] or h["hi"][i] < t["lo"][i] for i in range(3)): continue
            fz = C.fused(t, h)
            for q in pts:
                d = C.inside(h, q)
                if d >= -tol: continue
                if t["ground"] and h["ground"] and q.z < plate * k:
                    plate_top = max(plate_top, q.z); continue
                if C.in_socket(t, h, q) or C.buried(t, h, q): continue
                if t["ground"] and h["ground"]: plate_top = max(plate_top, q.z) if q.z < 1.5 * plate * k else plate_top
                key = (min(t["id"], h["id"]), max(t["id"], h["id"]))
                tgt = fused if fz else pairs
                e = tgt.setdefault(key, dict(depth=0.0, n=0, at=None, zmin=1e9, zmax=-1e9))
                e["n"] += 1; e["zmin"] = min(e["zmin"], q.z); e["zmax"] = max(e["zmax"], q.z)
                if -d > e["depth"]: e["depth"] = -d; e["at"] = q.copy()
    pokes = []
    for (tid, end), (h, zone, lv, E) in C.hosts.items():
        t = C.tubes[tid]; worst = (0.0, None)
        for f in t["faces"]:
            for q in _grid(f, 2):
                s = _near(t["P"], t["R"], t["S"], q)[2]
                if (s if end == 0 else t["L"] - s) > zone: continue
                _, _, _, X, _ = _near(h["P"], h["R"], h["S"], q)
                if (q - X).dot(lv) >= 0: continue          # the side the tube leaves on: the socket seam
                d = C.T.usd(t, q)                           # outside every other tube = visible
                if d > worst[0]: worst = (d, q.copy())
        if worst[0] > POKE_TOL * k:
            pokes.append(dict(tube=_label(t, C), host=_label(h, C), end=end, out_cm=round(worst[0] * 100 / k, 1),
                              at=[round(x / k, 2) for x in worst[1]]))
    rows = []
    for (a, b), e in sorted(pairs.items(), key=lambda kv: -kv[1]["depth"]):
        A, B = C.tubes[a], C.tubes[b]
        rows.append(dict(a=_label(A, C), b=_label(B, C), depth_cm=round(e["depth"] * 100 / k, 1), samples=e["n"],
                         z=[round(e["zmin"] / k, 2), round(e["zmax"] / k, 2)], at=[round(x / k, 2) for x in e["at"]]))
    fz = [dict(a=a, b=b, depth_cm=round(e["depth"] * 100 / k, 1), z=[round(e["zmin"] / k, 2), round(e["zmax"] / k, 2)])
          for (a, b), e in fused.items()]
    return dict(tubes=len(C.tubes), clashes=rows, pokes=pokes, fused=fz, plate_top=round(plate_top / k, 2),
                hosts={f"{t}:{e}": H[0]["id"] for (t, e), H in C.hosts.items()})


# ---- silhouette crossings (screen space): two trunks crossing in a picture read as one through the other, whatever
# the depth gap between them (user on a BanyanGrove vignette whose stems were 0.1 m+ apart in 3D but formed an X)
SIL_ABOVE = 3.0    # m shipped: stem axes may not cross from the root plate to this far (arc) past each stem's fork
SIL_NEAR = 2.0     # m shipped: a big limb may not cross another stem's axis where it passes within this of it (3D)
SIL_RATIO = 0.55   # a limb is big when its base radius > this x its stem's radius at its socket (Main: 0.6 x the stem;
#                    the socket rings sit on the swollen stem top, which reads 5-10 % wide: whorl limbs 0.7 x by design)
SIL_HIDE = 0.25    # tops count as hidden behind each other when their centres are within this x (ra + rb) on screen


def _root_stem(C, t):
    x = t
    for _ in range(40):
        if x["ground"]: return x if not C._hung(x) else None
        H = C.hosts.get((x["id"], 0))
        if not H: return None
        x = H[0]
    return None


def _seg_x(a0, a1, b0, b1):
    """2D segment intersection -> (ta, tb) or None"""
    d1 = (a1[0] - a0[0], a1[1] - a0[1]); d2 = (b1[0] - b0[0], b1[1] - b0[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-12: return None
    w = (b0[0] - a0[0], b0[1] - a0[1])
    ta = (w[0] * d2[1] - w[1] * d2[0]) / den; tb = (w[0] * d1[1] - w[1] * d1[0]) / den
    return (ta, tb) if 0.0 <= ta <= 1.0 and 0.0 <= tb <= 1.0 else None


def silhouettes(bm, k=1.0, plate=0.35, views=(), az=True, dist=10.0, eye=1.3, above=SIL_ABOVE, near=SIL_NEAR,
                ratio=SIL_RATIO, hide=SIL_HIDE):
    """Screen-space crossings of the trunk structure, per view. Stems = ground tubes that are not pillars; each stem's
    fork = the socket of its thickest limb on the stem body; big limbs: base radius > ratio x the stem there; a stem
    merged into a top limb runs on past its fork as one tube. Per view (perspective, from `loc` looking along `fwd`):
      stem crossing  : the axes of two stems cross on screen between the root plate and `above` m (arc) past each fork;
      limb crossing  : a big limb (or a stem's run beyond fork + above) crosses another stem's axis (that same span) on
                       screen at a point where the two lie within `near` m of each other in 3D;
      tops           : per stem pair, the fork centres on screen: clear (silhouette gap >= one diameter, ra + rb),
                       hidden (centres within hide x (ra + rb): one trunk behind the other) or partial (between).
    views: extra [dict(name, loc, fwd[, fov, aspect])] in shipped m (fov: vertical deg; set = only what is in a frame
    counts); az=True adds 8 azimuths first (0, 45, ... 315; az 0 looks along +y) at `dist` m, eye `eye` m, aimed at the
    mean fork height."""
    C = _Check(bm, k); UPV = Vector((0, 0, 1))
    stems = [t for t in C.tubes if t["ground"] and not C._hung(t)]
    fork, big, thick = {}, [], {}
    def body_r(A):  # the stem's own girth: its ring radius nearest 1.5 m up (above the flare)
        return min(zip(A["RP"], A["RR"]), key=lambda pr: abs(pr[0].z - 1.5 * k))[1]
    for t in C.tubes:
        if t["ground"]: continue
        H = C.hosts.get((t["id"], 0)); A = _root_stem(C, t)
        if not H or A is None or H[0] is not A: continue
        d, rh, s = _near(A["RP"], A["RR"], A["RS"], H[3])[:3]
        if rh < 0.5 * body_r(A): continue  # on the stem itself, not on its thin merged run
        if t["R"][1] > ratio * rh: big.append((t, A))
        if t["R"][1] > thick.get(A["id"], (0.0, 0.0))[0]: thick[A["id"]] = (t["R"][1], s)   # the fork: thickest limb
    fork = {a: s for a, (_, s) in thick.items()}
    span, runs = {}, {}
    for A in stems:
        sf = fork.get(A["id"], A["RS"][-1]); fork[A["id"]] = sf
        span[A["id"]] = [i for i in range(len(A["RP"])) if A["RP"][i].z >= plate * k and A["RS"][i] <= sf + above * k]
        runs[A["id"]] = [i for i in range(len(A["RP"])) if A["RS"][i] > sf + above * k]
    def fpt(A):
        sf = fork[A["id"]]; RP, RR, RS = A["RP"], A["RR"], A["RS"]
        for i in range(len(RP) - 1):
            if RS[i + 1] >= sf:
                u = (sf - RS[i]) / max(RS[i + 1] - RS[i], 1e-9); return RP[i].lerp(RP[i + 1], u), RR[i] + (RR[i + 1] - RR[i]) * u
        return RP[-1], RR[-1]
    tops = {A["id"]: fpt(A) for A in stems}
    fz = sum(p.z for p, _ in tops.values()) / max(len(tops), 1) / k; vv = []
    for a in (range(0, 360, 45) if az else ()):
        r = math.radians(a); loc = Vector((math.sin(r) * dist, -math.cos(r) * dist, eye))
        vv.append(dict(name=f"az{a:03d}", loc=loc, fwd=Vector((0, 0, fz)) - loc))
    views = vv + list(views)
    lines = [(A, [A["RP"][i] for i in span[A["id"]]]) for A in stems]
    others = [(t, A, t["RP"]) for t, A in big] + [(A, A, [A["RP"][i] for i in runs[A["id"]]]) for A in stems]
    out = []
    for V in views:
        L = Vector(V["loc"]) * k; f = Vector(V["fwd"]).normalized()
        rt = f.cross(UPV); rt = rt.normalized() if rt.length > 1e-6 else Vector((1, 0, 0)); up = rt.cross(f)
        lim = (math.tan(math.radians(V["fov"]) / 2) * V.get("aspect", 16 / 9), math.tan(math.radians(V["fov"]) / 2)) if V.get("fov") else None
        def pj(q):
            v = q - L; z = v.dot(f)
            return None if z < 0.05 * k else (v.dot(rt) / z, v.dot(up) / z, z)
        def inframe(p): return lim is None or (abs(p[0]) <= lim[0] and abs(p[1]) <= lim[1])
        def cross(PA, PB, test):
            hits = []
            QA = [pj(q) for q in PA]; QB = [pj(q) for q in PB]
            for i in range(len(PA) - 1):
                if QA[i] is None or QA[i + 1] is None: continue
                for j in range(len(PB) - 1):
                    if QB[j] is None or QB[j + 1] is None: continue
                    x = _seg_x(QA[i], QA[i + 1], QB[j], QB[j + 1])
                    if not x: continue
                    pa = PA[i].lerp(PA[i + 1], x[0]); pb = PB[j].lerp(PB[j + 1], x[1])
                    sp = (QA[i][0] + (QA[i + 1][0] - QA[i][0]) * x[0], QA[i][1] + (QA[i + 1][1] - QA[i][1]) * x[0])
                    if inframe(sp) and test(pa, pb): hits.append((pa, pb))
            return hits
        rec = dict(view=V["name"], crossings=[], tops=[])
        for ia, (A, PA) in enumerate(lines):
            for B, PB in lines[ia + 1:]:
                h = cross(PA, PB, lambda pa, pb: True)
                if h:
                    pf = lambda S, q: round((_near(S["RP"], S["RR"], S["RS"], q)[2] - fork[S["id"]]) / k, 2)
                    rec["crossings"].append(dict(kind="stem", a=A["id"], b=B["id"], n=len(h), at=[round(x / k, 2) for x in h[0][0]],
                                                 gap_m=round((h[0][0] - h[0][1]).length / k, 2),
                                                 past_fork_m=[pf(A, h[0][0]), pf(B, h[0][1])]))
                (ca, ra), (cb, rb) = tops[A["id"]], tops[B["id"]]
                qa, qb = pj(ca), pj(cb)
                if qa is None or qb is None or not (inframe(qa) or inframe(qb)): continue
                sa, sb = ra / qa[2], rb / qb[2]; dc = math.hypot(qa[0] - qb[0], qa[1] - qb[1]); D = sa + sb
                cls = "clear" if dc - D >= D else "hidden" if dc <= hide * D else "partial"
                rec["tops"].append(dict(a=A["id"], b=B["id"], cls=cls, gap_diam=round((dc - D) / D, 2)))
        for t, A, PT in others:
            for B, PB in lines:
                if B is A or len(PT) < 2: continue
                h = cross(PT, PB, lambda pa, pb: (pa - pb).length <= near * k)
                if h: rec["crossings"].append(dict(kind="limb", a=t["id"], stem_of_a=A["id"], b=B["id"], n=len(h),
                                                   at=[round(x / k, 2) for x in h[0][0]], gap_m=round((h[0][0] - h[0][1]).length / k, 2)))
        rec["n_cross"] = len(rec["crossings"]); rec["n_partial"] = sum(1 for x in rec["tops"] if x["cls"] == "partial")
        out.append(rec)
    return dict(stems=[A["id"] for A in stems], big=[t["id"] for t, _ in big],
                forks={A["id"]: round(tops[A["id"]][0].z / k, 2) for A in stems}, views=out,
                n_cross=sum(r["n_cross"] for r in out), n_partial=sum(r["n_partial"] for r in out))

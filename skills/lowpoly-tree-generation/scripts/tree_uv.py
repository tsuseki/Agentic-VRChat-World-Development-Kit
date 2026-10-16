"""Uniform-texel-density cylindrical UVs for tree bark (material index 0).

Every branch is a tube built ring by ring (tube() in tree_family_build.py): its quads
are created row by row, `sides` quads per row, with loop order (r0[s], r0[s+1], r1[s+1], r1[s]).
That order survives to_mesh, modifier apply and .blend save, so the rings can be recovered from any
built mesh without extra metadata. Each tube is unwrapped as a cylinder:
  V = accumulated arc length along the branch centreline / TILE   (never normalised per segment)
  U = s/sides * ring circumference / TILE                         (same metres-per-repeat as V)
Rings on trunks wide enough get an integer number of wraps so the seam closes exactly; thinner rings
keep the true fractional wrap so twig texels are not squashed (their seam is a sub-centimetre strip).
TILE metres = one texture repeat; the bark material uses tiling 1.
"""
import statistics
from mathutils import Vector

TILE = 0.6
INTEGER_WRAP_MIN = 0.75  # rings with circumference >= 0.75 * TILE snap to whole wraps
# Optional (set by the builder from CFG): the repeat grows with the tube's base radius, TILE at TILE_R and
# above, down to TILE_MIN on twigs, so big trunks do not show a fine grid; OFFSET_SEED gives every tube a
# random UV offset so neighbouring limbs never line up the same bark features.
TILE_MIN = None
TILE_R = 1.0
OFFSET_SEED = None
FACE_TILE = {}  # (mesh name, polygon index) -> repeat used, so stretch_stats measures distortion, not the chosen scale


def tubes(me):
    """Yield bark tubes as lists of rings (lists of vertex indices) recovered from face order."""
    polys = [p for p in me.polygons if p.material_index == 0 and len(p.vertices) == 4]
    i, tube, prev_top = 0, [], None
    while i < len(polys):
        p = polys[i]
        v = p.vertices
        sides = v[3] - v[0]
        row = polys[i:i + sides]
        r0 = [q.vertices[0] for q in row]
        r1 = [q.vertices[3] for q in row]
        if prev_top is not None and r0 != prev_top:
            yield tube, rowsets
            tube = []
        if not tube:
            tube, rowsets = [r0], []
        tube.append(r1); rowsets.append(row)
        prev_top = r1
        i += sides
    if tube:
        yield tube, rowsets


def cylinder_uvs(ob, layer="UVMap"):
    me = ob.data
    uv = me.uv_layers[layer].data
    co = [v.co for v in me.vertices]
    end_ring = {}  # end-ring vertex -> (s, sides, wraps, v, centre) for the cone caps
    start_ring = {}  # base-ring vertex -> same, for the cones closing a limb's base inside its parent
    import random
    rng = random.Random(OFFSET_SEED)
    for rings, rows in tubes(me):
        sides = len(rings[0])
        centres = [sum((co[k] for k in r), Vector()) / sides for r in rings]
        tile = TILE
        if TILE_MIN is not None:
            rad = sum((co[k] - centres[0]).length for k in rings[0]) / sides
            tile = max(TILE_MIN, min(TILE, TILE * rad / TILE_R))
        ou, ov = (rng.random(), rng.random()) if OFFSET_SEED is not None else (0.0, 0.0)
        acc = [0.0]
        for a, b in zip(centres, centres[1:]):
            acc.append(acc[-1] + (b - a).length)
        wraps = []
        for r in rings:
            circ = sum((co[r[(s + 1) % sides]] - co[r[s]]).length for s in range(sides))
            w = circ / tile
            wraps.append(max(1, round(w)) if circ >= INTEGER_WRAP_MIN * tile else w)
        for ri, row in enumerate(rows):
            for s, p in enumerate(row):
                FACE_TILE[(me.name, p.index)] = tile
                l0, l1, l2, l3 = p.loop_indices
                uv[l0].uv = (ou + s / sides * wraps[ri], ov + acc[ri] / tile)
                uv[l1].uv = (ou + (s + 1) / sides * wraps[ri], ov + acc[ri] / tile)
                uv[l2].uv = (ou + (s + 1) / sides * wraps[ri + 1], ov + acc[ri + 1] / tile)
                uv[l3].uv = (ou + s / sides * wraps[ri + 1], ov + acc[ri + 1] / tile)
        for s, k in enumerate(rings[-1]):
            end_ring[k] = (s, sides, wraps[-1], acc[-1], centres[-1], tile, ou, ov)
        for s, k in enumerate(rings[0]):
            start_ring[k] = (s, sides, wraps[0], 0.0, centres[0], tile, ou, ov)
    # cone caps: triangles (ring[s], ring[s+1], apex), continuing the tube's cylinder mapping
    for p in me.polygons:
        if p.material_index != 0 or len(p.vertices) != 3: continue
        a, b, apex = p.vertices
        if a in start_ring and b in start_ring and a not in end_ring:  # base cone (ring[s+1], ring[s], apex)
            s, sides, w, v, c, t, ou, ov = start_ring[b]
            la, lb, lc = p.loop_indices
            uv[la].uv = (ou + (s + 1) / sides * w, ov)
            uv[lb].uv = (ou + s / sides * w, ov)
            uv[lc].uv = (ou + (s + 0.5) / sides * w, ov - (co[apex] - c).length / t)
            FACE_TILE[(me.name, p.index)] = t
            continue
        if a not in end_ring: continue
        s, sides, w, v, c, t, ou, ov = end_ring[a]
        la, lb, lc = p.loop_indices
        uv[la].uv = (ou + s / sides * w, ov + v / t)
        uv[lb].uv = (ou + (s + 1) / sides * w, ov + v / t)
        uv[lc].uv = (ou + (s + 0.5) / sides * w, ov + (v + (co[apex] - c).length) / t)
        FACE_TILE[(me.name, p.index)] = t


def stretch_stats(ob, layer="UVMap", drop_small=0.05):
    """min/median/max of UV area / 3D area over bark faces, ignoring the smallest `drop_small` by area.
    Faces mapped with a radius-scaled repeat are normalised to TILE (distortion only, not the intended scale)."""
    me = ob.data
    uv = me.uv_layers[layer].data
    rows = []
    for p in me.polygons:
        if p.material_index != 0 or p.area <= 0:
            continue
        pts = [uv[l].uv for l in p.loop_indices]
        a = 0.0
        for k in range(len(pts)):
            x0, y0 = pts[k]; x1, y1 = pts[(k + 1) % len(pts)]
            a += x0 * y1 - x1 * y0
        t = FACE_TILE.get((me.name, p.index), TILE)
        rows.append((p.area, abs(a) / 2 / p.area * (t / TILE) ** 2))
    rows.sort()
    keep = [r for _, r in rows[int(len(rows) * drop_small):]]
    return round(min(keep), 3), round(statistics.median(keep), 3), round(max(keep), 3), round(max(keep) / max(min(keep), 1e-9), 2)

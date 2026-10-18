# Headless low-poly tree builder: skeleton -> tube bark -> leaf cards -> UVs -> crown normals -> FBX.
#   blender -b --factory-startup -P tree_family_build.py -- <Species> --tex <dir> --out <dir>
#           [--blend <dir>] [--lod1] [--qa <png>] [--config <species.py>]
# <Species> is a key of CFG below (or of a dict CFG in --config). Textures are read from --tex:
#   <tex>_Bark_Albedo.png, <tex>_Bark_Normal.png, <tex>_Leaves_RGBA.png (+ <tex>_Leaves_Cards.json for
#   crown mode "sprig", written by branch_atlas.py). Writes <out>/<Species>_Tree.fbx (mesh <Species>_Tree)
#   and <blend>/<Species>_Tree.blend. --lod1 also builds <Species>_Tree_LOD1 (only for very large worlds).
# Skeleton noise is deterministic: same Species + seed rebuilds the identical mesh.
# Optional CFG keys (all off by default; see SKILL.md "Big trees"):
#   clear=[dict(poly=[(x,y)...], z=(z0,z1), margin=m) | dict(seg=((x,y,z),(x,y,z)), r=m)]  keep-out volumes
#       (deck prisms, walkway capsules): branches stop clear_pad m (default 0) before entering one, cards are
#       rerouted, then shrunk, then skipped (a skipped tip card shows as tips_uncovered); a placed card's real surface
#       (5 x 5 samples) is checked last and the card dropped if any of it reaches into a volume (not screen cards:
#       a screen is placed on purpose, e.g. beside a never-walked bridge it must hide)
#   buttress=dict(n, z=(lo,hi), reach=(lo,hi), r)   flaring roots from the lower trunk down to z=0
#   side=[dict(n, z=(lo,hi), len, ang, r, tip, gnarl, up)]  extra trunk limbs/stubs at given heights (no children)
#   vines=dict(count, size, z=(lo,hi))   hanging sprig cards under depth>=1 branches (epiphytes / draped foliage)
#   lod1_cards (0.6), lod1_size (1.35)   LOD1 card count and size factors
#   lod1_subset=dict(keep=1.0, grow=1.0)   LOD1 = LOD0 thinned in place instead of rebuilt: same skeleton and card
#       draws, every other tube ring, lod1_sides, all tip cards plus a `keep` share of the rest, `grow` x larger and
#       unfolded. keep=1, grow=1 (bark-only LOD1) keeps the silhouette within a few cm; thinning cards opens holes.
#   bark_tile (0.6)   metres per bark texture repeat (use the scan's real width, e.g. 1.8 for Poly Haven barks)
#   bark_tile_min, bark_tile_r   repeat scaled by tube radius (bark_tile at >= bark_tile_r, down to bark_tile_min);
#       every tube also gets a random UV offset (seeded) so neighbouring limbs never repeat the same features
#   sides (7,5,4) / lod1_sides (5,4,3)   tube sides for trunk / inner levels / deepest level
#   smooth=dict(bend=12, depth=1, iters=2)   round the skeleton: corner-cut every bend sharper than `bend` deg on
#       branches of depth <= `depth` (iters passes, 1/4 cuts; ends kept). Adds rings only where limbs kink, so
#       gnarled olives read as curved wood instead of jointed sticks. Off by default (keeps old trees identical).
#   merge=dict(at=0.7, ang=50, blend=2, round=1, round_bend=20, depth=(0, 99), straighten=True)   sympodial joints:
#       a limb whose last fork is past `at` of its length continues into its best-aligned child as one tube (no
#       spike past the fork); see merge_continuations(). Recommended for every new tree.
#   lod1_mindepth   LOD1 drops the deepest level and roots its cards on this depth
#   clear_drop (0)   drop a branch the keep-out volumes cut to less than this share of its length
#   limbs=[dict(root, tip, r=(r0, r1), gnarl, children, arch, epiphytes)]   explicit limbs (tree-local, root on the
#       trunk at root.z; arch m upward bow; epiphytes = hanging cards along it)
#       that ignore the keep-out volumes and keep their end radius (e.g. a limb carrying a hanging pod)
#   screens=[dict(centre, size=(w, h, d), facing (deg, local), count, card, twigs, r)]   a dense foliage mass hung
#       from two short limbs over the box (hanging twigs packed with cards), LOD0 only
#   fork=dict(n, ang, len, r, tip, gnarl, up)   decurrent crown: a leader continues the trunk, n-1 major limbs leave
#       over its top 3-10 %
#       (they get the next levels' children; the trunk is not tapered to a tip)
#   side=[dict(..., grow=True)]   trunk limbs at absolute heights that get the next levels' children (real branches)
#   crown per_tip (k), tip_from (0.55)   k cards on the outer part of every leaf-bearing branch: dense clusters with
#       gaps between them (count is then the result, not a target)
#   lianas=dict(n, z=(lo, hi), r=(lo, hi), twist, segs)   thin vine stems climbing the trunk from the waterline
#   leaf_cluster (None) m, leaf_crown_mix (0.35)   per-clump leaf normals (tree_normals cluster mode) instead
#       of one crown dome; use with matte foliage so crowns do not shade as one bubble with a bright rim
#   bark_tex (= tex)   bark texture set name when several leaf sets share one bark
#   bark_macro=dict(scale, amount)   low-frequency value variation baked into the vertex colour of the bark
#       (multiply in the bark shader; leaves get white); breaks the tiling over big trunks
#   levels[i] segs (4 on the first level, else 3): segments per limb (fewer = cheaper bark on many-limbed conifers)
#   conifers: levels[i] whorl=k (k limbs per height, evenly around the parent), ang_end=(lo, hi) (angle range at
#       at[1]; `ang` holds at at[0]: drooping low limbs, rising top ones), up_end (up bias ramps from `up` to it
#       along each limb: drooping tips); crown size_top (card size x this at `height`, spire), ground (m, hanging
#       cards shrink/skip to stay above it); proxy="cone"
#   bend (0.0)   upward pull per stem segment (a leaning palm trunk curving up), stem_segs (6) segments per stem
#   crown mode "rosette" (palms, tree ferns, bananas): fronds radiating from every stem top; see rosette_crown()
#       and SKILL.md. levels=[] allowed (no branches). crown atlas=True|[cells] (twig/ellipsoid/spindle): each card
#       shows one cell of <tex>_Leaves_Cards.json; tangent (0..1, ellipsoid): cards lie along the shell (topiary)
import bpy, bmesh, math, random, itertools, sys, os
from mathutils import Vector, Quaternion, noise

argv = sys.argv[sys.argv.index("--") + 1:]
def _opt(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
NAME = argv[0]; LOD1 = "--lod1" in argv; QA = _opt("--qa"); QA = QA and os.path.abspath(QA)  # Blender resolves relative render paths oddly
TEXDIR = os.path.abspath(_opt("--tex", ".")) + "/"
OUT = os.path.abspath(_opt("--out", ".")) + "/"
SRC = os.path.abspath(_opt("--blend", OUT)) + "/"
os.makedirs(SRC, exist_ok=True); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree_normals import transfer_crown_normals, leaf_normal_spread
from tree_checks import floating_bark_components, floating_islands
from tree_uv import cylinder_uvs, stretch_stats
import json, statistics
UP = Vector((0, 0, 1))
# --------------------------------------------------------------------------- species
# stems: (count, lean range, length range, r0, r1, gnarl, base spread)
# levels: list of dicts for child levels: n children, at (fractions along parent), ang (deg from
#   parent dir toward outward), len range, r (fraction of parent end radius), tip radius, gnarl, up bias
# crown: 'twig' (cards on depth>=1 twigs above minz) or 'shell' (cards on a shape surface)
CFG = {
 "JapaneseMaple": dict(height=3.6, width=4.4,
    stems=(3, (0.45, 0.6), (1.5, 1.7), 0.1, 0.065, 0.25, 0.06),
    levels=[dict(n=3, at=(0.55, 1.0), ang=(45, 65), len=(1.1, 1.45), r=0.75, tip=0.4, gnarl=0.3, up=0.02),
            dict(n=3, at=(0.4, 1.0), ang=(35, 60), len=(0.6, 0.9), r=0.6, tip=0.01, gnarl=0.35, up=0.0)],
    crown=dict(mode="twig", minz=1.3, count=470, size=0.78, flat=0.7, fold=0.08, out=0.9, upr=(-0.1, 0.45)),
    seed=39, tex="JapaneseMaple", proxy="hull"),
 "ItalianCypress": dict(height=5.0, width=1.15,
    stems=(1, (0.0, 0.02), (4.4, 4.4), 0.13, 0.03, 0.03, 0.0),
    levels=[dict(n=12, at=(0.12, 0.92), ang=(18, 30), len=(0.45, 0.8), r=1.6, tip=0.01, gnarl=0.1, up=0.05)],
    crown=dict(mode="spindle", z0=0.45, z1=4.8, rmax=0.56, peak=0.33, count=500, size=0.7, fold=0.1),
    seed=37, tex="ItalianCypress", proxy="capsule", len_taper=0.6),
 "BirchClump": dict(height=5.0, width=3.0, lobe=0.08,
    stems=(5, (0.1, 0.22), (3.1, 3.4), 0.075, 0.035, 0.12, 0.12),
    levels=[dict(n=3, at=(0.5, 1.0), ang=(30, 45), len=(0.8, 1.15), r=0.8, tip=0.45, gnarl=0.3, up=0.0),
            dict(n=2, at=(0.5, 1.0), ang=(40, 70), len=(0.45, 0.7), r=0.6, tip=0.008, gnarl=0.35, up=-0.12)],
    crown=dict(mode="twig", minz=2.6, count=340, size=0.72, flat=0.15, fold=0.1, out=0.7, upr=(-0.7, 0.3)),
    seed=26, tex="BirchClump", proxy="hull"),
 "Ficus": dict(height=3.6, width=3.0, lobe=0.08,
    stems=(1, (0.04, 0.06), (1.55, 1.55), 0.12, 0.09, 0.08, 0.0),
    levels=[dict(n=5, at=(0.85, 1.0), ang=(35, 55), len=(0.8, 1.0), r=0.8, tip=0.45, gnarl=0.25, up=0.04),
            dict(n=2, at=(0.6, 1.0), ang=(30, 55), len=(0.45, 0.65), r=0.6, tip=0.01, gnarl=0.3, up=0.0)],
    crown=dict(mode="ellipsoid", c=(0, 0, 2.45), rad=(1.45, 1.45, 1.12), count=500, size=0.68, fold=0.1, flat=0.0),
    seed=11, tex="Ficus", proxy="ellipsoid"),
 "StonePine": dict(height=5.0, width=5.0,
    stems=(1, (0.14, 0.18), (2.8, 2.8), 0.17, 0.11, 0.12, 0.0),
    levels=[dict(n=5, at=(0.8, 1.0), ang=(45, 62), len=(1.3, 1.7), r=0.72, tip=0.4, gnarl=0.2, up=0.03),
            dict(n=2, at=(0.6, 1.0), ang=(35, 60), len=(0.7, 1.0), r=0.6, tip=0.012, gnarl=0.25, up=0.0)],
    crown=dict(mode="ellipsoid", c=(0, 0, 4.0), rad=(2.45, 2.45, 0.5), count=500, size=0.95, fold=0.08, flat=0.75),
    seed=29, tex="StonePine", proxy="ellipsoid"),
 # --- olive set: six big ancient olives, all multi-trunk with gnarled lobed bases, all sharing the
 # Olive materials. Leaves are sprig cards (crown mode "sprig") whose stem base is buried on a
 # branch axis; every branch end is cone-capped. Crowns are irregular clumps on the limbs.
 "Olive": dict(height=6.0, width=7.0, lobe=0.32, caps=True, taper=True,
    stems=(3, (0.35, 0.5), (2.4, 2.7), 0.24, 0.13, 0.3, 0.16),
    levels=[dict(n=2, at=(0.55, 1.0), ang=(40, 60), len=(1.4, 1.8), r=0.75, tip=0.5, gnarl=0.3, up=0.12),
            dict(n=2, at=(0.4, 1.0), ang=(30, 50), len=(0.8, 1.1), r=0.75, tip=0.4, gnarl=0.35, up=0.06),
            dict(n=2, at=(0.4, 1.0), ang=(30, 55), len=(0.45, 0.6), r=0.65, tip=0.01, gnarl=0.4, up=0.03)],
    crown=dict(mode="sprig", minz=2.5, mindepth=2, count=380, size=0.75, fold=0.1, tilt=0.8, upbias=0.3),
    seed=None, tex="Olive", proxy="ellipsoid", len_scale=1.6),
 "OliveAncient": dict(height=5.8, width=8.5, lobe=0.36, caps=True, taper=True, outward=0.25,
    stems=(5, (1.0, 1.3), (2.5, 2.8), 0.24, 0.12, 0.34, 0.2),
    levels=[dict(n=2, at=(0.6, 1.0), ang=(30, 50), len=(1.3, 1.6), r=0.75, tip=0.5, gnarl=0.32, up=0.12),
            dict(n=2, at=(0.4, 1.0), ang=(30, 55), len=(0.6, 0.85), r=0.75, tip=0.4, gnarl=0.4, up=0.05),
            dict(n=1, at=(0.4, 1.0), ang=(30, 55), len=(0.4, 0.55), r=0.65, tip=0.01, gnarl=0.4, up=0.03)],
    crown=dict(mode="sprig", minz=2.4, mindepth=2, count=630, size=0.85, fold=0.0, tilt=0.8, upbias=0.3,
        fill=dict(frac=0.45, mindepth=0, size=1.2, inward=0.8)),
    seed=None, tex="Olive", proxy="ellipsoid", len_scale=1.6),
 "OliveStandard": dict(height=6.0, width=7.0, lobe=0.34, caps=True, taper=True, outward=0.25,
    stems=(4, (0.6, 0.8), (2.7, 3.0), 0.22, 0.12, 0.33, 0.18),
    levels=[dict(n=2, at=(0.55, 1.0), ang=(35, 55), len=(1.2, 1.5), r=0.75, tip=0.5, gnarl=0.32, up=0.12),
            dict(n=2, at=(0.4, 1.0), ang=(30, 55), len=(0.6, 0.85), r=0.75, tip=0.4, gnarl=0.4, up=0.05),
            dict(n=1, at=(0.4, 1.0), ang=(30, 55), len=(0.4, 0.55), r=0.65, tip=0.01, gnarl=0.4, up=0.03)],
    crown=dict(mode="sprig", minz=2.6, mindepth=2, count=630, size=0.85, fold=0.0, tilt=0.8, upbias=0.3,
        fill=dict(frac=0.45, mindepth=0, size=1.2, inward=0.8)),
    seed=None, tex="Olive", proxy="ellipsoid", len_scale=1.6),
 "OliveSplitLean": dict(height=6.0, width=7.0, lobe=0.34, caps=True, taper=True, outward=0.25, lean_dir=0.6, lean_fan=0.45,
    stems=(3, (0.6, 0.8), (2.6, 2.9), 0.24, 0.13, 0.34, 0.15),
    levels=[dict(n=2, at=(0.55, 1.0), ang=(35, 55), len=(1.2, 1.5), r=0.75, tip=0.5, gnarl=0.32, up=0.12),
            dict(n=2, at=(0.4, 1.0), ang=(30, 55), len=(0.6, 0.85), r=0.75, tip=0.4, gnarl=0.4, up=0.05),
            dict(n=2, at=(0.4, 1.0), ang=(30, 55), len=(0.4, 0.55), r=0.65, tip=0.01, gnarl=0.4, up=0.03)],
    crown=dict(mode="sprig", minz=2.5, mindepth=2, count=630, size=0.85, fold=0.0, tilt=0.8, upbias=0.3,
        fill=dict(frac=0.45, mindepth=0, size=1.2, inward=0.8)),
    seed=None, tex="Olive", proxy="ellipsoid", len_scale=1.6),
 "OliveTallFour": dict(height=6.5, width=7.0, lobe=0.3, caps=True, taper=True,
    stems=(4, (0.3, 0.45), (3.2, 3.6), 0.2, 0.1, 0.28, 0.16),
    levels=[dict(n=2, at=(0.55, 1.0), ang=(35, 55), len=(1.2, 1.6), r=0.75, tip=0.5, gnarl=0.3, up=0.08),
            dict(n=2, at=(0.4, 1.0), ang=(30, 55), len=(0.6, 0.9), r=0.75, tip=0.4, gnarl=0.35, up=0.05),
            dict(n=1, at=(0.4, 1.0), ang=(20, 40), len=(0.35, 0.5), r=0.65, tip=0.01, gnarl=0.4, up=0.03)],
    crown=dict(mode="sprig", minz=2.8, mindepth=2, count=600, size=0.85, fold=0.0, tilt=0.8, upbias=0.3,
        fill=dict(frac=0.35, mindepth=1, size=1.15)),
    seed=None, tex="Olive", proxy="ellipsoid", len_scale=1.6),
 "OliveVase": dict(height=6.2, width=8.0, lobe=0.3, caps=True, taper=True,
    stems=(6, (0.45, 0.6), (2.7, 3.0), 0.18, 0.1, 0.3, 0.22),
    levels=[dict(n=2, at=(0.6, 1.0), ang=(35, 55), len=(1.2, 1.5), r=0.75, tip=0.5, gnarl=0.3, up=0.1),
            dict(n=2, at=(0.4, 1.0), ang=(30, 55), len=(0.6, 0.85), r=0.75, tip=0.4, gnarl=0.4, up=0.05),
            dict(n=1, at=(0.4, 1.0), ang=(30, 55), len=(0.4, 0.55), r=0.65, tip=0.01, gnarl=0.4, up=0.03)],
    crown=dict(mode="sprig", minz=2.6, mindepth=2, count=630, size=0.85, fold=0.0, tilt=0.8, upbias=0.3,
        fill=dict(frac=0.35, mindepth=1, size=1.15)),
    seed=None, tex="Olive", proxy="ellipsoid", len_scale=1.6),
 # --- birch variants (share BirchClump textures/materials) ---
 "BirchSingle": dict(height=5.0, width=2.2, lobe=0.03,
    stems=(1, (0.02, 0.05), (4.0, 4.0), 0.11, 0.035, 0.06, 0.0),
    levels=[dict(n=16, at=(0.3, 0.97), ang=(40, 60), len=(0.55, 1.0), r=1.6, tip=0.008, gnarl=0.25, up=-0.03)],
    crown=dict(mode="ellipsoid", c=(0, 0, 2.95), rad=(1.0, 1.0, 1.75), count=480, size=0.6, fold=0.1, flat=0.0, under=False),
    seed=None, tex="BirchClump", proxy="ellipsoid"),
 "BirchWeeping": dict(height=4.8, width=3.6, lobe=0.03,
    stems=(3, (0.14, 0.26), (3.1, 3.5), 0.085, 0.04, 0.1, 0.1),
    levels=[dict(n=4, at=(0.45, 1.0), ang=(45, 70), len=(0.8, 1.1), r=0.75, tip=0.4, gnarl=0.25, up=-0.02),
            dict(n=3, at=(0.3, 1.0), ang=(70, 100), len=(1.5, 2.1), r=0.6, tip=0.006, gnarl=0.08, up=-0.55)],
    crown=dict(mode="twig", minz=1.0, count=410, size=0.72, flat=0.0, fold=0.1, out=0.12, upr=(-2.5, -1.4)),
    seed=None, tex="BirchClump", proxy="hull"),
}
if _opt("--config"):
    _ns = {}; exec(open(_opt("--config")).read(), _ns); CFG.update(_ns["CFG"])
CFG = CFG[NAME]
TEXN = CFG["tex"]
import tree_uv
if "bark_tile" in CFG:  # metres per bark texture repeat (default tree_uv.TILE 0.6; scans of known size: their width)
    tree_uv.TILE = CFG["bark_tile"]
if "bark_tile_min" in CFG:  # repeat scales with tube radius: bark_tile at bark_tile_r and above, bark_tile_min on twigs
    tree_uv.TILE_MIN = CFG["bark_tile_min"]; tree_uv.TILE_R = CFG.get("bark_tile_r", 1.0)
BARKN = CFG.get("bark_tex", TEXN)  # bark texture set may differ from the leaf set
TEX = TEXDIR

# mathutils.noise.noise_vector() is randomised per Blender session (verified: three runs, three results),
# so skeletons use three offset samples of the deterministic noise.noise() instead.
def det_noise_vector(x):
    return Vector((noise.noise(x), noise.noise(x + Vector((31.4, 0, 0))), noise.noise(x + Vector((0, 47.1, 0)))))

class Br:
    def __init__(s, pts, radii, depth): s.pts, s.radii, s.depth = pts, radii, depth

def _in_poly(x, y, poly):
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): inside = not inside
    return inside

def _seg_dist2(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0.0 if L < 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2

_CLEAR_BOX = {}

def in_clear(p):
    """True if point p lies in a CFG['clear'] keep-out volume (deck prism + margin, or walkway capsule)."""
    for v in CFG.get("clear", ()):
        if "poly" in v:
            z0, z1 = v["z"]
            if not (z0 <= p.z <= z1): continue
            P = v["poly"]; m = v.get("margin", 0.0)
            bb = _CLEAR_BOX.get(id(v))
            if bb is None:
                bb = _CLEAR_BOX[id(v)] = (min(x for x, _ in P) - m, min(y for _, y in P) - m,
                                          max(x for x, _ in P) + m, max(y for _, y in P) + m)
            if not (bb[0] <= p.x <= bb[2] and bb[1] <= p.y <= bb[3]): continue
            if _in_poly(p.x, p.y, P): return True
            if m > 0 and any(_seg_dist2(p.x, p.y, *a, *b) <= m * m for a, b in zip(P, P[1:] + P[:1])): return True
        else:
            a, b = Vector(v["seg"][0]), Vector(v["seg"][1]); ab = b - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
            if (p - (a + ab * t)).length <= v["r"]: return True
    return False

def grow(start, direction, length, r0, r1, segs, depth, out, gnarl, up, seed, keep_out=True, up_end=None, flat=0.0):
    pts, radii = [start.copy()], [r0]
    d = direction.normalized(); p = start.copy()
    for i in range(1, segs + 1):
        n = det_noise_vector(p * 1.7 + Vector((depth * 3.1, seed * 0.37, 0.5)))
        u = up if up_end is None else up + (up_end - up) * (i - 1) / max(1, segs - 1)  # up_end: bias ramps along it
        d = (d + n * gnarl + UP * u).normalized()
        if flat and Vector((d.x, d.y, 0.0)).length > 1e-6:  # flat: each segment levels out toward horizontal
            d = Vector((d.x, d.y, d.z * (1.0 - flat))).normalized()
        p = p + d * (length / segs)
        if depth > 0: p.z = max(p.z, 0.25)  # drooping twigs never reach the ground
        ri = r0 + (r1 - r0) * i / segs
        if keep_out and depth > 0 and CFG.get("clear") and (in_clear(p) or in_clear((p + pts[-1]) * 0.5) or in_clear(p + UP * ri)
                                               or in_clear(p - UP * ri) or in_clear(p + d * CFG.get("clear_pad", 0.0))):
            break  # keep-out volume: the branch ends before it (clear_pad m short, room for its tip card)
        pts.append(p.copy()); radii.append(r0 + (r1 - r0) * i / segs)
    if len(pts) < 2: return None
    if keep_out and depth > 0 and len(pts) < segs + 1 and (len(pts) - 1) / segs < CFG.get("clear_drop", 0.0):
        return None  # cut short by a keep-out volume: drop it rather than leave a stubby tapered cone
    if len(pts) < segs + 1: radii = [r0 + (radii[-1] - r0) * k / (len(pts) - 1) for k in range(len(pts))]
    b = Br(pts, radii, depth); out.append(b); return b

def smooth_path(pts, radii, thr, iters):
    """Chaikin corner cut on interior points bending more than thr rad; first/last point stay put."""
    for _ in range(iters):
        np_, nr = [pts[0]], [radii[0]]
        for i in range(1, len(pts) - 1):
            a, b = pts[i] - pts[i - 1], pts[i + 1] - pts[i]
            if a.length < 1e-6 or b.length < 1e-6 or a.angle(b) <= thr:
                np_.append(pts[i]); nr.append(radii[i]); continue
            np_ += [pts[i] - a * 0.25, pts[i] + b * 0.25]
            nr += [radii[i] + (radii[i - 1] - radii[i]) * 0.25, radii[i] + (radii[i + 1] - radii[i]) * 0.25]
        np_.append(pts[-1]); nr.append(radii[-1])
        if len(np_) == len(pts): break
        pts, radii = np_, nr
    return pts, radii

def point_at(b, f):
    x = f * (len(b.pts) - 1); i = min(int(x), len(b.pts) - 2); t = x - i
    p = b.pts[i].lerp(b.pts[i + 1], t); r = b.radii[i] + (b.radii[i + 1] - b.radii[i]) * t
    d = (b.pts[i + 1] - b.pts[i]).normalized(); return p, r, d

MERGE_ATTACH = 0.05  # m: a child base within this of its parent's tube surface (or inside it) hangs on that tube
MERGE_SKIPPED = [0]  # merges refused because they would have dropped a stub carrying another child

def axis_gap(p, pts, radii):
    """Distance from p to the tube surface around the polyline pts (radius interpolated per segment); < 0 inside."""
    best = 1e9
    for i in range(len(pts) - 1):
        a, e = pts[i], pts[i + 1] - pts[i]; ll = e.length_squared
        t = 0.0 if ll < 1e-12 else max(0.0, min(1.0, (p - a).dot(e) / ll))
        best = min(best, (p - (a + e * t)).length - (radii[i] + (radii[i + 1] - radii[i]) * t))
    return best

def merge_continuations(branches, M):
    """Sympodial growth: a branch whose last fork sits near its end continues into that child (the best
    aligned one) as one tube. The parent drops its stub past the fork, takes the child's axis, and blends
    its radius into the child's over `blend` points; the child keeps its Br (cards, attach checks, its own
    children) but is not meshed (merged_into). M = dict(at=0.7, ang=65, blend=2, round=0, depth=(0, 99)).
    A best child turning more than `ang` off the parent's end is first swung (with its whole subtree, rigidly,
    about its base) to exactly `ang`, so the limb bends instead of leaving a hairpin with spikes. A merge that would
    drop a stub another child hangs on (that child's bark would float) is skipped: the limb stays as grown."""
    at, ang, nb = M.get("at", 0.7), math.radians(M.get("ang", 65)), M.get("blend", 2)
    dmin, dmax = M.get("depth", (0, 99))  # parent depths allowed to continue (each chain is meshed with its head's sides)
    kids_of = {}  # raw skeleton: child -> parent by nearest axis point (before any merge moves points)
    for c in branches:
        if c.depth == 0: continue
        best = None
        for b in branches:
            if b.depth != c.depth - 1: continue
            k = min(range(len(b.pts)), key=lambda i: (b.pts[i] - c.pts[0]).length)
            d = (b.pts[k] - c.pts[0]).length
            if best is None or d < best[0]: best = (d, b)
        if best: kids_of.setdefault(id(best[1]), []).append(c)
    def subtree(x):
        out, st = [], [x]
        while st:
            y = st.pop(); out.append(y); st += kids_of.get(id(y), [])
        return out
    for b in sorted(branches, key=lambda x: -x.depth):
        if getattr(b, "sides", None) or getattr(b, "keep", False) or len(b.pts) < 2: continue
        if not dmin <= b.depth <= dmax: continue
        seg = [(b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1)]
        L = sum(seg); cum = [0.0]
        for x in seg: cum.append(cum[-1] + x)
        kids = []
        for c in branches:
            if c.depth != b.depth + 1 or getattr(c, "merged_into", None) is not None or getattr(c, "sides", None): continue
            k = min(range(len(b.pts)), key=lambda i: (b.pts[i] - c.pts[0]).length)
            if (b.pts[k] - c.pts[0]).length < b.radii[k] + 0.1: kids.append((k, c))
        if not kids: continue
        klast = max(k for k, _ in kids)
        if cum[klast] / L < at: continue
        end_d = (b.pts[-1] - b.pts[-2]).normalized()
        cand = [(end_d.angle((c.pts[1] - c.pts[0]).normalized()), k, c) for k, c in kids if k == klast and len(c.pts) > 1]
        if not cand: continue
        a, k, c = min(cand, key=lambda x: x[0])
        q = None
        if a > ang:
            if not M.get("straighten", True): continue
            cd = (c.pts[1] - c.pts[0]).normalized(); axis = end_d.cross(cd)
            if axis.length < 1e-6: continue
            q = Quaternion(axis.normalized(), -(a - ang)); o = c.pts[0].copy()
        k = max(k, 1)  # keep at least the parent's first segment
        ratio = b.radii[k - 1] / max(c.radii[0], 1e-4)
        new_r = b.radii[:k] + [r * (ratio + (1.0 - ratio) * min(1.0, j / max(nb, 1))) for j, r in enumerate(c.radii)]
        cps = c.pts if q is None else [o + q @ (p - o) for p in c.pts]
        if q is not None and c.depth > 0: cps = [Vector((p.x, p.y, max(p.z, 0.25))) for p in cps]
        new_p = b.pts[:k] + cps
        # the merge drops b's stub past the fork: never if another child hangs on that stub (its bark would float;
        # the kid test above only sees children within 0.1 m of a polyline vertex). A child hangs on b when its base
        # is inside b's tube or within MERGE_ATTACH of it; it is left hanging when its base sits farther outside the
        # new tube than before by more than its own base radius (its tube no longer reaches the new parent tube).
        def orphaned(x):
            g0 = axis_gap(x.pts[0], b.pts, b.radii)
            return g0 <= MERGE_ATTACH and axis_gap(x.pts[0], new_p, new_r) > max(g0, 0.0) + x.radii[0]
        if any(x is not c and getattr(x, "merged_into", None) is None and orphaned(x) for x in kids_of.get(id(b), [])):
            MERGE_SKIPPED[0] += 1; continue
        if q is not None:
            for y in subtree(c):
                y.pts = [o + q @ (p - o) for p in y.pts]
                if y.depth > 0:
                    for p in y.pts: p.z = max(p.z, 0.25)
        b.lobe_end = cum[k - 1]
        b.pts = b.pts[:k] + [p.copy() for p in c.pts]
        b.radii = new_r
        rd = M.get("round", 0)  # corner-cut only the joint (window around the fork): a curve, not an elbow
        if rd:
            i0, i1 = max(0, k - 2), min(len(b.pts), k + 3)
            wp, wr = smooth_path(b.pts[i0:i1], b.radii[i0:i1], math.radians(M.get("round_bend", 15)), rd)
            b.pts = b.pts[:i0] + wp + b.pts[i1:]; b.radii = b.radii[:i0] + wr + b.radii[i1:]
            b.lobe_end += 0.0
        b.cont = c; c.merged_into = b

def build_skeleton(seed):
    rng = random.Random(seed); out = []
    cnt, lean, L, r0, r1, gn, spread = CFG["stems"]
    parents = []
    for k in range(cnt):
        if "lean_dir" in CFG:  # all stems lean one way, fanned around that azimuth
            az = CFG["lean_dir"] + (k - (cnt - 1) / 2) * CFG.get("lean_fan", 0.5) + rng.uniform(-0.15, 0.15)
        else:
            az = 2 * math.pi * k / cnt + rng.uniform(-0.3, 0.3)
        le = rng.uniform(*lean) if cnt > 1 else rng.uniform(*lean)
        d = Vector((math.cos(az) * le, math.sin(az) * le, 1.0))
        base = Vector((math.cos(az) * spread, math.sin(az) * spread, 0.0))
        sc = 1.0 if k == 0 or cnt < 4 else rng.uniform(0.7, 1.0)
        parents.append(grow(base, d, rng.uniform(*L) * sc, r0 * sc, r1 * sc, CFG.get("stem_segs", 6), 0, out, gn,
                            CFG.get("bend", 0.0), seed + k))
    trunk = out[0]; TL = sum((trunk.pts[i + 1] - trunk.pts[i]).length for i in range(len(trunk.pts) - 1))
    def side_limbs(grown):  # extra trunk limbs at absolute heights; grown=True ones get the upper levels' children
        made = []
        for k, S in enumerate(CFG.get("side", ())):
            if bool(S.get("grow")) != grown: continue
            for j in range(S["n"]):
                z = S["z"][0] + (S["z"][1] - S["z"][0]) * (j + rng.uniform(0.1, 0.9)) / S["n"]
                p, r, d = point_at(trunk, min(1.0, z / TL))
                if in_clear(p): continue
                az = rng.uniform(0, 2 * math.pi); perp = Vector((math.cos(az), math.sin(az), 0.0))
                a = math.radians(rng.uniform(*S["ang"])); cd = (d * math.cos(a) + perp * math.sin(a)).normalized()
                rr = r * S["r"]
                c = grow(p - d * min(0.03, r), cd, rng.uniform(*S["len"]), rr, S["tip"] * rr if S["tip"] > 0.05 else S["tip"],
                         4 if grown else 3, 1, out, S.get("gnarl", 0.2), S.get("up", 0.0), seed * 13 + j + k * 17)
                if c: made.append(c)
        return made
    for lv, P in enumerate(CFG["levels"]):
        nxt = []
        if lv == 1:
            nxt_extra = side_limbs(True)
            for k, X in enumerate(CFG.get("limbs", ())):  # explicit limbs (e.g. carrying a hanging pod): root -> tip
                root, tip = Vector(X["root"]), Vector(X["tip"]); q, rq, dq = point_at(trunk, min(1.0, root.z / TL))
                st = Vector((q.x, q.y, root.z)); v = tip - st
                c = grow(st, v.normalized(), v.length, X["r"][0], X["r"][1], 6, 1, out, X.get("gnarl", 0.0), 0.0,
                         seed * 17 + k, keep_out=False)
                if c:
                    c.radii[-1] = X["r"][1]; c.keep = True  # no taper to a tip: the pod rope is lashed at its end
                    n = len(c.pts) - 1
                    for i in range(1, n):  # gentle upward arch, ends stay put
                        t = i / n; c.pts[i].z += X.get("arch", 0.0) * 4 * t * (1 - t)
                    c.epi = X.get("epiphytes", 0)
                    if X.get("children", True): nxt_extra.append(c)
            for k, Sc in enumerate(CFG.get("screens", ())):
                c0 = Vector(Sc["centre"]); w, h, dd = Sc["size"]; az = math.radians(Sc["facing"])
                f = Vector((math.cos(az), math.sin(az), 0.0)); sdir = Vector((-f.y, f.x, 0.0))
                ztop = c0.z + h / 2 + 0.4; q, rq, _ = point_at(trunk, min(1.0, ztop / TL))
                axis = Vector((q.x, q.y, ztop))
                for side in (-1, 1):  # two short limbs from the trunk out over the screen's ends
                    end = c0 + sdir * side * w * 0.45 + Vector((0, 0, h / 2 + 0.3))
                    v = end - axis
                    hl = grow(axis, v.normalized(), v.length, Sc.get("r", 0.16), 0.05, 4, 2, out, 0.05, 0.0,
                              seed * 23 + k * 2 + side, keep_out=False)
                    if not hl: continue
                    for j in range(Sc.get("twigs", 7)):  # hanging twigs through the box
                        p0 = point_at(hl, rng.uniform(0.35, 1.0))[0] + f * rng.uniform(-dd / 2, dd / 2) * 0.6
                        tw = grow(p0, (-UP + rand_unit(rng) * 0.15).normalized(), h + 0.2 - (ztop - 0.4 - p0.z) * 0, 0.03,
                                  TIP_R, 3, 3, out, 0.1, 0.0, seed * 29 + j + k * 31, keep_out=False)
                        if tw: tw.screen = k
            parents = parents + nxt_extra
        if lv == 0 and CFG.get("fork"):  # decurrent crown: the trunk splits into its major limbs at the top
            F = CFG["fork"]; pt, rt, dt = point_at(trunk, 1.0); az0 = rng.uniform(0, 2 * math.pi)
            for j in range(F["n"]):
                lead = j == 0  # the leader continues the trunk line, so the top never shows a cut end
                f = 1.0 if lead else rng.uniform(0.9, 0.97)  # the other limbs leave a few metres lower, staggered
                p, r, d = point_at(trunk, f)
                az = az0 + 2 * math.pi * j / F["n"] + rng.uniform(-0.35, 0.35)
                perp = Vector((math.cos(az), math.sin(az), 0.0))
                a = math.radians(rng.uniform(4, 12) if lead else rng.uniform(*F["ang"]))
                cd = (d * math.cos(a) + perp * math.sin(a)).normalized()
                rr = rt * (0.85 if lead else F["r"]) if lead else r * F["r"]
                start = pt - dt * rt * 0.6 if lead else p - d * min(0.03, r)
                c = grow(start, cd, rng.uniform(*F["len"]), rr, F["tip"] * rr, 5, 1, out, F.get("gnarl", 0.1),
                         F.get("up", 0.0), seed * 5 + j)
                if c: nxt.append(c)
            trunk.radii[-1] = rt * 0.8  # the leader (0.85 x) sheathes the trunk end
        for b in parents:
            n = P["n"]; wk = P.get("whorl")
            for j in range(n):
                if wk:  # whorls (conifers): wk limbs per height, evenly spread around the parent, staggered per whorl
                    nw = -(-n // wk)
                    if j % wk == 0:
                        w = j // wk
                        fw = P["at"][0] + (P["at"][1] - P["at"][0]) * (w / max(1, nw - 1)) if nw > 1 else P["at"][1]
                        fw = min(1.0, fw + rng.uniform(-0.02, 0.02)); azw = rng.uniform(0, 2 * math.pi)
                    f = fw; p, r, d = point_at(b, f)
                    az = azw + 2 * math.pi * (j % wk) / wk + rng.uniform(-0.25, 0.25)
                else:
                    f = P["at"][0] + (P["at"][1] - P["at"][0]) * (j / max(1, n - 1)) if n > 1 else P["at"][1]
                    f = min(1.0, f + rng.uniform(-0.04, 0.04))
                    p, r, d = point_at(b, f)
                    az = rng.uniform(0, 2 * math.pi) if n > 3 else (j / n) * 2 * math.pi + rng.uniform(-0.6, 0.6)
                perp = d.orthogonal().normalized(); perp.rotate(__import__("mathutils").Quaternion(d, az))
                outw = Vector((p.x, p.y, 0));
                if outw.length > 0.05 and lv == 0 and n <= 3: perp = (perp + outw.normalized() * CFG.get("outward", 1.2)).normalized()
                if "ang_end" in P:  # angle range moves from `ang` (at[0]) to `ang_end` (at[1]): drooping lower limbs
                    h = max(0.0, min(1.0, (f - P["at"][0]) / max(1e-6, P["at"][1] - P["at"][0])))
                    a = math.radians(rng.uniform(*(x + (y - x) * h for x, y in zip(P["ang"], P["ang_end"]))))
                else:
                    a = math.radians(rng.uniform(*P["ang"]))
                cd = (d * math.cos(a) + perp * math.sin(a)).normalized()
                ln = rng.uniform(*P["len"]) * CFG.get("len_scale", 1.0)  # olives: long sweeping limbs
                if CFG.get("len_taper"): ln *= 1.0 - CFG["len_taper"] * f  # columnar: shorter limbs higher up
                rr = min(r * P["r"], r * 0.9) if P["r"] < 1 else min(0.03, r * 0.6)
                if CFG.get("clear") and (in_clear(p) or any(in_clear(p + e * (rr * 1.5 + 0.3)) for e in (UP, -UP, -cd))):
                    continue  # no branch starts in (or with its thickness / buried base cone reaching into) a volume
                c = grow(p - d * min(0.03, r), cd, ln, rr, P["tip"] * rr if P["tip"] > 0.05 else P["tip"],
                         P.get("segs", 4 if lv == 0 else 3), lv + 1, out, P["gnarl"], P["up"], seed * 7 + j + lv * 31,
                         up_end=P.get("up_end"), flat=P.get("flat", 0.0))
                if c: nxt.append(c)
        parents = nxt
    side_limbs(False)  # stubs etc.: no children
    L = CFG.get("lianas")
    if L:  # thin climbing vine stems hugging the trunk, winding slowly up; stop before any keep-out volume
        for j in range(L["n"]):
            az0 = 2 * math.pi * j / L["n"] + rng.uniform(-0.4, 0.4); tw = rng.uniform(-1, 1) * L.get("twist", 0.6)
            z1 = rng.uniform(*L["z"]); lr = rng.uniform(*L["r"]); pts, radii = [], []
            for i in range(L.get("segs", 12) + 1):
                t = i / L.get("segs", 12); z = z1 * t
                q, r, _ = point_at(trunk, min(1.0, z / TL)); az = az0 + tw * t * 2 * math.pi
                pt = Vector((q.x, q.y, z)) + Vector((math.cos(az), math.sin(az), 0.0)) * (r * 0.97 + lr)
                if CFG.get("clear") and in_clear(pt): break
                pts.append(pt); radii.append(lr)
            if len(pts) >= 3:
                radii[-1] = TIP_R; lb = Br(pts, radii, 1); lb.sides = 3; out.append(lb)
    B = CFG.get("buttress")
    if B:  # flaring roots: from the trunk at height z out and down to the waterline at reach
        for j in range(B["n"]):
            az = 2 * math.pi * j / B["n"] + rng.uniform(-0.25, 0.25)
            z = rng.uniform(*B["z"]); p, r, _ = point_at(trunk, min(1.0, z / TL))
            out_d = Vector((math.cos(az), math.sin(az), 0.0)); R = rng.uniform(*B["reach"])
            pts = [p + out_d * r * 0.2]; radii = [B["r"]]
            for i in range(1, 5):  # concave sweep: steep near the trunk, flat into the water
                t = i / 4; pts.append(Vector((p.x, p.y, 0)) + out_d * (r * 0.6 + R * t ** 0.8) + Vector((0, 0, z * (1 - t) ** 2.2)))
                radii.append(B["r"] * (1 - 0.75 * t))
            out.append(Br(pts, radii, 1))
    return out

# --------------------------------------------------------------------------- meshing
TIP_R = 0.003  # radius of a tapered branch end (m)

def tube(bm, br, sides, lobe_amt, cap):
    rings = []; acc = 0.0; prev_n = None
    for i, (p, r) in enumerate(zip(br.pts, br.radii)):
        t = (br.pts[i + 1] - p).normalized() if i < len(br.pts) - 1 else (p - br.pts[i - 1]).normalized()
        if i > 0: acc += (p - br.pts[i - 1]).length
        if prev_n is None:
            n = UP.cross(t)
            if n.length < 1e-4: n = Vector((1, 0, 0)).cross(t)
            n.normalize()
        else:
            n = (prev_n - t * prev_n.dot(t)).normalized()
        prev_n = n; b = t.cross(n); ring = []
        lb = lobe_amt if br.depth == 0 else 0.0
        if CFG.get("merge") or CFG.get("smooth"):  # extra rings: phase by arc length, fade along a merged limb
            ph = 1.7 * acc / 0.45
            le = getattr(br, "lobe_end", None)
            if le is not None: lb *= max(0.0, 1.0 - (acc - le) / 0.6) if acc > le else 1.0
        else:
            ph = 1.7 * i
        for s in range(sides):
            a = 2 * math.pi * s / sides
            lobe = 1.0 + lb * math.sin(3 * a + ph)
            q = p + (n * math.cos(a) + b * math.sin(a)) * r * lobe
            if i == 0 and br.depth == 0: q.z = 0.0
            ring.append(bm.verts.new(q))
        rings.append((ring, acc))
    for (r0, v0), (r1, v1) in zip(rings, rings[1:]):
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((r0[s], r0[s2], r1[s2], r1[s])); f.material_index = 0
    if br.depth > 0 and CFG.get("taper"):  # base ring closed by a cone buried in the parent: no open fork ring
        ring = rings[0][0]
        t = (br.pts[1] - br.pts[0]).normalized()
        apex = bm.verts.new(br.pts[0] - t * max(br.radii[0] * 1.5, 0.02))
        for s in range(sides):
            f = bm.faces.new((ring[(s + 1) % sides], ring[s], apex)); f.material_index = 0
    if cap:  # pointed cone closes the branch end (no open ring / flat disc)
        ring = rings[-1][0]
        t = (br.pts[-1] - br.pts[-2]).normalized()
        # forked trunk: a low crotch dome, not a spear; palm stem under a rosette: a blunt cone hidden in the frond bases
        k = 0.35 if (br.depth == 0 and CFG.get("fork")) else 1.0 if (br.depth == 0 and CFG["crown"]["mode"] == "rosette") else 2.5
        apex = bm.verts.new(br.pts[-1] + t * max(br.radii[-1] * k, 0.02))
        for s in range(sides):
            f = bm.faces.new((ring[s], ring[(s + 1) % sides], apex)); f.material_index = 0

def card(bm, uvl, base, d, nrm, s, fold, cell=None):
    """cell (atlas cell dict from <tex>_Leaves_Cards.json): UVs span that cell instead of the whole texture."""
    d = d.normalized(); nrm = (nrm - d * nrm.dot(d)).normalized(); side = nrm.cross(d)
    w = side * s * 0.5; base = base - d * s * 0.05; top = base + d * s; fv = nrm * s * fold
    u0, v0, u1, v1 = cell["rect"] if cell else (0.0, 0.0, 1.0, 1.0)
    if fold > 0:
        vs = [bm.verts.new(x) for x in (base - w, base + fv, base + w, top + w, top + fv, top - w)]
        for idx, us in (((0, 1, 4, 5), (0, .5, .5, 0)), ((1, 2, 3, 4), (.5, 1, 1, .5))):
            f = bm.faces.new([vs[k] for k in idx]); f.material_index = 1
            for loop, u, v in zip(f.loops, us, (0, 0, 1, 1)): loop[uvl].uv = (u0 + u * (u1 - u0), v0 + v * (v1 - v0))
    else:
        vs = [bm.verts.new(x) for x in (base - w, base + w, top + w, top - w)]
        f = bm.faces.new(vs); f.material_index = 1
        for loop, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uvl].uv = (u0 + u * (u1 - u0), v0 + v * (v1 - v0))

def sprig_card(bm, uvl, A, d, roll, s, fold, cell, dry=False):
    """Card whose atlas stem-base attach point lands exactly on A (a point on a branch axis).
    dry: only return its corner points (0,0), (1,0), (1,1), (0,1), nothing is created."""
    d = d.normalized(); n = (roll - d * roll.dot(d)).normalized(); side = n.cross(d)
    u0, v0, u1, v1 = cell["rect"]
    au = (cell["attach"][0] - u0) / (u1 - u0); av = (cell["attach"][1] - v0) / (v1 - v0)
    fv = n * s * fold
    O = A - (side * (au - 0.5) * s + d * av * s + fv * max(0.0, 1.0 - abs(au - 0.5) * 2))
    grid = ((0, 0), (.5, 0), (1, 0), (1, 1), (.5, 1), (0, 1)) if fold > 0 else ((0, 0), (1, 0), (1, 1), (0, 1))
    if dry: return [O + side * (lu - 0.5) * s + d * lv * s for lu, lv in ((0, 0), (1, 0), (1, 1), (0, 1))]
    first = len(bm.verts)
    vs = [bm.verts.new(O + side * (lu - 0.5) * s + d * lv * s + (fv if lu == 0.5 else Vector())) for lu, lv in grid]
    quads = ((0, 1, 4, 5), (1, 2, 3, 4)) if fold > 0 else ((0, 1, 2, 3),)
    for q in quads:
        f = bm.faces.new([vs[k] for k in q]); f.material_index = 1
        for loop, k in zip(f.loops, q):
            lu, lv = grid[k]; loop[uvl].uv = (u0 + lu * (u1 - u0), v0 + lv * (v1 - v0))
    return first, grid, (au, av)

def rand_unit(rng):
    v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))); return v.normalized()

def orient_normal(rng, d, flat):
    r = rand_unit(rng); r = (r - d * r.dot(d)).normalized()
    u = (UP - d * UP.dot(d))
    if u.length < 1e-3: return r
    return r.lerp(u.normalized(), flat).normalized()

def terminal_ends(branches):
    """Branches whose end does not continue into a child branch (their tips need foliage). A merged parent
    (cont) shares its continuation's end, which is counted on the continuation."""
    starts = [(b.pts[0], b.depth) for b in branches]
    return [b for b in branches if getattr(b, "cont", None) is None
            and not any(dep > b.depth and (p - b.pts[-1]).length < 0.2 for p, dep in starts)]

def sprig_crown(bm, uvl, branches, rng, count, size, fold, lod1=False, keep=None):
    """keep (lod1_subset): place the LOD0 cards with the LOD0 random sequence, but build only the tip cards plus
    a `keep` share of the others, `grow` times larger around the same attach point (LOD1 = LOD0 thinned)."""
    C = CFG["crown"]
    cells = json.load(open(TEX + f"{TEXN}_Leaves_Cards.json"))["cells"]
    md = C["mindepth"]
    if lod1 and CFG.get("lod1_mindepth") is not None: md = CFG["lod1_mindepth"]
    twigs = [b for b in branches if b.depth >= md and not getattr(b, "sides", None)]
    lens = [sum((b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1)) for b in twigs]
    cards = []  # every placed card (counts drive the loops below); dropped subset cards have first = None
    krng = random.Random(7919)  # own sequence: the subset choice never shifts the placement draws
    def place(b, t, d0, hang=False, nrm=None, exact=True):
        A, r, d = point_at(b, t)
        sz = size * rng.uniform(0.85, 1.15)
        if C.get("size_top") is not None:  # cards shrink toward the top (conifer spire): size x size_top at `height`
            sz *= 1.0 + (C["size_top"] - 1.0) * max(0.0, min(1.0, A.z / CFG["height"]))
        if CFG.get("clear"):
            if in_clear(A): return False
            ok = False
            for k in range(12):  # reroute (then shrink): a card may not reach into a keep-out volume
                if k == 8: sz *= 0.6
                if k == 10: sz *= 0.6
                d = ((-UP * 1.0 + rand_unit(rng) * 0.35) if hang else (d0 + rand_unit(rng) * C["tilt"] + UP * C["upbias"])).normalized()
                e1 = d.orthogonal().normalized(); e2 = d.cross(e1)  # the card is sz wide in an unknown roll
                if not any(in_clear(A + d * sz * f + e * sz * 0.5) for f in (0.0, 0.35, 0.7, 1.0)
                           for e in (Vector(), e1, -e1, e2, -e2, (e1 + e2) * 0.7072, (e1 - e2) * 0.7072,
                                     (e2 - e1) * 0.7072, -(e1 + e2) * 0.7072)): ok = True; break
            if not ok: return False
        else:
            d = ((-UP + rand_unit(rng) * 0.35) if hang else (d0 + rand_unit(rng) * C["tilt"] + UP * C["upbias"])).normalized()
        roll, cell = nrm if nrm is not None else rand_unit(rng), rng.choice(cards_cells)
        fl = C.get("flat", 0.0) if C["mode"] == "sprig" and not hang else 0.0
        if fl:  # flat (sprig): cards lie toward horizontal with their face toward the sky (layered flat crowns)
            if Vector((d.x, d.y, 0.0)).length > 1e-6: d = Vector((d.x, d.y, d.z * (1.0 - fl))).normalized()
            roll = roll.lerp(UP, fl).normalized()
        if exact and CFG.get("clear"):  # the real card surface (its back overhang and corners too) must stay out of the volumes
            q = sprig_card(bm, uvl, A, d, roll, sz, fold, cell, dry=True)
            if any(in_clear(q[0].lerp(q[1], i / 4).lerp(q[3].lerp(q[2], i / 4), j / 4)) for i in range(5) for j in range(5)):
                return False
        if C.get("ground") is not None:  # hanging cards stay above this height: shrink, then skip
            for _ in range(5):
                if min(x.z for x in sprig_card(bm, uvl, A, d, roll, sz, fold, cell, dry=True)) >= C["ground"]: break
                sz *= 0.75
            else:
                return False
        if keep is not None and t < 0.95 and krng.random() >= keep.get("keep", 0.5):
            cards.append((None, None, None, b, t)); return True
        first, grid, att = sprig_card(bm, uvl, A, d, roll, sz * (keep.get("grow", 1.3) if keep else 1.0), fold, cell)
        cards.append((first, grid, att, b, t)); return True
    cards_cells = cells
    bm.verts.ensure_lookup_table()
    # every terminal end above the leaf zone gets a card rooted just inside its cone cap
    for b in terminal_ends(branches):
        if b.pts[-1].z >= C["minz"] * 0.8:
            _, _, d = point_at(b, 0.97); place(b, 0.97, d)
    fill = C.get("fill")  # share of the cards spread over the inner limbs to close the gaps between clumps
    if fill:
        inner = [b for b in branches if b.depth >= fill["mindepth"]]
        ilens = [sum((b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1)) for b in inner]
        target = len(cards) + int(count * fill["frac"])
        base = size
        size = base * fill["size"]
        tries = 0
        while len(cards) < target and tries < count * 20:
            tries += 1
            b = rng.choices(inner, ilens)[0]
            t = rng.uniform(0.35, 0.97)
            A, _, d = point_at(b, t)
            if A.z < C["minz"]: continue
            # lean toward the crown axis and up, so fill cards close the hollow between splayed limbs
            to_axis = Vector((-A.x, -A.y, 0.0))
            if to_axis.length > 1e-3: d = (d * 0.4 + to_axis.normalized() * fill.get("inward", 0.0) + UP * 0.6).normalized()
            place(b, t, d)
        size = base
    if C.get("per_tip"):  # dense clusters on the outer part of every leaf-bearing branch, gaps between them
        k = C["per_tip"] if not lod1 else max(2, int(C["per_tip"] * CFG.get("lod1_cards", 0.6)))
        for b in twigs:
            if b.pts[-1].z < C["minz"]: continue
            for i in range(k):
                t = rng.uniform(C.get("tip_from", 0.55), 0.98); _, _, d = point_at(b, t); place(b, t, d)
        count = len(cards)
    tries = 0
    while len(cards) < count and tries < count * 20:
        tries += 1
        b = rng.choices(twigs, lens)[0]
        t = rng.uniform(0.2, 0.97)
        if point_at(b, t)[0].z < C["minz"]: continue
        _, _, d = point_at(b, t); place(b, t, d)
    V = CFG.get("vines")
    if V:  # hanging cards under limbs: draped foliage / epiphytes, rooted on the branch axis like the sprigs
        hosts = [b for b in branches if b.depth >= 1 and any(V["z"][0] <= p.z <= V["z"][1] for p in b.pts)]
        hl = [sum((b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1)) for b in hosts]
        base, size = size, V["size"] * (1.35 if size != C["size"] else 1.0)
        target, tries = len(cards) + int(V["count"] * ((count / C["count"]) if C["count"] else (CFG.get("lod1_cards", 0.6) if lod1 else 1.0))), 0
        while hosts and len(cards) < target and tries < V["count"] * 20:
            tries += 1
            b = rng.choices(hosts, hl)[0]; t = rng.uniform(0.15, 0.95)
            A = point_at(b, t)[0]
            if not (V["z"][0] <= A.z <= V["z"][1]) or A.z - size < 0.3: continue
            place(b, t, -UP, hang=True)
        size = base
    for b in branches:  # epiphytes / moss tufts hanging along explicit limbs (cards keep out of the volumes)
        for i in range(getattr(b, "epi", 0) if not lod1 else 0):
            place(b, rng.uniform(0.12, 0.92), -UP, hang=True)
    for k, Sc in enumerate(CFG.get("screens", ()) if not lod1 else ()):
        # foliage screen: hanging twigs from a limb over a box (centre, size w/h/d, facing az), packed with cards
        c0 = Vector(Sc["centre"]); w, h, dd = Sc["size"]; az = math.radians(Sc["facing"])
        f = Vector((math.cos(az), math.sin(az), 0.0)); sdir = Vector((-f.y, f.x, 0.0))
        hosts = [b for b in branches if getattr(b, "screen", None) == k]
        base, size = size, Sc.get("card", size)
        made = tries = 0
        while hosts and made < Sc["count"] and tries < Sc["count"] * 30:
            tries += 1
            b = rng.choice(hosts); t = rng.uniform(0.1, 0.98); A = point_at(b, t)[0]
            q = A - c0
            if abs(q.dot(sdir)) > w / 2 or abs(q.dot(f)) > dd / 2: continue
            # cards hang sideways/down in the screen plane and face the viewer (normal ~ facing), so they cover
            d = (sdir * rng.uniform(-1.0, 1.0) - UP * rng.uniform(0.2, 1.0) + f * rng.uniform(-0.15, 0.15)).normalized()
            if A.z + d.z * size < c0.z - h / 2 - 0.2: continue
            n0 = len(cards); place(b, t, d, nrm=(f + rand_unit(rng) * 0.35).normalized(), exact=False)
            made += len(cards) - n0
        size = base
    return [c for c in cards if c[0] is not None]

def frond(bm, uvl, A, axis, rad, L, tilt, droop, twist, fold, cell, C):
    """One rosette frond: a strip of C['segs'] quads (2 per segment when folded) along a drooping arc. It leaves A
    (a point on the stem axis) along `rad` (unit, perpendicular to `axis`) at `tilt` deg above it and bends `droop` deg
    down toward the tip (bend ~ s^droop_pow), the cross direction rolling `twist` deg about the spine by the tip.
    The atlas cell's attach point (bottom-centre, branch_atlas.py) sits on A; the cell top is the tip; `crop` = share
    of the cell width used, `aspect` squeezes the width (1 = undistorted texture). fold > 0: the frond edges hang
    below the midrib (Λ section). Returns (first vertex, grid, attach) like sprig_card, or None if it hits the ground."""
    segs = C.get("segs", 4); u0, v0, u1, v1 = cell["rect"]
    au = (cell["attach"][0] - u0) / (u1 - u0); av = (cell["attach"][1] - v0) / (v1 - v0)
    crop = min(C.get("crop", 1.0), 2 * min(au, 1 - au))
    W = L / max(1.0 - av, 1e-3) * (u1 - u0) / (v1 - v0) * crop * C.get("aspect", 1.0)
    side0 = axis.cross(rad).normalized(); dp = C.get("droop_pow", 1.5)
    for _ in range(12):  # a frond may not reach the ground: relax its droop until it clears
        pts, dirs = [A.copy()], []
        for i in range(segs):
            e = math.radians(tilt - droop * ((i + 0.5) / segs) ** dp)
            dirs.append(rad * math.cos(e) + axis * math.sin(e)); pts.append(pts[-1] + dirs[-1] * (L / segs))
        if min(p.z for p in pts) >= 0.1: break
        droop *= 0.8
    else:
        return None
    rows = []
    for k, p in enumerate(pts):
        t = (dirs[max(0, k - 1)] + dirs[min(segs - 1, k)]).normalized()
        sd = (side0 - t * side0.dot(t)).normalized(); sd.rotate(Quaternion(t, math.radians(twist) * k / segs))
        nv = t.cross(sd); hang = nv * fold * W
        rows.append((p - sd * W / 2 - hang, p, p + sd * W / 2 - hang))
    lus = (0.0, 0.5, 1.0) if fold > 0 else (0.0, 1.0)
    grid = ((0, 0), (.5, 0), (1, 0), (1, 1), (.5, 1), (0, 1)) if fold > 0 else ((0, 0), (1, 0), (1, 1), (0, 1))
    first = len(bm.verts); vv = []
    for k, row in enumerate(rows):  # rows 0 and 1 in grid order (attach_report reads the first quad by it)
        cols = (row if fold > 0 else (row[0], row[2]))
        order = list(range(len(lus)))[::-1] if k == 1 else list(range(len(lus)))
        made = {j: bm.verts.new(cols[j]) for j in order}; vv.append([made[j] for j in range(len(lus))])
    def uv(j, k): return (u0 + (au + (lus[j] - 0.5) * crop) * (u1 - u0), v0 + (av + (1 - av) * k / segs) * (v1 - v0))
    for k in range(segs):
        for j in range(len(lus) - 1):
            q = ((j, k), (j + 1, k), (j + 1, k + 1), (j, k + 1))
            f = bm.faces.new([vv[b][a] for a, b in q]); f.material_index = 1
            for loop, (a, b) in zip(f.loops, q): loop[uvl].uv = uv(a, b)
    return first, grid, (0.5, 0.0)

def rosette_crown(bm, uvl, branches, rng, fold):
    """Palm / tree fern / banana: fronds radiating from every stem top (terminal end above minz). Per head: `count`
    fronds on a golden-angle spiral (or interleaved over `spread` deg), age 0 (youngest, top, upright) .. 1 (oldest,
    `zone` m lower, flattest, most drooping); optional upright `young` spears and hanging `dead` fronds."""
    C = CFG["crown"]
    cells = json.load(open(TEX + f"{TEXN}_Leaves_Cards.json"))["cells"]
    live = [cells[i] for i in C.get("cells", range(len(cells)))]
    blen = lambda b: sum((b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1))
    heads = [b for b in terminal_ends(branches) if b.pts[-1].z >= C.get("minz", 0.0) * 0.8]
    Lmax = max(blen(b) for b in heads); cards = []
    jit = C.get("jitter", 6.0); spread = C.get("spread", 360.0)
    for b in heads:
        Lb = blen(b); sc = (Lb / Lmax) ** C.get("stem_scale", 0.7)
        axis = point_at(b, 1.0)[2].lerp(UP, C.get("upright", 0.6)).normalized()
        e1 = axis.orthogonal().normalized(); e2 = axis.cross(e1)
        az0 = rng.uniform(0, 2 * math.pi); n = max(3, round(C["count"] * sc))
        specs = [("live", i / max(1, n - 1)) for i in range(n)]
        Y, D = C.get("young"), C.get("dead")
        specs += [("young", 0.0)] * (Y["n"] if Y else 0) + [("dead", 1.0)] * (D["n"] if D else 0)
        for i, (kind, age) in enumerate(specs):
            if spread >= 360: az = az0 + i * math.radians(137.508)
            else: az = az0 + math.radians(((i * 0.618034) % 1.0 - 0.5) * spread)
            rad = e1 * math.cos(az) + e2 * math.sin(az)
            S = {"live": C, "young": Y, "dead": D}[kind]
            lo, hi = S["tilt"]; tilt = hi + (lo - hi) * age + rng.uniform(-jit, jit)
            dlo, dhi = S["droop"]; droop = max(0.0, dlo + (dhi - dlo) * age + rng.uniform(-jit, jit))
            L = rng.uniform(*C["length"]) * sc * (S.get("length", 1.0) if kind != "live" else 1.0)
            tw = rng.uniform(-1, 1) * C.get("twist", 0.0)
            z = Lb - C.get("top", 0.0) - C.get("zone", 0.3) * age
            if kind == "dead": z -= rng.uniform(0, D.get("zone", 0.4))
            if kind == "young": tilt = rng.uniform(lo, hi)
            A = point_at(b, max(0.0, min(1.0, z / Lb)))[0]
            cell = cells[S["cell"]] if kind != "live" and S.get("cell") is not None else rng.choice(live)
            r = frond(bm, uvl, A, axis, rad, L, tilt, droop, tw, fold, cell, C)
            if r: cards.append(r + (b, 1.0))
    return cards

def crown(bm, uvl, branches, rng, count, size, fold, lod1=False, keep=None):
    C = CFG["crown"]; mode = C["mode"]
    if mode == "sprig":
        return sprig_crown(bm, uvl, branches, rng, count, size, fold, lod1, keep)
    if mode == "rosette":  # lod1_subset (keep): fronds identical to LOD0 (unfolding moves the edges by fold x width)
        return rosette_crown(bm, uvl, branches, rng, C.get("fold", 0.0) if keep is not None else fold)
    cells = None  # atlas: each card shows one cell of <tex>_Leaves_Cards.json instead of the whole texture
    if C.get("atlas"):
        cells = json.load(open(TEX + f"{TEXN}_Leaves_Cards.json"))["cells"]
        if C["atlas"] is not True: cells = [cells[i] for i in C["atlas"]]
    pick = lambda: rng.choice(cells) if cells else None
    if mode == "twig":
        tips = [b for b in branches if b.depth >= C.get("mindepth", 1)]
        centre = Vector((0, 0, CFG["height"] * 0.7)); made = 0
        while made < count:
            b = rng.choices(tips, [2 if b.depth >= 2 else 1 for b in tips])[0]
            p, _, _ = point_at(b, rng.uniform(0.35, 1.0))
            if p.z < C["minz"]: continue
            out = p - centre; out.z *= 0.4; out.normalize()
            d = (out * C["out"] + Vector((rng.uniform(-.6, .6), rng.uniform(-.6, .6), rng.uniform(*C["upr"])))).normalized()
            if p.z + d.z * size * 1.25 < 0.15: continue  # hanging card would touch the ground
            nrm = orient_normal(rng, d, C["flat"]); s = size * rng.uniform(0.8, 1.2)
            card(bm, uvl, p, d, nrm, s, fold, pick()); made += 1
        return
    for _ in range(count):
        if mode == "spindle":
            h = rng.uniform(0, 1)
            z = C["z0"] + (C["z1"] - C["z0"]) * h
            prof = math.sin(math.pi * min(1.0, h / (2 * C["peak"]))) if h < C["peak"] else math.cos(0.5 * math.pi * (h - C["peak"]) / (1 - C["peak"]))
            rad = C["rmax"] * max(0.08, prof) ** 0.8 * rng.uniform(0.7, 1.0)
            a = rng.uniform(0, 2 * math.pi); out = Vector((math.cos(a), math.sin(a), 0))
            p = Vector((0, 0, z)) + out * rad - out * size * 0.15
            d = (UP * 0.85 + out * 0.35 + rand_unit(rng) * 0.2).normalized()
            if z + size > C["z1"] + 0.1: d = UP.copy(); p.z = C["z1"] - size * rng.uniform(0.9, 1.3)
            nrm = orient_normal(rng, d, 0.0).lerp(out, 0.6)
        else:  # ellipsoid shell
            c = Vector(C["c"]); R = Vector(C["rad"])
            v = rand_unit(rng)
            if v.z < -0.35 and C.get("under", True): v.z = -v.z * 0.5  # few cards on the underside
            v.normalize(); k = rng.uniform(0.72, 1.0)
            p = c + Vector((v.x * R.x, v.y * R.y, v.z * R.z)) * k
            out = Vector((v.x / R.x, v.y / R.y, v.z / R.z)).normalized()
            d = (out * 0.6 + UP * 0.45 + rand_unit(rng) * 0.35).normalized()
            tg = C.get("tangent", 0.0)  # clipped topiary: cards lie along the shell surface, facing out
            if tg:
                dt = d - out * d.dot(out)
                if dt.length > 1e-4: d = d.lerp(dt.normalized(), tg).normalized()
            p = p - d * size * 0.45
            nrm = orient_normal(rng, d, C.get("flat", 0.0))
            if tg: nrm = nrm.lerp(out, tg)
        s = size * rng.uniform(0.85, 1.15)
        card(bm, uvl, p, d, nrm, s, fold, pick())

def make_lod(name, seed, lod1, full_rings=frozenset()):
    """full_rings: indices (in skeleton order) of tubes meshed with every ring in the lod1_subset LOD1 (set by the
    floating-bark retry below; empty on the first pass)."""
    MERGE_SKIPPED[0] = 0
    branches = build_skeleton(seed)
    sub = CFG.get("lod1_subset") if lod1 else None  # LOD1 = the LOD0 tree thinned in place (no pop at the switch)
    if lod1 and not sub:
        for b in branches:
            keep = list(range(0, len(b.pts) - 1, 2)) + [len(b.pts) - 1]
            b.pts = [b.pts[k] for k in keep]; b.radii = [b.radii[k] for k in keep]
        deep = max(b.depth for b in branches)
        if CFG.get("lod1_mindepth") is not None and deep > CFG["lod1_mindepth"]:
            md = CFG["lod1_mindepth"]  # no twigs, every other branch of the level the LOD1 cards sit on
            branches = [b for b in branches if b.depth < md or getattr(b, "sides", None)] + \
                [b for b in branches if md <= b.depth < deep and not getattr(b, "sides", None)][::2]
        elif deep > 0:  # (a branchless palm keeps all its stems)
            branches = [b for b in branches if b.depth < deep] + [b for b in branches if b.depth == deep][::2]
    if CFG.get("merge"):  # each limb flows into its best-aligned last child: one tube, no tapered spike at the fork
        merge_continuations(branches, CFG["merge"])
    sm = CFG.get("smooth")
    if sm and (not lod1 or sub):  # after the skeleton: child bases and card roots stay where the seed put them
        for b in branches:
            if getattr(b, "merged_into", None) is not None: continue
            if b.depth <= sm.get("depth", 1) and len(b.pts) > 2 and not getattr(b, "sides", None):
                b.pts, b.radii = smooth_path(b.pts, b.radii, math.radians(sm.get("bend", 12)), sm.get("iters", 2))
    if CFG.get("taper"):  # every branch end narrows smoothly to TIP_R over its last 40%: no cut/capped ends
        for b in branches:
            if b.depth == 0 and CFG.get("fork"): continue  # the trunk ends inside its fork limbs, no spear tip
            if getattr(b, "keep", False):  # explicit limb: keeps its end radius, gently rounded by the end cap
                continue
            seg = [(b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1)]
            L = sum(seg); cum = [0.0]
            for x in seg: cum.append(cum[-1] + x)
            # the taper starts beyond the last child fork, so a child's base never sticks out of a thinned parent
            f0 = 0.6
            chain, x = [], getattr(b, "cont", None)
            while x is not None: chain.append(x); x = getattr(x, "cont", None)
            heads = {b.depth + 1} | {x.depth + 1 for x in chain}
            for c in branches:
                if c.depth not in heads or c in chain: continue
                k = min(range(len(b.pts)), key=lambda i: (b.pts[i] - c.pts[0]).length)
                if (b.pts[k] - c.pts[0]).length < b.radii[k] + 0.1: f0 = max(f0, cum[k] / L + 0.08)
            f0 = min(f0, 0.9)
            for i in range(len(b.pts)):
                f = max(0.0, (cum[i] / L - f0) / (1 - f0)) ** 1.5
                b.radii[i] = b.radii[i] * (1 - f) + TIP_R * f
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap"); bm.loops.layers.uv.new("UV2")
    deep = max(b.depth for b in branches)
    S0, S1 = CFG.get("sides", (7, 5, 4)), CFG.get("lod1_sides", (5, 4, 3))
    spans = []  # (skeleton index, first bark face, end) per meshed tube
    for bi, b in enumerate(branches):
        if getattr(b, "merged_into", None) is not None: continue  # its axis is the tail of its parent's tube
        St = S1 if lod1 else S0
        if getattr(b, "sides", None): sides = b.sides
        elif b.depth == 0: sides = St[0]
        elif b.depth < deep or deep == 1: sides = St[1]
        else: sides = St[2]
        full = (b.pts, b.radii)
        if sub and len(b.pts) > 2 and bi not in full_rings:  # every other ring on the tube only; the cards stay rooted on the full axis
            ks = list(range(0, len(b.pts) - 1, 2)) + [len(b.pts) - 1]
            b.pts = [b.pts[k] for k in ks]; b.radii = [b.radii[k] for k in ks]
        f0 = len(bm.faces)
        tube(bm, b, sides, CFG.get("lobe", 0.16), CFG.get("caps", False))  # lobe: trunk cross-section wobble (lumpy base)
        spans.append((bi, f0, len(bm.faces)))
        b.pts, b.radii = full
    if sub and len(full_rings) < len(spans):
        # dropping every other ring cuts curved axes into chords; a child whose base sat on the curve can end up beside
        # the thinned parent tube (floating bark). Mesh those parents with every ring and build this LOD again.
        fl = floating_islands(bm); add = set()
        for isl in fl:
            bi = next(i for i, a, e in spans if a <= isl["faces"][0] < e); p0 = branches[bi].pts[0]
            others = [(axis_gap(p0, branches[j].pts, branches[j].radii), j) for j, _, _ in spans if j != bi]
            if others: add.add(min(others)[1])
        if add - full_rings:
            bm.free(); bpy.data.meshes.remove(me)
            return make_lod(name, seed, lod1, full_rings | add)
    FULL_RINGS[name] = len(full_rings); SKIPS[name] = MERGE_SKIPPED[0]
    C = CFG["crown"]
    if sub:  # same count, size and draws as LOD0; sprig_crown builds a subset, larger, unfolded
        cards = crown(bm, uvl, branches, random.Random(seed + 11), C["count"], C.get("size", 1.0), 0.0, False, sub)
    else:
        cards = crown(bm, uvl, branches, random.Random(seed + 11),
              int(C["count"] * (CFG.get("lod1_cards", 0.6) if lod1 else 1.0)),
              C.get("size", 1.0) * (CFG.get("lod1_size", 1.35) if lod1 else 1.0), 0.0 if lod1 else C.get("fold", 0.0), lod1)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    cylinder_uvs(ob)
    M = CFG.get("bark_macro")
    if M:  # low-frequency value variation on the bark (vertex colour), white on the leaves
        ca = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
        for p in me.polygons:
            for li, vi in zip(p.loop_indices, p.vertices):
                if p.material_index == 0:
                    q = me.vertices[vi].co / M["scale"]
                    n = noise.noise(q) * 0.65 + noise.noise(q * 2.7 + Vector((5.2, 1.3, 7.7))) * 0.35
                    v = max(0.0, min(1.0, 1.0 - M["amount"] * (0.5 + 0.5 * n)))
                    ca.data[li].color = (v, v * 1.01, v * 0.97, 1.0)
                else:
                    ca.data[li].color = (1.0, 1.0, 1.0, 1.0)
    SKELETONS[name] = (branches, cards or [])
    ob.data.materials.append(mat_bark); ob.data.materials.append(mat_leaf)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    me.uv_layers.active = me.uv_layers["UV2"]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    me.uv_layers.active = me.uv_layers["UVMap"]
    for p in me.polygons: p.use_smooth = p.material_index == 0
    ob.select_set(False); return ob

def pick_seed():
    best = None
    for sd in range(1, 60):
        br = build_skeleton(sd)
        deep = max(b.depth for b in br)
        tips = [b.pts[-1] for b in br if b.depth == deep]
        xs = [t.x for t in tips]; ys = [t.y for t in tips]; zs = [t.z for t in tips]
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        w = (max(xs) - min(xs) + max(ys) - min(ys)) / 2
        lowest = min((p.z for b in br if b.depth >= 1 for p in b.pts), default=0.0)
        score = math.hypot(cx, cy) + abs(w - CFG["width"] * 0.8) * 0.5 + abs(max(zs) - CFG["height"] * 0.92) + max(0, -lowest) * 5
        if best is None or score < best[0]: best = (score, sd)
    return best[1]

# --------------------------------------------------------------------------- materials
bpy.ops.wm.read_factory_settings(use_empty=True)
def img(n, cs='sRGB'):
    i = bpy.data.images.load(TEX + n); i.colorspace_settings.name = cs; return i
mat_bark = bpy.data.materials.new(f"{BARKN}_Bark"); mat_bark.use_nodes = True
nt = mat_bark.node_tree; bsdf = nt.nodes["Principled BSDF"]
t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(f"{BARKN}_Bark_Albedo.png")
if CFG.get("bark_macro"):  # preview the vertex-colour macro variation the Unity bark shader multiplies in
    vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1.0
    sock = lambda socks, n: next(x for x in socks if x.name == n and x.type == 'RGBA')  # Mix has float/vector/colour twins
    nt.links.new(t.outputs[0], sock(mx.inputs, "A")); nt.links.new(vc.outputs[0], sock(mx.inputs, "B"))
    nt.links.new(sock(mx.outputs, "Result"), bsdf.inputs["Base Color"])
else:
    nt.links.new(t.outputs[0], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.85
nm = nt.nodes.new("ShaderNodeNormalMap"); tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img(f"{BARKN}_Bark_Normal.png", 'Non-Color')
nt.links.new(tn.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], bsdf.inputs["Normal"])
mat_leaf = bpy.data.materials.new(f"{TEXN}_Leaves"); mat_leaf.use_nodes = True
nt = mat_leaf.node_tree; bsdf = nt.nodes["Principled BSDF"]
t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(f"{TEXN}_Leaves_RGBA.png")
nt.links.new(t.outputs[0], bsdf.inputs["Base Color"]); nt.links.new(t.outputs[1], bsdf.inputs["Alpha"])
bsdf.inputs["Roughness"].default_value = 0.6; mat_leaf.use_backface_culling = False
if CFG.get("leaf_cluster"):  # matte foliage (matches FoliageCutout _Matte): no specular sheen or rim
    bsdf.inputs["Roughness"].default_value = 1.0; bsdf.inputs["Specular IOR Level"].default_value = 0.0

SKELETONS = {}
FULL_RINGS, SKIPS = {}, {}  # per LOD name: tubes kept at every ring (LOD1 retry), merges skipped
SEED = CFG["seed"] or pick_seed()
tree_uv.OFFSET_SEED = SEED if CFG.get("bark_tile_min") is not None else None
# Default: one LOD0 mesh named <Species>_Tree. LOD1 (fewer sides, half the deepest twigs, 35 % larger
# cards, 60 % of the count, no fold) only with --lod1, for very large worlds.
lod0 = make_lod(f"{NAME}_Tree" + ("_LOD0" if LOD1 else ""), SEED, False)
LODS = [lod0] + ([make_lod(f"{NAME}_Tree_LOD1", SEED, True)] if LOD1 else [])

def tris(o, mi=None): return sum(len(p.vertices) - 2 for p in o.data.polygons if mi is None or p.material_index == mi)
def bounds(o):
    vs = [v.co for v in o.data.vertices]
    return [round(min(v[i] for v in vs), 2) for i in range(3)], [round(max(v[i] for v in vs), 2) for i in range(3)]
def coplanar_pairs(obj, eps=1e-4):
    me = obj.data; hits = 0
    faces = [(p.normal.normalized(), p.center.copy(), [me.vertices[i].co.copy() for i in p.vertices]) for p in me.polygons if p.material_index == 0]
    for (n1, c1, v1), (n2, c2, v2) in itertools.combinations(faces, 2):
        if abs(n1.dot(n2)) < 0.999 or abs(n1.dot(c2 - c1)) > eps: continue
        u = n1.orthogonal().normalized(); w = n1.cross(u)
        a = [(p.dot(u), p.dot(w)) for p in v1]; b = [(p.dot(u), p.dot(w)) for p in v2]
        tol = 1e-3
        if (max(x for x, _ in a) < min(x for x, _ in b) + tol or min(x for x, _ in a) > max(x for x, _ in b) - tol or
            max(y for _, y in a) < min(y for _, y in b) + tol or min(y for _, y in a) > max(y for _, y in b) - tol): continue
        hits += 1
    return hits
print("STAT", NAME, "seed", SEED)
for o in LODS:
    print("STAT", o.name, "tris", tris(o), "bark", tris(o, 0), "leaf", tris(o, 1), "bounds", bounds(o))
print("STAT coplanar-overlapping bark pairs LOD0:", coplanar_pairs(lod0))
def attach_report(o):
    """Measured on the final mesh: each card's attach point (its atlas stem base mapped through the
    card's own vertices) against the nearest branch-axis segment and that segment's radius."""
    branches, cards = SKELETONS[o.name]
    if not cards: return None
    vs = o.data.vertices; dist, bad = [], 0
    for first, grid, (au, av), _, _ in cards:
        P = {g: vs[first + k].co for k, g in enumerate(grid)}
        bot = P[(0, 0)].lerp(P[(1, 0)], au); top = P[(0, 1)].lerp(P[(1, 1)], au)
        if (.5, 0) in P:  # folded card: piecewise through the mid column
            bot = P[(0, 0)].lerp(P[(.5, 0)], au * 2) if au < .5 else P[(.5, 0)].lerp(P[(1, 0)], au * 2 - 1)
            top = P[(0, 1)].lerp(P[(.5, 1)], au * 2) if au < .5 else P[(.5, 1)].lerp(P[(1, 1)], au * 2 - 1)
        A = bot.lerp(top, av)
        best = (1e9, 0.0)
        for b in branches:
            for i in range(len(b.pts) - 1):
                p0, p1 = b.pts[i], b.pts[i + 1]; seg = p1 - p0
                t = max(0.0, min(1.0, (A - p0).dot(seg) / max(seg.length_squared, 1e-12)))
                dd = (A - (p0 + seg * t)).length
                if dd < best[0]: best = (dd, b.radii[i] + (b.radii[i + 1] - b.radii[i]) * t)
        dist.append(best[0]); bad += best[0] > max(best[1], 1e-4)
    tips = [b for b in terminal_ends(branches) if b.pts[-1].z >= CFG["crown"].get("minz", 0.0) * 0.8]
    rooted = {id(c[3]) for c in cards if c[4] >= 0.95}
    return dict(cards=len(cards), attach_max_mm=round(max(dist) * 1000, 3),
                attach_median_mm=round(statistics.median(dist) * 1000, 3), out_of_tolerance=bad,
                tips=len(tips), tips_uncovered=sum(id(b) not in rooted for b in tips))

def limb_report(o):
    branches, _ = SKELETONS[o.name]
    L = lambda b: sum((b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1))
    by = {}
    for b in branches: by.setdefault(b.depth, []).append(L(b))
    leaf = [v.co for p in o.data.polygons if p.material_index == 1 for v in (o.data.vertices[i] for i in p.vertices)]
    return dict(mean_len_by_depth={d: round(sum(v) / len(v), 2) for d, v in sorted(by.items())},
                crown_radius=round(max((c.x * c.x + c.y * c.y) ** 0.5 for c in leaf), 2) if leaf else None)
def tip_face_report(o):
    import statistics
    branches, _ = SKELETONS[o.name]
    leaf = [p.area for p in o.data.polygons if p.material_index == 1]
    med = statistics.median(leaf)
    open_edges = sum(1 for e in o.data.edges if e.is_loose is False and
                     all(o.data.vertices[v].co.z > 0.01 for v in e.vertices)) if False else None
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(o.data)
    open_rings = sum(1 for e in bm.edges if e.is_boundary and all(f.material_index == 0 for f in e.link_faces)
                     and min(v.co.z for v in e.verts) > 0.01)
    bm.free()
    return dict(open_bark_edges_above_ground=open_rings, ends_radius_over_5mm=sum(1 for b in branches if b.radii[-1] > 0.005),
                max_end_radius_mm=round(1000 * max(b.radii[-1] for b in branches), 1),
                leaf_faces_over_4x_median_area=sum(1 for a in leaf if a > 4 * med))
for o in LODS:
    print("STAT", o.name, "tips/faces", tip_face_report(o))
print("STAT", lod0.name, "limbs", limb_report(lod0))
for o in LODS:
    print("STAT", o.name, "bark stretch (min, median, max, max/min)", stretch_stats(o), "attach", attach_report(o))
for o in LODS:
    before = leaf_normal_spread(o)
    dims = transfer_crown_normals(o, CFG["proxy"], cluster=CFG.get("leaf_cluster"), crown_mix=CFG.get("leaf_crown_mix", 0.35))
    print("STAT", o.name, "proxy", CFG["proxy"], dims, "leaf normal |dot| before", before, "after", leaf_normal_spread(o))
for o in LODS:  # bark islands not connected to the ground-rooted bark (buried base cones count as connected)
    print("STAT", o.name, "floating_bark_components", *floating_bark_components(o))
    if SKIPS.get(o.name): print("STAT", o.name, "merges skipped (stub carries another child):", SKIPS[o.name])
    if FULL_RINGS.get(o.name): print("STAT", o.name, "tubes kept at every ring (thinned tube left bark floating):", FULL_RINGS[o.name])

bpy.ops.object.select_all(action='DESELECT')
for o in LODS: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT + f"{NAME}_Tree.fbx", use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
    axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='OFF', path_mode='STRIP',
    use_mesh_modifiers=True, add_leaf_bones=False, object_types={'MESH'})
bpy.ops.wm.save_as_mainfile(filepath=SRC + f"{NAME}_Tree.blend", relative_remap=False)  # absolute texture paths: the .blend can be copied (stage -> final) without losing them

if QA:  # internal check only
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
    sc.cycles.transparent_max_bounces = 128  # stacked alpha cards: the default 8 renders black leaf patches
    sc.render.resolution_x, sc.render.resolution_y = 720, 900
    world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.58, 0.62, 1)
    sun_d = bpy.data.lights.new("sun", 'SUN'); sun_d.energy = 3; sun = bpy.data.objects.new("sun", sun_d); sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    for o in LODS[1:]: o.hide_render = True
    H = max(v.co.z for v in lod0.data.vertices)
    cam_d = bpy.data.cameras.new("c"); cam_d.lens = 35; cam = bpy.data.objects.new("c", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0, -H * 2.0, 1.6); cam.rotation_euler = (Vector((0, 0, H * 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = QA; bpy.ops.render.render(write_still=True)
print("FAMILY_OK", NAME)

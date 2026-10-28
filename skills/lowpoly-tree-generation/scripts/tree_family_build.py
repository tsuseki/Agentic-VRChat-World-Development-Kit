# Headless low-poly tree builder: skeleton -> tube bark -> leaf cards -> UVs -> crown normals -> FBX.
#   blender -b --factory-startup -P tree_family_build.py -- <Species> --tex <dir> --out <dir>
#           [--blend <dir>] [--lod1 [--lods]] [--qa <png>] [--config <species.py>]
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
#   flare=dict(r=1.3, h=0.35, skirt=0.05, steps=2)   root flare: ground-rooted stems widen to r x at z=0 over h m
#                                    (<= 30 % of the stem; `steps` rings), plus a closed skirt ring `skirt` m below ground
#       opt-in skirt_axis=s: the skirt runs on along the stem's first segment instead of straight down (no kink at
#       the ground on leaning stems when the base is seen without terrain); s = the pack scale the mesh ships at
#       (horizontal offset / s, because the pack scales x/y but keeps underground depths). Off = identical builds.
#   side=[dict(n, z=(lo,hi), len, ang, r, tip, gnarl, up)]  extra trunk limbs/stubs at given heights (no children)
#   vines=dict(count, size, z=(lo,hi))   hanging sprig cards under depth>=1 branches (epiphytes / draped foliage)
#   low_tips=dict(min=3, n=4, reach=1.0, size=0.6, ground=0.1, cut=0.3)   bare low limbs (sprig): every terminal limb
#       chain carrying fewer than `min` cards gets `n` more over its outer `reach` m (one at the tip), card length
#       `size`, kept above `ground`; chains lying entirely below `cut` m (ground limbs, never leafy) are not meshed.
#       Added after every other card with its own random sequence: no other card moves. Off = identical builds.
#   crown roll_tilt=(lo, hi) (sprig, opt-in): each card is rolled about its own axis so its plane stands lo..hi deg
#       (random sign) off the plane through the axis and the horizontal; replaces `flat`'s face-to-sky roll (flat still
#       levels the direction). For low mats whose face-up cards read as flat rosettes. Own random sequence: card
#       positions and directions are those of the plain build until the ground keep-out shrinks or skips a rolled
#       card differently. Off = identical builds.
#   crown tip_upbias=<float> (sprig, opt-in; bamboo): the card on every ground-stem tip uses this upbias instead of
#       `upbias` (e.g. +0.4 under a hanging -1.8 crown), so the culm tip carries its own rising spray instead of a bare
#       whip above the crown. crown tip_upbias_all=True (opt-in): every terminal tip's card uses it (weeping mound:
#       low drooping twig ends get a level tip card that clears the ground instead of being skipped, tips_uncovered).
#       No extra random draws. Off = identical builds.
#   hug=dict(c=(x, y, z), rad=(rx, ry, rz), at=0.92, depth=(0, 0)) (opt-in; clipped hedges / balls): branches of these
#       depths slide along the ellipsoid level surface `at` of (c, rad) instead of growing through it: once a branch
#       reaches that surface each next segment keeps only its tangential direction and its end is put back on the
#       surface, so ground canes run up and over the inside of a clipped shell and every sprig card rooted on them sits
#       just under the face (cheap leaf carriers for a dense clipped surface). No extra random draws: off = identical.
#   crown surface=dict(c=(x, y, z), rad=(rx, ry, rz), chord=1.0, max_up=None, skin=0) (sprig, opt-in; clipped topiary): each
#       card keeps its root on the twig but lies along the level surface through that root of the ellipsoid (c, rad),
#       facing out, dipped by `chord` x the angle that brings its far end back onto that surface (osculating circle, <= 40 deg);
#       max_up (deg) rolls it about its axis just enough that its face stays >= max_up off horizontal. Use without
#       roll_tilt (it would override the roll). c="root": the ellipsoid is centred on the root of each card's own twig
#       (+ lift m up), one small dome per twig cluster (cloud-pruned pads). skin=k (opt-in, < 1): the root moves k x the
#       twig radius out along that surface normal, so the card lies on the outer side of a twig running along the face
#       instead of halving it (still inside the attach tolerance). No extra random draws: off = identical builds.
#   crown cells=[i, ...] (sprig/bamboo, opt-in): cards draw only these cells of <tex>_Leaves_Cards.json (one atlas;
#       e.g. a subset of sprays per variant). Every leaf cell is an open spray, never a dense leaf patch (user
#       2026-10-27). Same single rng.choice per card: off = identical builds.
#   crown cell_scale=True (sprig, opt-in): each card's length x its drawn cell's Cards.json "scale" (default 1), so a
#       cell painted with bigger leaves builds the same leaf size in metres as the others (Masaki cell 1, 2026-10-27).
#       No extra random draws: off = identical builds.
#   crown roles=dict(frac=0.2, low=True) (sprig, opt-in; needs Cards.json cells with "role": "full" | "lateral" |
#       "shoot" | "sprig", optional "scale" = card length multiplier, default 1): a dry first pass on a copy of the
#       random state finds every card's far end; the cards that stick out of the crown (the `frac` share of tip and
#       main cards furthest out of the crown ellipsoid, plus every low_tips card if `low`) show a lateral/shoot/sprig
#       cell, the interior and fill cards a "full" cell (per-card own sequence). Same cards, places, directions and
#       count; a role cell that would hit `clear`/`ground` falls back to the drawn cell. Prints STAT crown roles.
#       roles group=<k> (opt-in): every card rooted on the same branch within k x the median card length of an "out"
#       card's root (the whole cluster on a protruding tip, low limb chains) turns "out" too, and the out cards of each
#       branch take the lateral/shoot/sprig cells in turn along the branch (no two neighbours alike) instead of the
#       per-card draw. Off = identical builds.
#       roles top=<k> / above=<m> (opt-in, varied cells on the rim and underside only): a card may turn "out" (seed,
#       low_tips or group member) only if its far end lies at or below zc + k x rz of the crown ellipsoid (k 0 = the
#       lower half: a flat umbrella's top keeps full cells) and its root at or above `above` m (low limbs keep full
#       cells). `frac` still counts over all tip and main cards. Off = identical builds (StonePine 2026-10-27).
#       roles bare=<m> (opt-in): a card with more than m metres of bare limb behind its root (bare_behind: back along
#       its limb chain into the parent limbs to the nearest other card root or leafy side branch; trunks not counted)
#       keeps a full cell; frac takes the next eligible card. Off = identical builds (AleppoPineLean 2026-10-27).
#   crown floor_base=True (sprig, opt-in): no card hangs below the base of its limb (where its merged chain leaves
#       its parent) towards the trunk: a card whose lowest corner is under that base and nearer the trunk axis than its
#       root is levelled (heading kept, tip not below its root) and laid face up, then shrunk (x0.75, up to 5 times) or
#       skipped until no corner is below min(base, root). No random draws, but a skipped card is redrawn (later cards
#       move). Prints STAT floor_base. Off = identical builds (StonePineYoung pendant cards by the trunk, 2026-10-27).
#   crown mirror=True (sprig, opt-in): about half the cards (per-card own sequence) show their cell U-mirrored; the
#       mirrored attach point stays on the branch axis. Off (both) = identical builds.
#   crown max_rise=<deg> (sprig, opt-in; weeping mounds): a card whose axis rises more than max_rise deg above
#       horizontal is lowered to max_rise, keeping its heading (0: every card tip-out or tip-down, the willow rule).
#       Applied after `flat`, before surface/roll_tilt. No extra random draws: off = identical builds.
#   crown max_fall=<deg> (sprig, opt-in): likewise a card whose tip falls more than max_fall deg below horizontal is
#       raised to -max_fall (55: no card within 35 deg of hanging vertical; an edge-on hanging card reads as a
#       stippled vertical stripe). Off = identical builds.
#   crown fill up=0.6, minz=<crown minz> (opt-in): the fill cards' up lean (d*0.4 + to_axis*inward + UP*up; < 0 leans
#       them down over the limbs) and the lowest fill root. Defaults = the old fixed values: off = identical builds.
#   low_tips out=(lo, hi) (opt-in): each low_tips card is re-aimed tip-out: heading = radial from the trunk + its own
#       drawn heading, elevation lo..hi deg (own random sequence 7937), so no low card hangs vertically (an edge-on
#       hanging card reads as a stippled vertical stripe). Off = identical builds.
#   crown crest=dict(n=80, size=1.4, cells=[0, 1, 2], step=0.25, cell=0.6, band=0.3, zmin=0.5, space=0.55,
#       rise=(-5, 20), both=True, face_up=(20, 50), out=0.15, mindepth=1, seed=7993) (sprig, opt-in; weeping crowns):
#       every card of a hanging crown hangs below its root, so the top of each arching limb stays bare and the crown
#       reads outlined by wire (BoothAssets SakuraWeeping, JP promo thumbnail). Crest points = limb samples (every
#       `step` m on depth >= mindepth) within `band` m of the highest limb point of their `cell` m xy grid square and
#       above zmin x height; highest first, at least `space` m apart, at most n. Each gets one spray card rooted on the
#       axis, lying along the limb (either way if `both`, `rise` deg above horizontal, + `out` x the radial) in the
#       limb's vertical plane tilted `face_up` deg to face out and up, so its blossom covers the crest from the side and
#       from above without standing up out of the dome. Placed last with their own random sequence: every other card
#       is unchanged. Off = identical builds.
#       follow=True: the spray is first turned outward (away from the trunk), and `rise` (use <= 0) is measured from the
#       limb tangent's own slope clamped to <= horizontal, so sprays drape out and down along the arch, never above it.
#   declip=dict(script=<declip.py>, margin=0.03, fuse=flare h, max_tilt=35, export=<dir>, apply=True)   bark-through-bark fix: after
#       merge/smooth/taper, limbs whose meshed tubes clash are tilted apart rigidly about their bases (fork zones and the
#       ground-stem root crown below `fuse` m are allowed overlap); see BoothAssets/Tools/trees/declip.py. Off = identical builds.
#   bury=1.5 (opt-in): depth of the cone that closes a child's base ring, behind the ring x its base radius (min 2 cm).
#       Thick limbs on a thin lobed 6-sided trunk poke the default cone out of the trunk's far side as a strap or
#       faceted wedge (BoothAssets BlackPine BP6); 0.25 keeps it inside. Mesh only, no draws: off = identical builds.
#   base_clamp=True (default; False = the old builds): after the tubes are meshed, `base_cones.clamp` pulls every child's
#       base cone (apex depth) and any ring corner that leaves the other tubes by > 2 mm back inside the parent tube,
#       using the parent's actual meshed ring (lobe, 4/3 sides, taper, merge, declip): no light wedge of cone faces on the
#       trunk's far side (BoothAssets olives 2026-10-23). Prints `STAT <name> base cones clamped N` only when it moves
#       something, so trees that never poked stay geometry-identical (the Lightmap UV is re-laid from the UVMap charts).
#   base_fix=True (default with base_clamp; False = the builds before 2026-10-26): after the clamp, `base_cones.contacts`
#       flags child limbs whose base floats > 1 mm clear of every other tube, and flat caps (cones the clamp closed flush)
#       showing >= 0.1 cm2 outside the other tubes. The flagged limb's MESHED axis (skeleton, cards, children unchanged)
#       gets its base on the parent's meshed axis and, for a flat cap, a base ring narrowed to 0.85^n x its radius that
#       widens back over 3 radii (n = passes it still shows, <= 4); the LOD is meshed again. Prints `STAT <name> base fix
#       moved N narrowed M passes P left [...]` only when it fires: trees without the defect stay geometry-identical.
#   levels[i] root_out=<k> (opt-in): every limb of that level is shifted rigidly k x the parent radius out along its own
#       radial (shape, noise and draws unchanged), so a thick limb (r 0.55 x trunk) leaves the trunk wall within the
#       trunk radius instead of running ~1.2 trunk radii inside it (BlackPine BP6, k 0.35 with bury 0.25: base ring
#       still inside the trunk). Its children and cards move with it. Off = identical builds.
#   lod1_cards (0.6), lod1_size (1.35)   LOD1 card count and size factors
#   lod1_subset=dict(keep=1.0, grow=1.0)   LOD1 = LOD0 thinned in place instead of rebuilt: same skeleton and card
#       draws, every other tube ring, lod1_sides, all tip cards plus a `keep` share of the rest, `grow` x larger and
#       unfolded. keep=1, grow=1 (bark-only LOD1) keeps the silhouette within a few cm; thinning cards opens holes.
#       Every LOD (always on): a card whose attach point lies farther than the tube radius from the axis of the tube
#       actually meshed is moved rigidly onto that axis, so its painted twig still leaves the 3D bark (snap_cards_to_bark;
#       0 tris). LOD1 every-other-ring chords hang off the full axis by up to ~45 cm on long curved limbs; on LOD0 only
#       cards of merged children whose head axis was smoothed move (a few cm).
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
#   lods=[dict(rings, sides, grow, maxdepth | drop, min_r), ...] (--lods; default LOD_LEVELS)   far LODGroup levels
#       <Species>_Tree_LOD2, _LOD3 built from the LOD1's skeleton and card draws (see make_lod lv); the hidden-card cull
#       (BoothAssets lod1_cull_cards.py --lod N --keep-cards K) then thins their cards by visibility.
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
#       and SKILL.md. levels=[] allowed (no branches); suckers = `side` limbs at the trunk base (each its own head),
#       rosette `head_pow` (opt-in) shrinks small heads' frond counts (x sc^head_pow) and zones. crown atlas=True|[cells] (twig/ellipsoid/spindle): each card
#       shows one cell of <tex>_Leaves_Cards.json; tangent (0..1, ellipsoid): cards lie along the shell (topiary)
import bpy, bmesh, math, random, itertools, sys, os
from mathutils import Vector, Quaternion, noise

argv = sys.argv[sys.argv.index("--") + 1:]
def _opt(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
NAME = argv[0]; LOD1 = "--lod1" in argv; LODS_ON = "--lods" in argv; QA = _opt("--qa"); QA = QA and os.path.abspath(QA)  # Blender resolves relative render paths oddly
TEXDIR = os.path.abspath(_opt("--tex", ".")) + "/"
OUT = os.path.abspath(_opt("--out", ".")) + "/"
SRC = os.path.abspath(_opt("--blend", OUT)) + "/"
os.makedirs(SRC, exist_ok=True); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree_normals import transfer_crown_normals, leaf_normal_spread
from tree_checks import floating_bark_components, floating_islands
import base_cones
from tree_uv import cylinder_uvs, stretch_stats
import lightmap_uv
import json, statistics
UP = Vector((0, 0, 1))
# --lods far levels (LODGroup LOD1 / LOD2 of a pack whose LOD0 is this builder's culled LOD1): lighter bark (every
# `rings`-th ring, `sides`), small branches dropped, every card kept `grow` x larger about its twig base, unfolded.
LOD_LEVELS = [dict(rings=2, sides=(4, 3, 3), drop=1, grow=1.15),
              dict(rings=3, sides=(4, 3, 3), maxdepth=1, min_r=0.3, grow=1.4)]
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
if CFG.get("flare"):  # flared stem bases keep the plain stem's wraps and repeat (no texture shear over the flare)
    tree_uv.FLARE_H = CFG["flare"].get("h", 0.35)
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
        HG = CFG.get("hug")
        if HG and HG.get("depth", (0, 0))[0] <= depth <= HG.get("depth", (0, 0))[1]:  # opt-in: slide along the shell
            c, R, at = Vector(HG["c"]), HG["rad"], HG.get("at", 0.92)
            rho = lambda x: Vector(((x.x - c.x) / R[0], (x.y - c.y) / R[1], (x.z - c.z) / R[2])).length
            q = pts[-1] - c
            g = Vector((q.x / R[0] ** 2, q.y / R[1] ** 2, q.z / R[2] ** 2))
            if rho(pts[-1]) >= at * 0.98 and g.length > 1e-9 and d.dot(g) > 0:  # on the shell: tangential step only
                n = g.normalized(); t = d - n * d.dot(n)
                if t.length > 1e-6: d = t.normalized(); p = pts[-1] + d * (length / segs)
            if rho(p) > at:  # back onto the level surface (radially from c)
                p = c + (p - c) * (at / rho(p)); d = (p - pts[-1]).normalized()
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

def stem_layout_points(SL, cnt, seed):
    """CFG stem_layout (opt-in): cnt stem bases scattered over an area with its own random sequence, at least `gap` m
    apart. kind "disc" (r), "ellipse" (rx, ry) or "strip" (w along x, d along y; a hedge/screen row). Sorted by
    distance from the origin, so stem 0 (the full-size one) stands in the middle. Also read by build_skeleton: `rim`
    (m, default 1) = distance at which a stem reaches its full lean, `lean_min` (0.3) = lean share at the centre;
    opt-in `axis_out` (m): stems lean out from the centre segment x in [-axis_out, axis_out] (y = 0) instead of the
    centre point, so a strip fans to both sides along its whole length (no bare middle); off = identical builds."""
    rng = random.Random(seed * 101 + 7); pts = []; gap = SL.get("gap", 0.12); kind = SL.get("kind", "disc")
    for _ in range(cnt * 400):
        if len(pts) == cnt: break
        if kind == "strip":
            p = Vector((rng.uniform(-0.5, 0.5) * SL["w"], rng.uniform(-0.5, 0.5) * SL["d"], 0.0))
        else:
            a = rng.uniform(0, 2 * math.pi); s = math.sqrt(rng.random())
            rx, ry = (SL["r"], SL["r"]) if kind == "disc" else (SL["rx"], SL["ry"])
            p = Vector((math.cos(a) * s * rx, math.sin(a) * s * ry, 0.0))
        if all((p - q).length >= gap for q in pts): pts.append(p)
    assert len(pts) == cnt, f"stem_layout: only {len(pts)} of {cnt} bases fit at gap {gap}"
    return sorted(pts, key=lambda p: p.length)

def build_skeleton(seed):
    rng = random.Random(seed); out = []
    cnt, lean, L, r0, r1, gn, spread = CFG["stems"]
    parents = []
    SL = CFG.get("stem_layout")  # opt-in (bamboo groves, screens): stem bases scattered over an area, not on a ring
    if SL: SLP = stem_layout_points(SL, cnt, seed)
    for k in range(cnt):
        if "lean_dir" in CFG:  # all stems lean one way, fanned around that azimuth
            az = CFG["lean_dir"] + (k - (cnt - 1) / 2) * CFG.get("lean_fan", 0.5) + rng.uniform(-0.15, 0.15)
        else:
            az = 2 * math.pi * k / cnt + rng.uniform(-0.3, 0.3)
        le = rng.uniform(*lean) if cnt > 1 else rng.uniform(*lean)
        d = Vector((math.cos(az) * le, math.sin(az) * le, 1.0))
        base = Vector((math.cos(az) * spread, math.sin(az) * spread, 0.0))
        if SL:  # base from the layout; lean outward from the centre (or lean_dir), scaled up toward the rim
            base = SLP[k]; rad = Vector((base.x, base.y, 0.0)); rim = SL.get("rim", 1.0)
            if SL.get("axis_out") is not None:  # opt-in: out from the centre segment, not the centre point
                rad.x -= max(-SL["axis_out"], min(SL["axis_out"], base.x))
            if "lean_dir" not in CFG and rad.length > 1e-3: az = math.atan2(rad.y, rad.x) + (az - 2 * math.pi * k / cnt)
            le *= SL.get("lean_min", 0.3) + (1.0 - SL.get("lean_min", 0.3)) * min(1.0, rad.length / rim)
            d = Vector((math.cos(az) * le, math.sin(az) * le, 1.0))
        sc = 1.0 if k == 0 or cnt < 4 else rng.uniform(0.7, 1.0)
        parents.append(grow(base, d, rng.uniform(*L) * sc, r0 * sc, r1 * sc, CFG.get("stem_segs", 6), 0, out, gn,
                            CFG.get("bend", 0.0), seed + k, up_end=CFG.get("bend_end")))  # bend_end: stem bend ramps to it (nodding tips)
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
                if c: c.par = trunk; made.append(c)
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
                    c.par = trunk; c.radii[-1] = X["r"][1]; c.keep = True  # no taper to a tip: the pod rope is lashed at its end
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
                    hl.par = trunk
                    for j in range(Sc.get("twigs", 7)):  # hanging twigs through the box
                        p0 = point_at(hl, rng.uniform(0.35, 1.0))[0] + f * rng.uniform(-dd / 2, dd / 2) * 0.6
                        tw = grow(p0, (-UP + rand_unit(rng) * 0.15).normalized(), h + 0.2 - (ztop - 0.4 - p0.z) * 0, 0.03,
                                  TIP_R, 3, 3, out, 0.1, 0.0, seed * 29 + j + k * 31, keep_out=False)
                        if tw: tw.screen = k; tw.par = hl
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
                if c: c.par = trunk; nxt.append(c)
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
                if c and P.get("root_out"):  # opt-in: the whole limb shifted rigidly root_out x parent radius out along
                    rad = cd - d * cd.dot(d)  # its own radial (same shape and noise), so a thick limb clears the parent wall sooner
                    if rad.length > 1e-6:
                        sh = rad.normalized() * r * P["root_out"]; c.pts = [q + sh for q in c.pts]
                if c: c.par = b; nxt.append(c)
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

def flare_axis(br):
    """CFG flare=dict(r=1.3, h=0.35, skirt=0.05, steps=2): the ground ring of a ground-rooted stem (depth 0, base at
    z=0) widens to r x its radius, easing back (quadratic, concave) to the plain radius h m up the axis (h at most 30 %
    of the stem's length, so short bush stems are not flared end to end), with rings added at h*j/steps
    (j = 1..steps) unless a skeleton point sits within 2 cm; one closed skirt ring sits `skirt` m below z=0.
    Mesh only: the skeleton (cards, attach, merges) is unchanged. Returns (pts, radii, skirt depth or None, h)."""
    F = CFG.get("flare")
    if not F or br.depth != 0 or br.pts[0].z > 0.05 or len(br.pts) < 2: return br.pts, br.radii, None, 0.0
    fr, sk, n = F.get("r", 1.3), F.get("skirt", 0.05), F.get("steps", 2)
    h = min(F.get("h", 0.35), 0.3 * sum((br.pts[i + 1] - br.pts[i]).length for i in range(len(br.pts) - 1)))
    ease = lambda s: 1.0 + (fr - 1.0) * max(0.0, 1.0 - s / h) ** 2
    pts, radii = [br.pts[0].copy()], [br.radii[0] * fr]; acc = 0.0
    for i in range(1, len(br.pts)):
        a, b = br.pts[i - 1], br.pts[i]; L = (b - a).length
        for j in range(1, n + 1):
            s = h * j / n
            if acc + 0.02 < s < acc + L - 0.02:
                t = (s - acc) / L
                pts.append(a.lerp(b, t)); radii.append((br.radii[i - 1] + (br.radii[i] - br.radii[i - 1]) * t) * ease(s))
        acc += L
        pts.append(b.copy()); radii.append(br.radii[i] * ease(acc))
    sp = pts[0] - Vector((0, 0, sk))
    sa = F.get("skirt_axis")
    if sa:  # opt-in: skirt on the stem axis (offset / ship scale: the pack keeps underground depths, scales x/y)
        d0 = br.pts[1] - br.pts[0]
        if d0.z > 1e-4: sp = pts[0] - Vector((d0.x / d0.z * sk / sa, d0.y / d0.z * sk / sa, sk))
    return [sp] + pts, [radii[0]] + radii, sk, h

def tube(bm, br, sides, lobe_amt, cap):
    rings = []; acc = 0.0; prev_n = None
    pts, radii, skirt, fh = flare_axis(br)
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = (pts[i + 1] - p).normalized() if i < len(pts) - 1 else (p - pts[i - 1]).normalized()
        if i > 0: acc += (p - pts[i - 1]).length
        if skirt is not None:  # flare rings tilt from horizontal at the ground (no flattened ellipse, no squashed
            s0 = (pts[1] - pts[0]).length if CFG["flare"].get("skirt_axis") else skirt  # skirt_axis: slanted skirt length
            w = min(1.0, max(0.0, (acc - s0) / max(fh, 1e-3)))  # quads on a leaning stem) to the axis direction at h
            t = (UP * (1.0 - w) + t * w).normalized()
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
            if br.depth == 0 and i == (1 if skirt is not None else 0): q.z = 0.0
            elif i == 0 and skirt is not None: q.z = -skirt
            ring.append(bm.verts.new(q))
        rings.append((ring, acc))
    for (r0, v0), (r1, v1) in zip(rings, rings[1:]):
        for s in range(sides):
            s2 = (s + 1) % sides
            f = bm.faces.new((r0[s], r0[s2], r1[s2], r1[s])); f.material_index = 0
    if skirt is not None:  # flat disc closing the skirt ring below ground: no open bottom edge
        ring = rings[0][0]; c = bm.verts.new(Vector((pts[0].x, pts[0].y, -skirt)))
        for s in range(sides):
            f = bm.faces.new((ring[(s + 1) % sides], ring[s], c)); f.material_index = 0
    rosette = CFG["crown"]["mode"] == "rosette"  # palm suckers (side limbs, no taper) need the buried base cone too
    if br.depth > 0 and (CFG.get("taper") or rosette):  # base ring closed by a cone buried in the parent: no open fork ring
        ring = rings[0][0]
        t = (br.pts[1] - br.pts[0]).normalized()
        # opt-in `bury` (default 1.5): apex depth behind the base ring x its radius. A thick limb on a thin lobed trunk
        # pokes the default cone out of the trunk's far side (a strap / faceted wedge); 0.25 keeps it inside the trunk
        q = br.pts[0] - t * max(br.radii[0] * CFG.get("bury", 1.5), 0.02)
        if q.z < 0.0: q.z = 0.0  # a low sucker's buried cone stays above ground (it sits in the flared trunk base)
        apex = bm.verts.new(q)
        for s in range(sides):
            f = bm.faces.new((ring[(s + 1) % sides], ring[s], apex)); f.material_index = 0
    if cap:  # pointed cone closes the branch end (no open ring / flat disc)
        ring = rings[-1][0]
        t = (br.pts[-1] - br.pts[-2]).normalized()
        # forked trunk: a low crotch dome, not a spear; palm stem / sucker under a rosette: a blunt cone in the frond bases
        k = 0.35 if (br.depth == 0 and CFG.get("fork")) else 1.0 if rosette else 2.5
        apex = bm.verts.new(br.pts[-1] + t * max(br.radii[-1] * k, 0.02))
        for s in range(sides):
            f = bm.faces.new((ring[s], ring[(s + 1) % sides], apex)); f.material_index = 0

def card(bm, uvl, base, d, nrm, s, fold, cell=None):
    """cell (atlas cell dict from <tex>_Leaves_Cards.json): UVs span that cell instead of the whole texture; the card
    width follows the cell's width/height (square atlas: UV ratio = pixel ratio; square cells = square cards)."""
    u0, v0, u1, v1 = cell["rect"] if cell else (0.0, 0.0, 1.0, 1.0)
    d = d.normalized(); nrm = (nrm - d * nrm.dot(d)).normalized(); side = nrm.cross(d)
    w = side * s * 0.5 * (u1 - u0) / (v1 - v0); base = base - d * s * 0.05; top = base + d * s; fv = nrm * s * fold
    if fold > 0:
        vs = [bm.verts.new(x) for x in (base - w, base + fv, base + w, top + w, top + fv, top - w)]
        for idx, us in (((0, 1, 4, 5), (0, .5, .5, 0)), ((1, 2, 3, 4), (.5, 1, 1, .5))):
            f = bm.faces.new([vs[k] for k in idx]); f.material_index = 1
            for loop, u, v in zip(f.loops, us, (0, 0, 1, 1)): loop[uvl].uv = (u0 + u * (u1 - u0), v0 + v * (v1 - v0))
    else:
        vs = [bm.verts.new(x) for x in (base - w, base + w, top + w, top - w)]
        f = bm.faces.new(vs); f.material_index = 1
        for loop, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uvl].uv = (u0 + u * (u1 - u0), v0 + v * (v1 - v0))

def sprig_card(bm, uvl, A, d, roll, s, fold, cell, dry=False, mirror=False):
    """Card whose atlas stem-base attach point lands exactly on A (a point on a branch axis); s = card length,
    width = s x the cell's width/height (square cells: square cards).
    dry: only return its corner points (0,0), (1,0), (1,1), (0,1), nothing is created.
    mirror: the cell is shown U-mirrored (same winding); the mirrored attach point still lands on A."""
    d = d.normalized(); n = (roll - d * roll.dot(d)).normalized(); side = n.cross(d)
    u0, v0, u1, v1 = cell["rect"]
    au = (cell["attach"][0] - u0) / (u1 - u0); av = (cell["attach"][1] - v0) / (v1 - v0)
    if mirror: au = 1.0 - au
    sw = s * (u1 - u0) / (v1 - v0)
    fv = n * s * fold
    O = A - (side * (au - 0.5) * sw + d * av * s + fv * max(0.0, 1.0 - abs(au - 0.5) * 2))
    grid = ((0, 0), (.5, 0), (1, 0), (1, 1), (.5, 1), (0, 1)) if fold > 0 else ((0, 0), (1, 0), (1, 1), (0, 1))
    if dry: return [O + side * (lu - 0.5) * sw + d * lv * s for lu, lv in ((0, 0), (1, 0), (1, 1), (0, 1))]
    first = len(bm.verts)
    vs = [bm.verts.new(O + side * (lu - 0.5) * sw + d * lv * s + (fv if lu == 0.5 else Vector())) for lu, lv in grid]
    quads = ((0, 1, 4, 5), (1, 2, 3, 4)) if fold > 0 else ((0, 1, 2, 3),)
    for q in quads:
        f = bm.faces.new([vs[k] for k in q]); f.material_index = 1
        for loop, k in zip(f.loops, q):
            lu, lv = grid[k]; loop[uvl].uv = (u0 + ((1.0 - lu) if mirror else lu) * (u1 - u0), v0 + lv * (v1 - v0))
    return first, grid, (au, av)

def card_attach_point(P, grid, au, av):
    """Atlas attach point of a built card: P maps its grid (lu, lv) keys to vertex positions."""
    bot = P[(0, 0)].lerp(P[(1, 0)], au); top = P[(0, 1)].lerp(P[(1, 1)], au)
    if (.5, 0) in P:  # folded card: piecewise through the mid column
        bot = P[(0, 0)].lerp(P[(.5, 0)], au * 2) if au < .5 else P[(.5, 0)].lerp(P[(1, 0)], au * 2 - 1)
        top = P[(0, 1)].lerp(P[(.5, 1)], au * 2) if au < .5 else P[(.5, 1)].lerp(P[(1, 1)], au * 2 - 1)
    return bot.lerp(top, av)

def nearest_on_axis(A, pts, radii):
    """(distance, point, radius) of the nearest point to A on the polyline pts (radius interpolated per segment)."""
    best = (1e9, pts[0], radii[0])
    for i in range(len(pts) - 1):
        p0, seg = pts[i], pts[i + 1] - pts[i]
        t = max(0.0, min(1.0, (A - p0).dot(seg) / max(seg.length_squared, 1e-12)))
        q = p0 + seg * t; dd = (A - q).length
        if dd < best[0]: best = (dd, q, radii[i] + (radii[i + 1] - radii[i]) * t)
    return best

def snap_cards_to_bark(bm, branches, cards, meshed):
    """The bark is meshed on other axes than the ones the cards were rooted on: LOD1 (lod1_subset) keeps every other
    ring, so a card rooted between kept rings hangs off the chord (WeepingWillow 10 % of cards, cedars 3.5 %, 5-46 cm);
    a merged child's cards sit on the child's axis, not on the smoothed head tube that meshes it (a few cm). Each card
    whose attach point lies farther than the tube radius from the meshed axis of the tube carrying its branch (the head
    of its merge chain) is moved rigidly so the point sits on that axis; cards within the radius never move. meshed:
    skeleton index -> (pts, radii) actually meshed. Returns the shifts (m) of the moved cards."""
    idx = {id(b): i for i, b in enumerate(branches)}
    bm.verts.ensure_lookup_table()
    order = sorted(cards, key=lambda c: c[0]); ends = [c[0] for c in order[1:]] + [len(bm.verts)]
    moved = []
    for (first, grid, (au, av), b, _), end in zip(order, ends):
        h = b
        while getattr(h, "merged_into", None) is not None: h = h.merged_into
        if idx[id(h)] not in meshed: continue
        A = card_attach_point({g: bm.verts[first + k].co for k, g in enumerate(grid)}, grid, au, av)
        dd, Q, r = nearest_on_axis(A, *meshed[idx[id(h)]])
        if dd <= max(r, 1e-4): continue
        sh = Q - A
        for k in range(first, end): bm.verts[k].co += sh
        moved.append(dd)
    return moved

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

def limb_chain(branches, b):
    """Members of the merged tube ending in terminal branch b (head first): parents that continue into it (merge)."""
    up = {id(x.cont): x for x in branches if getattr(x, "cont", None) is not None}
    ch = [b]
    while id(ch[0]) in up: ch.insert(0, up[id(ch[0])])
    return ch

def low_cut(branches):
    """low_tips cut: indices of tube heads whose whole merged chain lies below `cut` m and has no other branch rooted
    on it (a bare ground limb is dropped, not leafed; it never carries cards, so no card moves)."""
    LT = CFG.get("low_tips")
    if not LT or not LT.get("cut"): return set()
    out = set(); idx = {id(x): i for i, x in enumerate(branches)}
    for b in terminal_ends(branches):
        ch = limb_chain(branches, b)
        if ch[0].depth == 0 or max(p.z for x in ch for p in x.pts) >= LT["cut"]: continue
        ids = {id(x) for x in ch}
        if any(id(c) not in ids and c.depth > ch[0].depth and min((c.pts[0] - p).length for x in ch for p in x.pts) < 0.2
               for c in branches): continue
        out.add(idx[id(ch[0])])
    return out

def sprig_crown(bm, uvl, branches, rng, count, size, fold, lod1=False, keep=None, probe=None, roles=None):
    """keep (lod1_subset): place the LOD0 cards with the LOD0 random sequence, but build only the tip cards plus
    a `keep` share of the others, `grow` times larger around the same attach point (LOD1 = LOD0 thinned).
    probe (crown roles, first pass): a list that gets (A, d, size, kind) per placed card instead of any geometry;
    roles (second pass): per placed card "full" or "out" (see card_roles); the card keeps its place, direction and roll
    and only its atlas cell (and the cell's `scale`) changes, falling back to the drawn cell if the new one would not fit."""
    C = CFG["crown"]
    cells = json.load(open(TEX + f"{TEXN}_Leaves_Cards.json"))["cells"]
    md = C["mindepth"]
    if lod1 and CFG.get("lod1_mindepth") is not None: md = CFG["lod1_mindepth"]
    twigs = [b for b in branches if b.depth >= md and not getattr(b, "sides", None)]
    lens = [sum((b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1)) for b in twigs]
    cards = []  # every placed card (counts drive the loops below); dropped subset cards have first = None
    krng = random.Random(7919)  # own sequence: the subset choice never shifts the placement draws
    trng = random.Random(6007)  # own sequence for roll_tilt: card positions/directions stay those of the plain build
    CHAIN_UP = {id(x.cont): x for x in branches if getattr(x, "cont", None) is not None}  # floor_base: merged chain heads
    FBN = [0]  # floor_base: cards levelled
    KIND = ["tip"]  # which loop places the card (crown roles: tip / main / fill / low / hang)
    def place(b, t, d0, hang=False, nrm=None, exact=True, ub=None, aim=None):
        UB = C["upbias"] if ub is None else ub  # ub: per-card upbias (tip_upbias on ground-stem tips)
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
                d = ((-UP * 1.0 + rand_unit(rng) * 0.35) if hang else (d0 + rand_unit(rng) * C["tilt"] + UP * UB)).normalized()
                e1 = d.orthogonal().normalized(); e2 = d.cross(e1)  # the card is sz wide in an unknown roll
                if not any(in_clear(A + d * sz * f + e * sz * 0.5) for f in (0.0, 0.35, 0.7, 1.0)
                           for e in (Vector(), e1, -e1, e2, -e2, (e1 + e2) * 0.7072, (e1 - e2) * 0.7072,
                                     (e2 - e1) * 0.7072, -(e1 + e2) * 0.7072)): ok = True; break
            if not ok: return False
        else:
            d = ((-UP + rand_unit(rng) * 0.35) if hang else (d0 + rand_unit(rng) * C["tilt"] + UP * UB)).normalized()
        roll, cell = nrm if nrm is not None else rand_unit(rng), rng.choice(cards_cells)
        if C.get("cell_scale"):  # opt-in (sprig): the drawn cell's Cards.json "scale" (card length multiplier, default 1)
            sz *= cell.get("scale", 1.0)  # so a cell drawn with bigger leaves builds the same leaf size in metres; no draws
        fl = C.get("flat", 0.0) if C["mode"] == "sprig" and not hang else 0.0
        if fl:  # flat (sprig): cards lie toward horizontal with their face toward the sky (layered flat crowns)
            if Vector((d.x, d.y, 0.0)).length > 1e-6: d = Vector((d.x, d.y, d.z * (1.0 - fl))).normalized()
            roll = roll.lerp(UP, fl).normalized()
        MR = C.get("max_rise") if C["mode"] == "sprig" and not hang else None
        MF = C.get("max_fall") if C["mode"] == "sprig" and not hang else None
        for lim, bad in ((MR, MR is not None and d.z > math.sin(math.radians(MR or 0.0))),
                         (None if MF is None else -MF, MF is not None and d.z < -math.sin(math.radians(MF or 0.0)))):
            if not bad: continue  # opt-in: card tip clamped to <= max_rise / >= -max_fall deg, heading kept
            h = Vector((d.x, d.y, 0.0))
            if h.length < 1e-6: h = Vector((A.x, A.y, 0.0)) if Vector((A.x, A.y, 0.0)).length > 1e-6 else Vector((1.0, 0.0, 0.0))
            h.normalize(); d = (h * math.cos(math.radians(lim)) + UP * math.sin(math.radians(lim))).normalized()
        if aim is not None: d = aim(A, d)  # low_tips out: re-aimed tip-out
        SF = C.get("surface") if C["mode"] == "sprig" and not hang else None
        if SF:  # opt-in (sprig, clipped topiary): the card lies along the level surface through A of the ellipsoid
            c0 = b.pts[0] + UP * SF.get("lift", 0.0) if SF["c"] == "root" else Vector(SF["c"])  # "root": one dome per twig (cloud pads)
            q = A - c0; R2 = [x * x for x in SF["rad"]]  # (c, rad), face out, painted twig still on A
            g = Vector((q.x / R2[0], q.y / R2[1], q.z / R2[2]))
            if g.length > 1e-9:
                n = g.normalized(); tv = d - n * d.dot(n)  # (tv/bv: place() keeps its own b and t)
                if SF.get("skin"): A = A + n * r * SF["skin"]  # opt-in: root on the outer side of its twig (covers it)
                tv = (tv if tv.length > 1e-4 else n.orthogonal()).normalized()
                k = (tv.x * tv.x / R2[0] + tv.y * tv.y / R2[1] + tv.z * tv.z / R2[2]) / g.length  # normal curvature along tv
                dip = math.asin(min(0.64, sz * k * 0.5)) * SF.get("chord", 1.0)  # chord: far end back on the surface (<= 40 deg)
                d = (tv * math.cos(dip) - n * math.sin(dip)).normalized()
                n = (n - d * n.dot(d)).normalized(); roll = n
                if SF.get("max_up") is not None:  # smallest roll about d that keeps |normal.z| <= cos(max_up)
                    m = math.cos(math.radians(SF["max_up"])); bv = d.cross(n); Rm = math.hypot(n.z, bv.z)
                    if Rm > m:
                        p0 = math.atan2(bv.z, n.z); al = math.acos(m / Rm)
                        ph = min(((p0 + s * al + o + math.pi) % (2 * math.pi) - math.pi
                                  for s in (-1, 1) for o in (0.0, math.pi)), key=abs)
                        roll = n * math.cos(ph) + bv * math.sin(ph)
        RT = C.get("roll_tilt") if C["mode"] == "sprig" and not hang else None
        if RT:  # opt-in (sprig): roll each card about its own axis d so its plane stands RT deg (lo, hi) off the plane
            u = UP - d * UP.dot(d)  # through d and the horizontal: no card faces the sky flat (mat shrubs read as rosettes)
            if u.length > 1e-3:
                u.normalize(); a = math.radians(trng.uniform(*RT)) * (1.0 if trng.random() < 0.5 else -1.0)
                roll = (u * math.cos(a) + d.cross(u) * math.sin(a)).normalized()
        FB = None
        if C.get("floor_base") and C["mode"] == "sprig" and not hang:
            # opt-in floor_base: no card hangs below the base of its limb (where its merged chain leaves its parent)
            # towards the trunk: a card whose lowest corner is under that base and nearer the trunk axis than its root
            # is levelled (heading kept, tip no lower than its root) and laid face up, then fits() shrinks it (x0.75, up
            # to 5 times) or skips it until no corner is below min(base, root). No random draws; off = identical builds.
            h = b
            while id(h) in CHAIN_UP: h = CHAIN_UP[id(h)]
            lo = min(sprig_card(bm, uvl, A, d, roll, sz, fold, cell, dry=True), key=lambda x: x.z)
            if lo.z < h.pts[0].z and math.hypot(lo.x, lo.y) < math.hypot(A.x, A.y):
                if d.z < 0.0 and Vector((d.x, d.y, 0.0)).length > 1e-6: d = Vector((d.x, d.y, 0.0)).normalized()
                roll = (UP - d * UP.dot(d)).normalized() if (UP - d * UP.dot(d)).length > 1e-3 else roll
                FB = min(h.pts[0].z, A.z - 0.01); FBN[0] += 1
        def fits(cl, s, m=False):  # the card's real surface must stay out of keep-out volumes and above `ground` (shrunk)
            if exact and CFG.get("clear"):  # the real card surface (its back overhang and corners too) must stay out of the volumes
                q = sprig_card(bm, uvl, A, d, roll, s, fold, cl, dry=True, mirror=m)
                if any(in_clear(q[0].lerp(q[1], i / 4).lerp(q[3].lerp(q[2], i / 4), j / 4)) for i in range(5) for j in range(5)):
                    return None
            if C.get("ground") is not None:  # hanging cards stay above this height: shrink, then skip
                for _ in range(5):
                    if min(x.z for x in sprig_card(bm, uvl, A, d, roll, s, fold, cl, dry=True, mirror=m)) >= C["ground"]: break
                    s *= 0.75
                else:
                    return None
            if FB is not None:  # opt-in floor_base (above)
                for _ in range(5):
                    if min(x.z for x in sprig_card(bm, uvl, A, d, roll, s, fold, cl, dry=True, mirror=m)) >= FB: break
                    s *= 0.75
                else:
                    return None
            return s
        s0 = fits(cell, sz)  # the drawn cell decides whether the card is placed: roles/mirror never change the card count
        if s0 is None: return False
        idx = len(cards); mir = False
        if roles is not None or C.get("mirror"):
            # crown roles: the cell of the card's role (own per-card sequence, no shared draws), `scale` = its card length
            # multiplier; crown mirror: half the cards U-mirrored. Each falls back (unmirrored, then drawn cell) if it won't fit.
            M = (True, False) if C.get("mirror") and random.Random(7963 + idx).random() < 0.5 else (False,)
            cands = [(cell, sz)]
            if roles is not None:
                r = roles[idx]
                rc = (OUT[int(r[4:]) % len(OUT)] if r.startswith("out:")  # roles group: cells in turn along the branch
                      else random.Random(7951 + idx).choice(OUT if r == "out" else FULL))
                cands.insert(0, (rc, sz * rc.get("scale", 1.0)))
            for cl, s in cands:
                hit = next(((m, s2) for m in M for s2 in (fits(cl, s, m),) if s2 is not None), None)
                if hit: cell, (mir, s0) = cl, hit; break
        sz = s0
        if probe is not None: probe.append((A.copy(), d.copy(), sz, "hang" if hang else KIND[0], id(b), t))
        if keep is not None and t < 0.95 and krng.random() >= keep.get("keep", 0.5):
            cards.append((None, None, None, b, t)); return True
        if probe is not None: cards.append((-1, None, None, b, t)); return True
        first, grid, att = sprig_card(bm, uvl, A, d, roll, sz * (keep.get("grow", 1.3) if keep else 1.0), fold, cell, mirror=mir)
        cards.append((first, grid, att, b, t)); return True
    # opt-in crown cells=[i, ...] (sprig/bamboo): cards draw only these atlas cells (e.g. a dense clipped-surface cell for
    # topiary variants, open sprays for the free-growing ones); same single rng.choice per card, off = identical
    cards_cells = [cells[i] for i in C["cells"]] if C.get("cells") is not None else cells
    if roles is not None:  # crown roles: interior cards show "full" cells, the protruding ones lateral/shoot/sprig
        FULL = [c for c in cards_cells if c.get("role") == "full"]
        OUT = [c for c in cards_cells if c.get("role") in ("lateral", "shoot", "sprig")]
        assert FULL and OUT, "crown roles: the Cards.json cells need role full and lateral/shoot/sprig"
    bm.verts.ensure_lookup_table()
    # every terminal end above the leaf zone gets a card rooted just inside its cone cap; opt-in crown tip_upbias
    # (sprig, bamboo): the cards on ground-stem (culm) tips use this upbias instead of `upbias`, so a hanging-card
    # crown still dresses the nodding culm tip (no bare whip above the crown). No extra random draws: off = identical.
    for b in terminal_ends(branches):
        if b.pts[-1].z >= C["minz"] * 0.8:
            _, _, d = point_at(b, 0.97)
            place(b, 0.97, d, ub=C.get("tip_upbias") if b.depth == 0 or C.get("tip_upbias_all") else None)
    fill = C.get("fill")  # share of the cards spread over the inner limbs to close the gaps between clumps
    if fill:
        KIND[0] = "fill"
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
            if A.z < fill.get("minz", C["minz"]): continue
            # lean toward the crown axis and up, so fill cards close the hollow between splayed limbs
            to_axis = Vector((-A.x, -A.y, 0.0))
            if to_axis.length > 1e-3: d = (d * 0.4 + to_axis.normalized() * fill.get("inward", 0.0) + UP * fill.get("up", 0.6)).normalized()
            place(b, t, d)
        size = base
    KIND[0] = "main"
    if C.get("per_tip"):  # dense clusters on the outer part of every leaf-bearing branch, gaps between them
        k = C["per_tip"] if not lod1 else max(2, int(C["per_tip"] * CFG.get("lod1_cards", 0.6)))
        for b in twigs:
            if b.pts[-1].z < C["minz"]: continue
            for i in range(k):
                t = rng.uniform(C.get("tip_from", 0.55), 0.98); _, _, d = point_at(b, t); place(b, t, d)
        count = len(cards)
    tries = 0
    NS = C.get("node_step")  # opt-in (bamboo): cards on ground stems cluster at node heights every NS m (leaf tiers)
    while len(cards) < count and tries < count * 20:
        tries += 1
        b = rng.choices(twigs, lens)[0]
        t = rng.uniform(0.2, 0.97)
        if NS and b.depth == 0:  # snap to the stem's tier heights; each stem's tiers shifted by its own golden-ratio phase
            k = twigs.index(b); Lb = lens[k]; ph = (k * 0.618034 % 1.0) * NS
            t = max(0.2, min(0.97, (round((t * Lb - ph) / NS) * NS + ph) / Lb))
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
        KIND[0] = "hang"
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
    LT = CFG.get("low_tips")
    if LT:  # bare low limbs: chains with fewer than `min` cards get `n` cards over their outer `reach` m, one at the tip
        KIND[0] = "low"
        rng = random.Random(7907)  # own sequence, placed last: every card above is unchanged (place() reads this rng)
        base, size = size, LT.get("size", size); g0 = C.get("ground"); C["ground"] = LT.get("ground", 0.1)
        cut = {id(branches[i]) for i in low_cut(branches)}
        blen = lambda x: sum((x.pts[i + 1] - x.pts[i]).length for i in range(len(x.pts) - 1))
        aim = None
        if LT.get("out"):  # opt-in: low cards tip-out (radial + own heading) at lo..hi deg elevation, never hanging
            orng = random.Random(7937)
            def aim(A, d):
                rad = Vector((A.x, A.y, 0.0)); h = Vector((d.x, d.y, 0.0))
                h = (rad.normalized() if rad.length > 1e-6 else Vector()) + (h.normalized() * 0.5 if h.length > 1e-6 else Vector())
                h = h.normalized() if h.length > 1e-6 else Vector((1.0, 0.0, 0.0))
                e = math.radians(orng.uniform(*LT["out"]))
                return (h * math.cos(e) + UP * math.sin(e)).normalized()
        for b in terminal_ends(branches):
            ch = limb_chain(branches, b); ids = {id(x) for x in ch}
            if id(ch[0]) in cut or sum(id(c[3]) in ids for c in cards) >= LT.get("min", 3): continue
            segs = [(x, blen(x)) for x in reversed(ch)]  # tip member first
            for k in range(LT.get("n", 4)):
                s = 0.03 * blen(b) if k == 0 else rng.uniform(0.0, LT.get("reach", 1.0))  # arc length back from the tip
                for x, L in segs:
                    if s <= L or x is ch[0]: break
                    s -= L
                t = max(0.05, min(0.97, 1.0 - s / max(L, 1e-6)))
                _, _, d = point_at(x, t); place(x, t, d, aim=aim)
        C["ground"] = g0
        if g0 is None: del C["ground"]
        size = base
    CR = C.get("crest")
    if CR:  # opt-in (sprig, weeping): sprays standing on the top of the arching limbs (header: crown crest)
        KIND[0] = "crest"
        crng = random.Random(CR.get("seed", 7993))  # own sequence, placed last: every card above is unchanged
        step, gc, band = CR.get("step", 0.25), CR.get("cell", 0.6), CR.get("band", 0.3)
        key = lambda p: (math.floor(p.x / gc), math.floor(p.y / gc))
        blen_c = lambda x: sum((x.pts[i + 1] - x.pts[i]).length for i in range(len(x.pts) - 1))
        samp, top = [], {}
        for b in branches:
            if b.depth < 1 or getattr(b, "sides", None): continue
            n = max(2, int(blen_c(b) / step) + 1)
            for i in range(n):
                t = 0.03 + 0.94 * i / (n - 1); A = point_at(b, t)[0]; k = key(A)
                top[k] = max(top.get(k, -1e9), A.z)
                if b.depth >= CR.get("mindepth", 1): samp.append((A.z, b, t))
        zmin = CR.get("zmin", 0.5) * CFG["height"]
        cand = sorted((s for s in samp if s[0] >= zmin and s[0] >= top[key(point_at(s[1], s[2])[0])] - band),
                      key=lambda s: -s[0])
        chosen = []
        for z, b, t in cand:
            A = point_at(b, t)[0]
            if any((A - q).length < CR.get("space", 0.55) for q, _, _ in chosen): continue
            chosen.append((A, b, t))
            if len(chosen) >= CR.get("n", 80): break
        ccells = [cells[i] for i in CR.get("cells", (0, 1, 2))]
        made = 0
        for A, b, t in sorted(chosen, key=lambda c: (c[0].x, c[0].y, c[0].z)):  # stable order for the draws
            _, _, dt = point_at(b, t)
            th = Vector((dt.x, dt.y, 0.0)); rad = Vector((A.x, A.y, 0.0))
            rad = rad.normalized() if rad.length > 1e-6 else Vector((1.0, 0.0, 0.0))
            th = th.normalized() if th.length > 0.2 else rad
            FL = CR.get("follow", False)  # lie along the limb's real tangent, tipped outward, never above it
            if FL and th.dot(rad) < 0.0: th = -th
            if CR.get("both", True) and crng.random() < 0.5: th = -th  # either way along the limb: both arch flanks
            e = math.radians(crng.uniform(*CR.get("rise", (-5.0, 20.0))))
            if FL:  # rise is relative to the limb tangent's slope (<= 0: the spray drapes down over the arch)
                dtn = dt.normalized() if dt.length > 1e-6 else th
                slope = math.asin(max(-1.0, min(1.0, dtn.z if dtn.dot(th) >= 0.0 else -dtn.z)))
                e = min(slope, 0.0) + min(e, 0.0)
            d = (th * math.cos(e) + UP * math.sin(e) + rad * CR.get("out", 0.15)).normalized()
            n0 = th.cross(UP).normalized()  # card in the limb's vertical plane, then faced out and up
            if n0.dot(rad) < 0.0: n0 = -n0
            ph = math.radians(crng.uniform(*CR.get("face_up", (20.0, 50.0))))
            nrm = n0 * math.cos(ph) + UP * math.sin(ph)
            sz = CR.get("size", 1.4) * crng.uniform(0.85, 1.15); cell = crng.choice(ccells)
            q = sprig_card(bm, uvl, A, d, nrm, sz, fold, cell, dry=True)
            if (CFG.get("clear") and any(in_clear(x) for x in q)) or min(x.z for x in q) < C.get("ground", 0.0): continue
            made += 1
            if probe is not None:
                probe.append((A.copy(), d.copy(), sz, "crest", id(b), t)); cards.append((-1, None, None, b, t)); continue
            first, grid, att = sprig_card(bm, uvl, A, d, nrm, sz * (keep.get("grow", 1.3) if keep else 1.0), fold, cell)
            cards.append((first, grid, att, b, t))
        if probe is None:
            print(f"STAT crest {'lod1' if lod1 else 'lod0'} candidates {len(cand)} cards {made} "
                  f"z {round(min((c[0].z for c in chosen), default=0.0), 2)}-{round(max((c[0].z for c in chosen), default=0.0), 2)}")
    if C.get("floor_base") and probe is None: print(f"STAT floor_base {'lod1' if lod1 else 'lod0'} levelled {FBN[0]}")
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
    def strip(droop):
        pts, dirs = [A.copy()], []
        for i in range(segs):
            e = math.radians(tilt - droop * ((i + 0.5) / segs) ** dp)
            dirs.append(rad * math.cos(e) + axis * math.sin(e)); pts.append(pts[-1] + dirs[-1] * (L / segs))
        rows = []
        for k, p in enumerate(pts):
            t = (dirs[max(0, k - 1)] + dirs[min(segs - 1, k)]).normalized()
            sd = (side0 - t * side0.dot(t)).normalized(); sd.rotate(Quaternion(t, math.radians(twist) * k / segs))
            nv = t.cross(sd); hang = nv * fold * W
            rows.append((p - sd * W / 2 - hang, p, p + sd * W / 2 - hang))
        return pts, rows
    for _ in range(12):  # a frond may not reach the ground: relax its droop until the midrib clears 0.1 m and the
        pts, rows = strip(droop)  # frond edges (width, fold hang, twist) clear z = 0
        if min(p.z for p in pts) >= 0.1 and min(q.z for r in rows for q in r) >= 0.0: break
        droop *= 0.8
    else:
        return None
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
        hp = C.get("head_pow")  # opt-in: small heads (suckers) get count/young/dead x sc^head_pow and zone x sc
        hs = 1.0 if hp is None else sc ** (hp - 1.0)
        az0 = rng.uniform(0, 2 * math.pi); n = max(3, round(C["count"] * sc * hs))
        specs = [("live", i / max(1, n - 1)) for i in range(n)]
        Y, D = C.get("young"), C.get("dead")
        hn = (lambda k: k) if hp is None else (lambda k: round(k * sc ** hp))
        specs += [("young", 0.0)] * (hn(Y["n"]) if Y else 0) + [("dead", 1.0)] * (hn(D["n"]) if D else 0)
        for i, (kind, age) in enumerate(specs):
            if spread >= 360: az = az0 + i * math.radians(137.508)
            else: az = az0 + math.radians(((i * 0.618034) % 1.0 - 0.5) * spread)
            rad = e1 * math.cos(az) + e2 * math.sin(az)
            S = {"live": C, "young": Y, "dead": D}[kind]
            lo, hi = S["tilt"]; tilt = hi + (lo - hi) * age + rng.uniform(-jit, jit)
            dlo, dhi = S["droop"]; droop = max(0.0, dlo + (dhi - dlo) * age + rng.uniform(-jit, jit))
            L = rng.uniform(*C["length"]) * sc * (S.get("length", 1.0) if kind != "live" else 1.0)
            tw = rng.uniform(-1, 1) * C.get("twist", 0.0)
            z = Lb - C.get("top", 0.0) - C.get("zone", 0.3) * age * (1.0 if hp is None else sc)
            if kind == "dead": z -= rng.uniform(0, D.get("zone", 0.4))
            if kind == "young": tilt = rng.uniform(lo, hi)
            A = point_at(b, max(0.0, min(1.0, z / Lb)))[0]
            cell = cells[S["cell"]] if kind != "live" and S.get("cell") is not None else rng.choice(live)
            r = frond(bm, uvl, A, axis, rad, L, tilt, droop, tw, fold, cell, C)
            if r: cards.append(r + (b, 1.0))
    return cards

def bare_behind(probe, branches):
    """crown roles `bare` helper: per probe card, the bare limb length (m) between the card's root and the nearest
    foliage behind it, walking back along its merged limb chain and on into the parent limb chains: foliage = another
    card's root or the root of a side branch whose subtree carries cards. A walk that reaches a stem (a chain with no
    parent) ends there: trunks are not counted as bare limb."""
    seg = lambda b: [(b.pts[i + 1] - b.pts[i]).length for i in range(len(b.pts) - 1)]
    def arc(b, f):  # arc length at point_at parameter f (by point index)
        s = seg(b); x = f * len(s); i = min(int(x), len(s) - 1)
        return sum(s[:i]) + s[i] * (x - i) if s else 0.0
    head, off = {}, {}  # branch id -> chain head id, arc of the branch start along the chain
    for b in branches:
        if getattr(b, "merged_into", None) is not None: continue
        h, a = b, 0.0
        while h is not None:
            head[id(h)] = id(b); off[id(h)] = a; a += sum(seg(h)); h = getattr(h, "cont", None)
    byid = {id(b): b for b in branches}
    marks = {}  # chain head id -> [(arc, owner)]: owner = ("card", i) or ("child", child chain head id)
    for i, p in enumerate(probe):
        marks.setdefault(head.get(p[4]), []).append((off.get(p[4], 0.0) + arc(byid[p[4]], p[5]), ("card", i)))
    parent, kids = {}, {}  # chain head -> (parent chain head, arc of its root on that chain); chain head -> child heads
    for c in branches:
        par = getattr(c, "par", None)
        if par is None or getattr(c, "merged_into", None) is not None or id(par) not in head: continue
        s = seg(par); q = c.pts[0]; best = (1e9, 0.0); a0 = 0.0
        for k in range(len(s)):
            u = par.pts[k + 1] - par.pts[k]; L = max(1e-9, s[k]); w = max(0.0, min(1.0, (q - par.pts[k]).dot(u) / (L * L)))
            dd = (par.pts[k] + u * w - q).length
            if dd < best[0]: best = (dd, a0 + w * L)
            a0 += L
        parent[id(c)] = (head[id(par)], off[id(par)] + best[1]); kids.setdefault(head[id(par)], []).append(id(c))
    leafy = {}
    def has_cards(h):  # the chain or any chain in its subtree carries a card
        if h not in leafy:
            leafy[h] = False
            leafy[h] = any(o[0] == "card" for _, o in marks.get(h, [])) or any(has_cards(k) for k in kids.get(h, []))
        return leafy[h]
    for h, (ph, a) in parent.items():
        if has_cards(h): marks.setdefault(ph, []).append((a, ("child", h)))
    def walk(h, a, excl):
        if h not in parent: return 0.0  # a stem (chain with no parent): the trunk is not bare limb
        ms = [x for x, o in marks.get(h, []) if o != excl and x < a - 1e-6]
        if ms: return a - max(ms)
        ph, pa = parent[h]
        return a + walk(ph, pa, ("child", h))
    out = [0.0] * len(probe)
    for i, p in enumerate(probe):
        h = head.get(p[4]); me = off.get(p[4], 0.0) + arc(byid[p[4]], p[5])
        out[i] = walk(h, me, ("card", i))
    return out

def card_roles(probe, frac=0.2, low=True, group=None, top=None, above=None, bare=None, branches=None):
    """crown roles: "out" for the cards that stick out of the crown, "full" for the rest. The crown is the ellipsoid
    through the far card ends (A + d x size) of the tip and main cards: horizontal centre = their mean, horizontal
    radius = 90th percentile distance, vertical centre/radius from z10..z90. Out = the `frac` share of tip and main
    cards whose far end lies furthest out (stray tips and the silhouette edge), plus every low_tips card if `low`.
    Fill and hanging cards stay "full".
    group (opt-in): every non-hanging card on the same branch whose root lies within group x the median card length of
    an out card's root turns out too (the whole cluster on that tip), and the out cards of each branch get "out:<k>",
    k counting along the branch (by t) from a per-branch offset: the cells are taken in turn, neighbours differ.
    top / above (opt-in, rim and underside only): a card may turn out (as a seed, a low_tips card or a group member)
    only if its far end lies at or below zc + top x rz (the dome top keeps full cells) and its root at or above
    `above` m (low limbs by the trunk keep full cells); the `frac` share is still counted over all tip and main cards
    and taken from the furthest-out eligible ones.
    bare (opt-in, m): a card with more than `bare` m of bare limb behind its root on its limb chain (bare_behind) keeps
    a full cell: a long bare limb ending in a sparse sprig reads as a dead stick with a wisp (AleppoPineLean, review
    C1-med-spray3 r2 nit 4). Same frac share, taken from the next eligible cards. Off = identical builds."""
    far = [(p[0] + p[1] * p[2]) for p in probe]
    ids = [i for i, p in enumerate(probe) if p[3] in ("tip", "main")]
    tz = [p[0].z for p in probe]
    zc, rz = 0.0, 1.0
    if ids:
        pct = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]
        z10, z90 = pct([far[i].z for i in ids], 0.1), pct([far[i].z for i in ids], 0.9)
        zc, rz = (z10 + z90) / 2, max(1e-3, (z90 - z10) / 2)
    bb = bare_behind(probe, branches) if bare is not None else None
    ok = lambda i: ((top is None or (far[i].z - zc) / rz <= top) and (above is None or tz[i] >= above)
                    and (bb is None or bb[i] <= bare))
    roles = ["out" if low and p[3] == "low" and ok(i) else "full" for i, p in enumerate(probe)]
    if ids:
        cx = sum(far[i].x for i in ids) / len(ids); cy = sum(far[i].y for i in ids) / len(ids)
        rh = max(1e-3, pct([math.hypot(far[i].x - cx, far[i].y - cy) for i in ids], 0.9))
        sc = {i: math.hypot(math.hypot(far[i].x - cx, far[i].y - cy) / rh, (far[i].z - zc) / rz) for i in ids}
        for i in sorted((i for i in ids if ok(i)), key=lambda i: -sc[i])[:int(round(frac * len(ids)))]: roles[i] = "out"
    if not group: return roles
    reach = group * sorted(p[2] for p in probe)[len(probe) // 2]
    byb = {}
    for i, p in enumerate(probe): byb.setdefault(p[4], []).append(i)
    for s in [i for i, r in enumerate(roles) if r == "out"]:
        for j in byb[probe[s][4]]:
            if probe[j][3] != "hang" and (probe[j][0] - probe[s][0]).length <= reach and ok(j): roles[j] = "out"
    for b, js in byb.items():
        outs = sorted((j for j in js if roles[j] == "out"), key=lambda j: probe[j][5])
        k0 = random.Random(7951 + js[0]).randrange(3)
        for k, j in enumerate(outs): roles[j] = f"out:{k0 + k}"
    return roles

def crown(bm, uvl, branches, rng, count, size, fold, lod1=False, keep=None):
    C = CFG["crown"]; mode = C["mode"]
    if mode == "sprig":
        R = C.get("roles")
        if not R: return sprig_crown(bm, uvl, branches, rng, count, size, fold, lod1, keep)
        # opt-in crown roles=dict(frac=0.2, low=True): a dry first pass on a copy of the random state finds where each
        # card lands, the real pass places the very same cards and only swaps their cells by role (card count/tris kept)
        r1 = random.Random(); r1.setstate(rng.getstate()); probe = []
        sprig_crown(bm, uvl, branches, r1, count, size, fold, lod1, keep, probe=probe)
        roles = card_roles(probe, R.get("frac", 0.2), R.get("low", True), R.get("group"), R.get("top"), R.get("above"),
                           R.get("bare"), branches)
        n_out = sum(r.startswith("out") for r in roles)
        print(f"STAT crown roles {'lod1' if lod1 else 'lod0'} cards {len(probe)} out {n_out} "
              f"(low {sum(p[3] == 'low' for p in probe)}) full {len(roles) - n_out} mirror {'Y' if C.get('mirror') else 'N'}"
              + (f" group {R['group']}" if R.get("group") else "")
              + (f" top {R['top']}" if R.get("top") is not None else "") + (f" above {R['above']}" if R.get("above") is not None else ""))
        if R.get("bare") is not None:  # cards the bare-limb rule turned back to full (out without it), with their bare m
            bb = bare_behind(probe, branches)
            r0 = card_roles(probe, R.get("frac", 0.2), R.get("low", True), R.get("group"), R.get("top"), R.get("above"))
            kept = sorted((round(bb[i], 2), tuple(round(v, 2) for v in probe[i][0])) for i in range(len(probe))
                          if r0[i].startswith("out") and not roles[i].startswith("out"))
            print(f"STAT crown roles bare {R['bare']} {'lod1' if lod1 else 'lod0'} turned full {len(kept)} (bare m, root xyz) {kept}")
        return sprig_crown(bm, uvl, branches, rng, count, size, fold, lod1, keep, roles=roles)
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
    prng = random.Random(4243)  # ellipsoid `parts`: own sequence, so the shell choice never shifts the card draws
    for _ in range(count):
        ps = 1.0  # card size scale of the ellipsoid part (parts `size`)
        if mode == "spindle":
            h = rng.uniform(0, 1)
            z = C["z0"] + (C["z1"] - C["z0"]) * h
            cone = C.get("profile") == "cone"  # clipped topiary cone: rounded base up to `peak`, straight sides to the tip
            def prof_at(x):
                x = max(0.0, min(1.0, x))
                if cone: return max(0.08, math.sin(0.5 * math.pi * min(1.0, x / C["peak"])) if x < C["peak"] else (1 - x) / (1 - C["peak"]))
                pr = math.sin(math.pi * min(1.0, x / (2 * C["peak"]))) if x < C["peak"] else math.cos(0.5 * math.pi * (x - C["peak"]) / (1 - C["peak"]))
                return max(0.08, pr) ** 0.8
            rad = C["rmax"] * prof_at(h) * rng.uniform(*C.get("shell", (0.7, 1.0)))
            a = rng.uniform(0, 2 * math.pi); out = Vector((math.cos(a), math.sin(a), 0))
            p = Vector((0, 0, z)) + out * rad - out * size * 0.15
            d = (UP * 0.85 + out * 0.35 + rand_unit(rng) * 0.2).normalized()
            if z + size > C["z1"] + 0.1: d = UP.copy(); p.z = C["z1"] - size * rng.uniform(0.9, 1.3)
            nrm = orient_normal(rng, d, 0.0).lerp(out, 0.6)
            tg = C.get("tangent", 0.0)  # clipped topiary: cards lie along the profile surface (up the slope), facing out
            if tg:
                e = 0.01; hs = max(h, C["peak"] + e) if cone else h  # cone: the rounded base takes the side slope (no flared skirt)
                dr = C["rmax"] * (prof_at(hs + e) - prof_at(hs - e)); dz = 2 * e * (C["z1"] - C["z0"])
                sl = (UP * dz + out * dr).normalized(); sn = (out * dz - UP * dr).normalized()
                d = d.lerp(sl, tg).normalized(); nrm = nrm.lerp(sn, tg)
        else:  # ellipsoid shell
            c = Vector(C["c"]); R = Vector(C["rad"])
            if C.get("parts"):  # several overlapping shells (multi-domed crown, sucker clumps), picked by surface area
                Pt = C["parts"]
                e = prng.choices(Pt, [x["rad"][0] * x["rad"][1] + x["rad"][0] * x["rad"][2] + x["rad"][1] * x["rad"][2] for x in Pt])[0]
                c = Vector(e["c"]); R = Vector(e["rad"]); ps = e.get("size", 1.0)
            v = rand_unit(rng)
            if v.z < -0.35 and C.get("under", True): v.z = -v.z * 0.5  # few cards on the underside
            v.normalize(); k = rng.uniform(0.72, 1.0)
            LP = C.get("lumps")  # natural crown: the shell radius swells and dips with deterministic noise (bumpy outline)
            if LP: k *= 1.0 + LP["amp"] * noise.noise(Vector((v.x * R.x, v.y * R.y, v.z * R.z)) / LP["size"] + Vector(LP.get("ofs", (3.1, 7.3, 1.7))))
            p = c + Vector((v.x * R.x, v.y * R.y, v.z * R.z)) * k
            out = Vector((v.x / R.x, v.y / R.y, v.z / R.z)).normalized()
            d = (out * 0.6 + UP * 0.45 + rand_unit(rng) * 0.35).normalized()
            tg = C.get("tangent", 0.0)  # clipped topiary: cards lie along the shell surface, facing out
            if tg:
                dt = d - out * d.dot(out)
                if dt.length > 1e-4: d = d.lerp(dt.normalized(), tg).normalized()
            p = p - d * size * ps * 0.45
            nrm = orient_normal(rng, d, C.get("flat", 0.0))
            if tg: nrm = nrm.lerp(out, tg)
        s = size * ps * rng.uniform(0.85, 1.15)
        cl = pick()
        if C.get("ground") is not None:  # volume crowns: a card reaching below `ground` m is lifted until it clears
            dn = d.normalized(); nn = (nrm - dn * nrm.dot(dn)).normalized()
            u0, v0, u1, v1 = cl["rect"] if cl else (0.0, 0.0, 1.0, 1.0)
            w = nn.cross(dn) * s * 0.5 * (u1 - u0) / (v1 - v0); b0 = p - dn * s * 0.05; fv = nn * s * fold
            low = min(x.z for x in (b0 - w, b0 + w, b0 + dn * s - w, b0 + dn * s + w, b0 + fv, b0 + dn * s + fv))
            if low < C["ground"]: p = p + UP * (C["ground"] - low)
        card(bm, uvl, p, d, nrm, s, fold, cl)

def base_axis(pts, radii, ov):
    """Mesh-only axis of a child limb the base fix touched (the skeleton, cards and grandchildren stay put): ov["P"] puts
    the base on the parent's meshed axis (a limb floating off its branch), ov["rb"] narrows the base ring to rb and widens
    it back to the limb's own radius over a neck of BASE_NECK base radii (a limb as thick as its parent there, whose cone
    could only be closed by a flat disc)."""
    pts, radii = list(pts), list(radii)
    if ov.get("P") is not None: pts[0] = ov["P"].copy()
    rb = ov.get("rb")
    if rb is not None and rb < radii[0] and len(pts) > 1:
        e = pts[1] - pts[0]; L1 = e.length; s = min(0.5 * L1, BASE_NECK * radii[0])
        if s > 1e-4:
            pts.insert(1, pts[0] + e * (s / L1)); radii.insert(1, radii[0] + (radii[1] - radii[0]) * s / L1)
        radii[0] = rb
    return pts, radii

BASE_NECK = 3.0  # base fix: a narrowed base ring widens back to the limb's radius over this many limb radii
BASE_STEP = 0.85  # base fix: a flat cap's base ring narrows to BASE_STEP ** n x the limb radius on its n-th pass
BASE_ROUNDS = 4  # base fix: mesh -> clamp -> contacts passes at most (narrowest base 0.85 ** 4 = 0.52 x the limb)

def base_fix(branches, meshed, vspans, bad, over):
    """CFG base_fix (default on with base_clamp): per child base that base_cones.contacts flags on the clamped mesh, a
    mesh-only override for the next pass (see base_axis). Floating: the base goes onto the nearest point of its parent's
    meshed axis (the head of the parent's merge chain; without a recorded parent, the nearest other meshed tube). A base
    that already sits within half the parent radius of that axis is left alone (its gap comes from elsewhere). Flat cap:
    the base goes onto that axis too, and the base ring narrows by BASE_STEP on every pass the cap still shows (the
    parent tapered under the fork, a three-way fork of equal limbs). Returns the new override dict (== `over`: done)."""
    new = {k: dict(v) for k, v in over.items()}; idx = {id(b): i for i, b in enumerate(branches)}
    for c in bad:
        bi = next((i for i, v0, v1 in vspans if v0 <= c["vert"] < v1), None)
        if bi is None: continue
        b = branches[bi]; A = b.pts[0]; p = getattr(b, "par", None)
        while p is not None and getattr(p, "merged_into", None) is not None: p = p.merged_into
        pi = idx.get(id(p)) if p is not None else None
        if pi not in meshed:
            cand = [(axis_gap(A, *meshed[j]), j) for j in meshed if j != bi]
            if not cand: continue
            pi = min(cand)[1]
        dd, P, rp = nearest_on_axis(A, *meshed[pi])
        if not c["flat_cap"] and dd <= 0.5 * rp and bi not in over: continue  # base already on the parent axis: nothing to move
        ov = new.setdefault(bi, {}); ov["P"] = P.copy()
        if c["flat_cap"]:
            ov["n"] = ov.get("n", 0) + 1; ov["rb"] = max(TIP_R, b.radii[0] * BASE_STEP ** ov["n"])
    return new

def make_lod(name, seed, lod1, full_rings=frozenset(), base_over=None, base_round=0, lv=None):
    """full_rings: indices (in skeleton order) of tubes meshed with every ring in the lod1_subset LOD1 (set by the
    floating-bark retry below; empty on the first pass). base_over / base_round: the base fix's mesh-only overrides
    (skeleton index -> base_axis dict) and pass number (see base_fix; empty / 0 on the first pass).
    lv (--lods): one far level of LOD_LEVELS / CFG lods, built like the lod1_subset LOD1 from the same skeleton and card
    draws: every `rings`-th ring, `sides`, tubes deeper than `maxdepth` (or `drop` levels off the deepest, kept when the
    tree has fewer levels than that) or thinner at the base than `min_r` x the thickest stem not meshed (nor any branch
    on them); every card kept, `grow` x larger about its attach point, unfolded (the cull thins them by visibility)."""
    base_over = base_over or {}
    MERGE_SKIPPED[0] = 0
    branches = build_skeleton(seed)
    if lv is not None: lod1 = True
    sub = (dict(keep=1.0, grow=lv.get("grow", 1.0)) if lv is not None else CFG.get("lod1_subset")) if lod1 else None
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
    if CFG.get("declip"):  # opt-in: limbs that clash (bark through bark) are tilted apart about their bases, see CFG["declip"]["script"]
        if "mod" not in DECLIP_STATS:  # loaded once: its cache replays the same moves for every LOD
            import importlib.util as _ilu
            _sp = _ilu.spec_from_file_location("declip_mod", CFG["declip"]["script"]); _dmod = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_dmod)
            DECLIP_STATS["mod"] = _dmod
        DECLIP_STATS[name] = DECLIP_STATS["mod"].declip(branches, low_cut(branches), CFG, ("declip", NAME, seed), NAME)
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap"); bm.loops.layers.uv.new(lightmap_uv.LAYER)
    deep = max(b.depth for b in branches)
    S0, S1 = CFG.get("sides", (7, 5, 4)), CFG.get("lod1_sides", (5, 4, 3))
    skip = set()  # lv: tubes not meshed in this far level (too deep or too thin), and every branch rooted on one
    if lv is not None:
        md = lv.get("maxdepth")
        if md is None and lv.get("drop") and deep - lv["drop"] >= 1: md = deep - lv["drop"]
        rmin = lv.get("min_r", 0.0) * max(b.radii[0] for b in branches if b.depth == 0)
        for bi, b in enumerate(branches):
            p = getattr(b, "par", None)
            if (md is not None and b.depth > md) or (b.depth > 0 and b.radii[0] < rmin) or \
                    (p is not None and any(branches[j] is p for j in skip)):
                skip.add(bi)
    spans = []  # (skeleton index, first bark face, end) per meshed tube
    vspans = []  # (skeleton index, first vertex, end) per meshed tube (base fix)
    meshed = {}  # skeleton index -> (pts, radii) of the axis actually meshed (LOD1: thinned; base fix: base_axis)
    cut = low_cut(branches)  # low_tips: bare ground limbs are not meshed
    for bi, b in enumerate(branches):
        if getattr(b, "merged_into", None) is not None or bi in cut or bi in skip: continue  # merged: its axis is the tail of its parent's tube
        St = lv["sides"] if lv is not None else S1 if lod1 else S0
        if getattr(b, "sides", None): sides = b.sides
        elif b.depth == 0: sides = St[0]
        elif b.depth < deep or deep == 1: sides = St[1]
        else: sides = St[2]
        full = (b.pts, b.radii)
        if sub and len(b.pts) > 2 and bi not in full_rings:  # every other (lv: every `rings`-th) ring; the cards stay rooted on the full axis
            ks = list(range(0, len(b.pts) - 1, lv.get("rings", 2) if lv is not None else 2)) + [len(b.pts) - 1]
            b.pts = [b.pts[k] for k in ks]; b.radii = [b.radii[k] for k in ks]
        if bi in base_over: b.pts, b.radii = base_axis(b.pts, b.radii, base_over[bi])  # base fix (mesh only)
        f0 = len(bm.faces); v0 = len(bm.verts)
        tube(bm, b, sides, CFG.get("lobe", 0.16), CFG.get("caps", False))  # lobe: trunk cross-section wobble (lumpy base)
        spans.append((bi, f0, len(bm.faces))); meshed[bi] = (list(b.pts), list(b.radii))
        vspans.append((bi, v0, len(bm.verts)))
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
            return make_lod(name, seed, lod1, full_rings | add, base_over, base_round, lv)
    if CFG.get("base_clamp", True):
        nclamp = base_cones.clamp(bm)
        if CFG.get("base_fix", True):  # limbs floating off their branch / flat-capped bases: fix the axis, mesh again
            bad = [c for c in base_cones.contacts(bm, k=1.0 / base_cones.SHIP_SCALE) if c["floating"] or c["flat_cap"]]
            new = base_fix(branches, meshed, vspans, bad, base_over) if bad and base_round < BASE_ROUNDS else base_over
            if new != base_over:
                bm.free(); bpy.data.meshes.remove(me)
                return make_lod(name, seed, lod1, full_rings, new, base_round + 1, lv)
            if base_over or bad:
                print("STAT", name, "base fix moved", sum(1 for v in base_over.values() if v.get("P") is not None),
                      "narrowed", sum(1 for v in base_over.values() if v.get("rb") is not None), "passes", base_round,
                      "left", [(c["child"], "float" if c["floating"] else "cap", c["gap_mm"] if c["floating"] else c["cap_out_mm"]) for c in bad])
        if nclamp: print("STAT", name, "base cones clamped", nclamp)
    FULL_RINGS[name] = len(full_rings); SKIPS[name] = MERGE_SKIPPED[0]; MESHED[name] = meshed
    C = CFG["crown"]
    if sub:  # same count, size and draws as LOD0; sprig_crown builds a subset, larger, unfolded
        cards = crown(bm, uvl, branches, random.Random(seed + 11), C["count"], C.get("size", 1.0), 0.0, False, sub)
    else:
        cards = crown(bm, uvl, branches, random.Random(seed + 11),
              int(C["count"] * (CFG.get("lod1_cards", 0.6) if lod1 else 1.0)),
              C.get("size", 1.0) * (CFG.get("lod1_size", 1.35) if lod1 else 1.0), 0.0 if lod1 else C.get("fold", 0.0), lod1)
    if cards:  # every painted twig base on the bark that is actually meshed (LOD1: the thinned tubes that ship)
        SNAPPED[name] = snap_cards_to_bark(bm, branches, cards, meshed)
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
    print("STAT", name, "lightmap", lightmap_uv.repack(ob, bark=CFG.get("lightmap_bark", 5.0), check=False))
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
if CFG.get("leaf_cluster"):  # matte foliage: no specular sheen or rim
    bsdf.inputs["Roughness"].default_value = 1.0; bsdf.inputs["Specular IOR Level"].default_value = 0.0

SKELETONS = {}
DECLIP_STATS = {}  # per LOD name: declip result (CFG declip)
FULL_RINGS, SKIPS = {}, {}  # per LOD name: tubes kept at every ring (LOD1 retry), merges skipped
MESHED, SNAPPED = {}, {}  # per LOD name: meshed axis per tube; shifts of the cards moved onto the meshed bark
SEED = CFG["seed"] or pick_seed()
tree_uv.OFFSET_SEED = SEED if CFG.get("bark_tile_min") is not None else None
# Default: one LOD0 mesh named <Species>_Tree. LOD1 (fewer sides, half the deepest twigs, 35 % larger
# cards, 60 % of the count, no fold) only with --lod1, for very large worlds. --lods (with --lod1): the far levels
# <Species>_Tree_LOD2, _LOD3 (CFG lods, default LOD_LEVELS) for a LODGroup whose LOD0 is the culled LOD1; their
# leaf normals use the LOD1 crown proxy so all levels shade alike.
lod0 = make_lod(f"{NAME}_Tree" + ("_LOD0" if LOD1 else ""), SEED, False)
LODS = [lod0] + ([make_lod(f"{NAME}_Tree_LOD1", SEED, True)] if LOD1 else [])
if LOD1 and LODS_ON:
    LODS += [make_lod(f"{NAME}_Tree_LOD{2 + i}", SEED, True, lv=L) for i, L in enumerate(CFG.get("lods", LOD_LEVELS))]

def tris(o, mi=None): return sum(len(p.vertices) - 2 for p in o.data.polygons if mi is None or p.material_index == mi)
def bounds(o):
    vs = [v.co for v in o.data.vertices]
    return [round(min(v[i] for v in vs), 2) for i in range(3)], [round(max(v[i] for v in vs), 2) for i in range(3)]
def coplanar_pairs(obj, eps=1e-4):  # faces not above ground (flare skirt walls and discs) are never seen: not counted
    me = obj.data; hits = 0
    faces = [(p.normal.normalized(), p.center.copy(), [me.vertices[i].co.copy() for i in p.vertices]) for p in me.polygons
             if p.material_index == 0 and max(me.vertices[i].co.z for i in p.vertices) > 1e-6]
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
for _n, _d in DECLIP_STATS.items():
    if _n != "mod": print("STAT", _n, "declip", _d)
for o in LODS:
    print("STAT", o.name, "tris", tris(o), "bark", tris(o, 0), "leaf", tris(o, 1), "bounds", bounds(o))
print("STAT coplanar-overlapping bark pairs LOD0:", coplanar_pairs(lod0))
def attach_report(o):
    """Measured on the final mesh: each card's attach point (its atlas stem base mapped through the card's own
    vertices) against the nearest axis of the bark actually meshed in this LOD (LOD1: the thinned tubes that ship) and
    that tube's radius there; out_of_tolerance = farther than the radius (bare_limbs.py would see a floating spray)."""
    branches, cards = SKELETONS[o.name]
    if not cards: return None
    vs = o.data.vertices; axes = list(MESHED[o.name].values()); dist, bad = [], 0
    for first, grid, (au, av), _, _ in cards:
        A = card_attach_point({g: vs[first + k].co for k, g in enumerate(grid)}, grid, au, av)
        dd, _, r = min((nearest_on_axis(A, *ax) for ax in axes), key=lambda x: x[0])
        dist.append(dd); bad += dd > max(r, 1e-4)
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
    print("STAT", o.name, "bark stretch (min, median, max, max/min)", stretch_stats(o),
          "attach", o.name.rsplit("_", 1)[-1] if "_LOD" in o.name else "LOD0", attach_report(o))
    if SNAPPED.get(o.name):
        sh = sorted(SNAPPED[o.name])
        print("STAT", o.name, "cards moved onto the meshed bark:", len(sh), "median cm", round(100 * sh[len(sh) // 2], 1),
              "max cm", round(100 * sh[-1], 1))
for o in LODS:
    before = leaf_normal_spread(o)
    dims = transfer_crown_normals(o, CFG["proxy"], cluster=CFG.get("leaf_cluster"), crown_mix=CFG.get("leaf_crown_mix", 0.35),
                                  ref=LODS[1] if o.name[-1:] in "23456789" and "_LOD" in o.name else None)
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

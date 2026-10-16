# "Outside the room" LODs for dense object groups

A room full of small props (a wine wall of bottles, server racks, a book wall) can cost 80–120
draws on its own, and players see it two ways: up close inside the room, and from far away through
glass or a doorway. Occlusion culling cannot hide it behind glass (glass is not an occluder), so the
far view pays the full cost.

Unity `LODGroup` switches on **screen size, not position**: it cannot know whether the player is
inside. In practice inside means close and outside means far, so a screen-size switch does the job.

Status: measured in a penthouse world (pass 2 on 2026-10-12, error-bounded redo on 2026-10-14
after the user rejected the ratio LODs): 12 room clusters plus heavy props. Tools:
`scripts/StaticMergeTool.cs.txt` modes `lod` and `heavy`, `scripts/MeshDecimator.cs.txt`,
`scripts/LodBillboards.cs.txt` (menus under *Tools → Static Merge*); copy them to an `Editor/`
folder as `.cs`, and `scripts/LodBillboard.shader.txt` (runtime) plus `scripts/LinearDepth.shader.txt`
(capture only) as `.shader` files outside `Editor/`. LODs are built in Unity on copies, not in
Blender: the copies keep the source's lightmap index and scale-offset, so no re-bake is needed.

## Recipe

1. **One LODGroup per cluster, never per small object.** Hundreds of tiny LODGroups add per-frame
   culling cost of their own. Heavy single props (≥ ~10 k triangles) are the exception: one
   LODGroup each.
2. **LOD0 = the cluster merged** with the no-bake recipe in [merging.md](merging.md) (per material
   and lightmap index; the source renderers are disabled, never deleted). A merge that passes its
   capture proof is pixel-identical, so the originals are not needed as LOD0. For a heavy prop,
   LOD0 is the original renderer.
3. **Levels are error-bounded, not ratio-driven** (user, 2026-10-14: the first 50 %-ratio level
   looked "shredded, sawtooth coves, spiky panels"). Four levels by default (user, 2026-10-13:
   "full, some decimation, heavy decimation, billboards"):
   - LOD0 full; LOD1 stops before any surface moves more than **3 mm**; LOD2 at **12 mm**; LOD3 a
     billboard (below). Whatever triangle count that leaves is the level (room merges kept 60–95 %
     at LOD1, 50–85 % at LOD2); the triangle saving was never the goal, the draw calls were.
   - Collapses that fold a UV0 or UV2 triangle are rejected (lightmap blotches). UV0/UV2/normal
     seams, submesh borders and open borders stay locked. Gate every level: signed volume ≥ 0.8
     of the source, bounds ≥ 95 %, zero-length normals repaired; a level saving < 20 % reuses the
     level above.
   - **The error is in metres, so decimate in metres**: scale positions by the renderer's largest
     |lossyScale| for the run. On a 100×-scaled FBX (a 1 cm couch mesh) a 3 mm bound in mesh units
     meant 30 cm, and `Vector3.normalized` returns zero below 1e-5, so every plane normal was zero
     and every collapse cost nothing: the couch came out blotchy and notched. Any length or area
     epsilon in mesh code needs world-scaled positions.
   - A level that still shows lightmap blotches after the gate (a large upholstered sectional did)
     reuses LOD0 for that level.
4. **Switch distances follow from the error**: put level k where its error is about one pixel
   (`PixelAngle` 0.0015 rad): LOD1 beyond half the diagonal + 2 m, LOD2 beyond half + 8 m, the
   billboard beyond half + 25 m for rooms and half + 16 m for props. Set the heights for the worst
   case, VRChat Low (lodBias 1) at 110° FOV; High (lodBias 2) doubles every distance.
   `ReapplyLodHeights()` re-derives them without a rebuild.
5. **The switch scales with the player's settings.** Screen height ∝ lodBias / tan(FOV/2), so
   VRChat's quality levels move it (Low 1, Medium 1.5, High 2) and a VR headset (~100° vertical
   FOV) switches nearer than desktop. Test forced levels and automatic switching at lodBias 1 and 2.
6. Inside rooms and doorways the cluster must stay LOD0 at every bias.
7. Re-bake occlusion after building (LOD0 meshes changed); check for pop along paths and at
   doorways. Merged furniture is never OccluderStatic: a merge exceeds Smallest Occluder where its
   sources didn't and culls furniture behind it.

### Lowest LOD is a per-object billboard (user rules, 2026-10-13)

The last level is **not** a further-decimated mesh. Each object in the cluster gets its own Y-axis
card (user pick after whole-room cards looked flat from the garden): an object is the highest
hierarchy node whose renderers fit about 3.6 × 3.2 m; merged pieces are expanded back to their
sources for the capture. Cards are captured with the baked lighting from 8 directions, tiles
16–128 px sized to the pixels the object covers where its card starts, all cards of a group on one
atlas page as one mesh (one batch per visible page). A whole furnished penthouse came to 333 cards
on one 4096 page (about 21 MB), draw calls unchanged.

Keep a mesh at the billboard level (LOD3 = LOD2) for whatever a Y-axis card misrepresents:

- emissive or Unlit materials (pendant lamps vanished as cards);
- flat objects under 25 cm tall (a doormat became a slanted sliver);
- wall panels under 0.5 m deep and over 1 m wide (wine-wall bays stuck out as dark slabs);
- pieces bigger than an object (ceilings, soffits, long counters): as cards the ceiling vanished
  and its cove LEDs floated as a doubled ring;
- objects under 25 cm get no card at all.

Rebuild the cards after every merge rebuild and every lighting bake (they hold the baked light),
then re-derive the heights and re-bake occlusion.

### Impostors only as the very last level

Depth-mesh room impostors swapped by an Udon distance switch come **after** the billboards (user,
2026-10-14: "keep them, but only far away, after the real LODs"): in the penthouse at 27 m from the
room footprint. Gate each impostor piece by rendering it against the real room at VR resolution
from every point of a 0.5 m grid over the walkable area where the switch can show it, eye heights
1.1 and 1.6 m; a piece differing in more than 0.006 % of pixels by > 24/255 is deleted so that room
stays real. Coarser gates (2 m grid, nearest 4 points, a 1 m grid stopping short of the barrier)
each let a visibly wrong piece through. Error-bounded, the layer ended up saving little.

## Diagnose before touching LOD code

"First LOD shredded, objects culled in line of sight" turned out to be the garden **impostors**,
not the mesh LODs. Render the user's camera with and without each far layer (impostors, cards,
LODGroups forced to LOD0) before changing any of them.

## Proof

Same as merging: same-camera captures inside, in the doorway and from outside; mature before/after
samples from the outside viewpoints; inside views unchanged. For the far levels: render each
outdoor pose with every LODGroup forced to each level and again with automatic LOD, and diff
against LOD0. Render every heavy object's LOD1/LOD2 once, forced: **the volume gate misses thin
sheets** (two bed duvets passed it with LOD1 shredded); skip props in enclosed rooms whose farthest
reachable view never reaches the switch distance (the LOD only ships risk).

## Measured (penthouse world)

- Error-bounded levels, forced: LOD1/LOD2 differ from LOD0 in ≤ 0.1 % of pixels from the garden
  and jacuzzi, 0.3 % at 3 m inside the lounge (a thin wire sculpture, one side table). Switch
  distances at lodBias 1, 110°: lounge 11.3 / 17.3 / 34.3 m, dining 7.6 / 13.6 / 30.6 m.
- The earlier ratio LODs (LOD1 50 %, LOD2 20 %, one far distance D = 30 m) passed pixel diffs of
  ≤ 0.04 % yet the user saw shredded coves and saw-tooth panel edges: pixel-share metrics average
  away thin-feature damage, so look at forced-level renders of the thin features themselves.
- Decimation floors set by locked seams: a statue reached 0.29, millwork only 0.82.
- LOD0 = merged: inside and doorway captures changed ≤ 0.075 % of pixels, none over 8 codes.

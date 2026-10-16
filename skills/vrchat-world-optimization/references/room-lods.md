# "Outside the room" LODs for dense object groups

A room full of small props (a wine wall of bottles, server racks, a book wall) can cost 80–120
draws on its own, and players see it two ways: up close inside the room, and from far away through
glass or a doorway. Occlusion culling cannot hide it behind glass (glass is not an occluder), so the
far view pays the full cost.

Unity `LODGroup` switches on **screen size, not position**: it cannot know whether the player is
inside. In practice inside means close and outside means far, so a screen-size switch does the job.

Status: measured in a penthouse world (pass 2, 2026-10-12): 12 room clusters plus 15 heavy props;
numbers in the "Measured" section below. Tool: `scripts/StaticMergeTool.cs.txt` modes `lod` and
`heavy`, with `scripts/MeshDecimator.cs.txt`.

## Recipe

1. **One LODGroup per cluster, never per small object.** Hundreds of tiny LODGroups add per-frame
   culling cost of their own. Heavy single props (≥ ~10 k triangles) are the exception: one
   LODGroup each.
2. **LOD0 = the cluster merged** with the no-bake recipe in [merging.md](merging.md) (per material
   and lightmap index; the source renderers are disabled, never deleted). A merge that passes its
   capture proof is pixel-identical, so the originals are not needed as LOD0. For a heavy prop,
   LOD0 is the original renderer.
3. **LOD1 ≈ 50 %, LOD2 ≈ 20 % triangles**, decimated copies of the LOD0 meshes that keep the
   source's lightmap index and scale-offset (UV2 untouched by the collapse). Gate every level:
   signed volume ≥ 0.8 of the source, bounds ≥ 95 %, zero-length normals repaired, UV0/UV2/normal
   seams, submesh borders and open borders locked. A level that saves < 25 % is skipped: a
   seam-locked mesh that only reaches ~0.8 loses visible detail for too little gain.
4. **One far distance D for the whole world**, stored once (`SetFarLodDistance`): LOD1 from D,
   LOD2 from 2·D, a culled sliver at the end. The heights are computed at lodBias 1 and FOV 60.
5. **The switch scales with the player's settings.** Screen height ∝ lodBias / tan(FOV/2), so
   VRChat's quality levels move it (Low 1, Medium 1.5, High 2) and a VR headset (~100° vertical
   FOV) switches at about **0.5 × D**. Test the far captures at lodBias 0.5, 1, 1.5 and 2, and
   report the VR row analytically.
6. Pick D from captures along the reachable outdoor paths at 2–3 candidate distances (the world
   owner chooses); inside rooms and doorways the cluster must stay LOD0 at every bias.
7. Re-bake occlusion after building (LOD0 meshes changed); check for pop along paths and at
   doorways.

### Lowest LOD is a billboard (user rule, 2026-10-13)

The last level before the culled sliver is **not** a further-decimated mesh. It is a billboard:
the cluster captured from outside into one texture, on a few quads (or a depth-mesh card), with one
material, so the whole room or prop group costs one draw. LOD1 and LOD2 stay decimated meshes for the
middle distances. Capture with the lighting baked in (unlit card), from the side players actually
see the cluster from; check it with the same-camera forced-level renders at 110° FOV, like every
other level.

## Proof

Same as merging: same-camera captures inside, in the doorway and from outside; mature before/after
samples from the outside viewpoints; inside views unchanged. For the far levels: render each
outdoor pose with every LODGroup forced to LOD0 and again with automatic LOD per (D, lodBias), and
diff the pair.

## Measured (penthouse world, pass 2)

- Candidates 30 / 50 / 70 m from six garden-path poses: the worst far-LOD pixel change was
  0.04 % of pixels > 5 codes (D 30, lodBias 0.5); at lodBias ≥ 1 every case was ≤ 0.006 %. The
  owner picked **30 m**. Triangles saved in view at lodBias 1: 120 k–350 k desktop, 340 k–440 k
  VR-FOV (analytic).
- Decimation floors set by locked seams: a statue reached 0.29, millwork only 0.82 (skipped).
- **The volume gate misses thin sheets.** Two bed duvets passed it (volume ≥ 0.8) with LOD1 shredded
  or reshaped; the reviewer caught it. Render every heavy object's LOD1/LOD2 once, forced, and
  skip props in enclosed rooms whose farthest reachable view is inside the VR switch distance
  (they never show a far level, so the LOD only ships risk).
- LOD0 = merged: inside and doorway captures changed ≤ 0.075 % of pixels, none over 8 codes.

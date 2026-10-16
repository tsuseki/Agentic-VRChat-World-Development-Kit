# Merging static meshes for draw calls, without a lighting re-bake

Draw calls, not triangles, are the usual bottleneck in dense interiors (modern furniture packs,
modular railings, lamp hardware, shelves of props). Unity static batching helps but stops at every
material change, lightmap page, transparent object and probe difference; whatever is left in the
named rows of the category table ([draw-call-attribution.md](draw-call-attribution.md)) is what it
could not batch. Merging builds one mesh per group so the group costs one draw per material.

Status: measured in a penthouse world (pass 2, 2026-10-12) with `scripts/StaticMergeTool.cs.txt`:
2,013 source renderers → 383 merged pieces (ceiling fixtures 112 → 39, railings/mullion cells
338 → 85, glass 23 → 11, 12 room clusters 1,540 → 248). Interleaved same-session play mode,
merged vs originals: garden views 2,410–2,758 → 1,489–1,690 draws (−34 to −42 %), indoor rooms
−29 to −48 %; `Camera.Render` at the worst view −5.5 / −6.6 ms against 1.3 ms noise (only
interleaved repeats were stable: un-interleaved samples drifted ±3 ms). Triangles rose 2–14 %
(one room +44 %): a merged room is frustum- and occlusion-culled as one object.
Same-camera captures: ≤ 0.075 % pixels changed, none > 8 codes.

## Grouping rules

Merge a group only when every member shares all of:

1. **Room / culling cell.** Never across rooms or floors. A merged mesh is culled as one object;
   a floor-wide merge defeats occlusion culling and makes indoor views slower. The room is the
   culling unit. Big rooms: split further by a ~10–15 m grid.
2. **Material** (the same `sharedMaterial`, not just the same shader). One merged renderer per
   material; a multi-material merge still costs one draw per submesh.
3. **Lightmap index** (baked) or **probe-lit** status (with the same anchor / probe usage).
   **Probe-lit members** merge only when their light-probe radiance agrees: relative difference
   ≤ 3 % (absolute 0.0005), sampled at each member's own probe anchor; the merged piece uses the
   seed member's anchor. Without that gate one-SH sampling of a long merged rail changed whole
   bands of pixels.
4. **Reflection-probe zone** (same blended probes), or reflections visibly change.
5. **Static, opaque, non-interactive.** Exclude pickups, object sync, anything an Udon script
   moves, toggles or reads (games, pens, video, doors, toggles, lie-down colliders), skinned
   meshes, particles, water/ripple surfaces, mirrors, UI/TMP, animated objects.

## Opaque recipe (no bake)

1. For each source renderer, copy its mesh into the group's space (`localToWorldMatrix`, then the
   merged root's `worldToLocalMatrix`), keeping normals, tangents and UV0.
2. **Bake the lightmap placement into UV2**: `uv2' = uv2 * lightmapScaleOffset.xy +
   lightmapScaleOffset.zw` per source vertex, then give the merged renderer the same
   `lightmapIndex` and `lightmapScaleOffset = (1, 1, 0, 0)`. The merged mesh samples exactly the
   texels the originals sampled, with no re-bake.
3. Bakery applies lightmaps at load from its storage component (`ftLightmapsStorage`), not from
   the serialized renderer: register each merged renderer there with the same index and scale
   offset (the precedent rebind script pattern), or it renders unlit in game. Progressive-baked
   worlds use `Lightmapping` data directly; verify the renderer's values persist after a save and
   a scene reload.
4. Use `IndexFormat.UInt32` past 65k vertices. Recalculate bounds.
5. **Keep the originals**: disable only their `MeshRenderer` (never the GameObject; colliders,
   scripts and children keep working), and mark the merged objects static with the same flags.
   Store a rollback JSON (renderer path → original enabled state, merged asset paths).
6. Re-bake **occlusion culling** (fast, CPU, not lighting). New renderers missing from the
   occlusion data are never occlusion-culled, so indoor views get worse until it is re-baked.
7. Generated geometry (a builder script, a light-rail generator) recreates sources: make the
   merge a re-runnable editor command and note it next to the generator.

### Light-emitting meshes (Bakery Light Mesh, emissive diffusers)

The bake reads the source renderers. Keep the light-mesh components on the originals and provide
an editor menu that swaps originals ↔ merged ("show originals for bake" / "use merged"); run it
before and after every bake, and document it in the project's `AGENTS.md`.

## Transparent glass: coplanar and same-facing only

Unity draws transparent objects one by one, sorted back to front, so a glazing system split per
pane costs one draw per pane face. Merging can only keep the look when the sort order cannot
change: group panes that are **coplanar (same plane within a few mm), face the same way, share
material and fall in the same reflection-probe zone**. Panes on one flat wall never overlap from
any viewpoint, so their internal order does not matter.

**Proven failure:** a merge that grouped panes from different facades/directions (55 panes into
13 meshes) changed the garden, fire-pit and library views by 0.7–1.0 % of pixels in coherent
reflection and transparency bands. It was rejected and reverted. Never merge transparent pieces by
material and probe alone.

**Inner/outer faces.** Glass modelled as two faces (an inside face lit by the room probe, an outside
face by the exterior probe) keeps its draw order only when the inside and outside merges contain
**identical pane sets**: pair them before merging, and drop a whole pane from both sides when either
face fails the probe check. A mismatched set re-sorted inside/outside layers and changed 1–2 % of
the lounge glass.

**Only nearby panes** (user rule, 2026-10-13): besides same facing and coplanar, panes merge only
within one 6 m cell, taken from the pane's own position so its In and Out faces share the cell. A
merged transparent piece sorts by one centre; a 44 m strip or an L of two walls sorts its far panes
wrongly. Check glass with the faces painted bright magenta: real glass is too faint for a pixel diff
to notice a missing pane.

## Occlusion: merged furniture must not be an occluder

Umbra ignores occluders smaller than **Smallest Occluder** (Penthouse: 2.5 m). Each sofa, lamp or
cushion was below that, so it never hid anything. A merged piece ("all brass in the room") is far
bigger, so copying the first source's static flags makes a gappy cloud of furniture count as a
wall. Things seen through or past it vanish while still visible, mostly near the edge of the view.
Penthouse had 553 merged pieces flagged this way after its merges; players reported "furniture
disappears when I'm not looking straight at it" (2026-10-12).

- Merged pieces keep `OccluderStatic` only when they are shell (walls, slabs). Furniture and
  dress pieces keep `OccludeeStatic` only.
- Strip `OccluderStatic` from every cutout or transparent material (leaf cards, glass).
- Do not pad bounds to work around it. Static batching recomputes renderer bounds from the
  vertices: a padded `mesh.bounds` (7.83 m) was back to 5.83 m in play mode. Geometry padding
  moved the reflection-probe blend of 666 pieces (ceilings picking up the floor above).
- Test: render the same pose with occlusion on and off (any difference means visible things are
  being culled), then with occlusion off at the normal and at a 130° `cullingMatrix` (any difference
  means bounds are too small). **Use a 110° FOV** (user rule: closest to the headset; edge-of-view
  culling shows up best there), several yaws per point. Positive control: shrink
  one visible piece's `localBounds` and confirm the frustum test catches it. ClientSim's tooltip panel and
  stand-in avatar show up in play-mode occlusion diffs; ignore them.
- If thin gaps (a slab edge under glazing) still cull, lower **Smallest Hole** (0.25 → 0.1 m fixed
  Penthouse with smaller Umbra data).

## Occlusion authoring: bake-only occluders, areas, portals

Occlusion only stops rendering; scripts, physics and animators in a hidden zone still run (disable
zones the player is not in to save CPU). Prove every change below with the on/off and wide-
`cullingMatrix` diffs above.

- **Occluders are large, solid, opaque statics only** (walls, slabs, closed shells). Unity uses
  **LOD0's silhouette** for an occluder, so a room whose LOD0 is gappy occludes poorly whatever its
  far LODs look like.
- **Bake-only proxy occluders.** Where the real shell is gappy, thin or complex (modular kits,
  pillars with jogs, glass walls with mullions, the dense core of a hedge), occlude with plain cubes
  under one `__Occluders__` root tagged **`EditorOnly`**: `OccluderStatic` only, no collider, one
  loud material so gaps show in the Scene view. Sit them 2–5 cm inside or just behind the wall and
  a little **smaller than its exposed edges**, so they never hide something visible past a corner.
  EditorOnly objects take part in the occlusion bake and are stripped from the upload, so there is
  no enable/disable step to forget. Big EditorOnly slabs also seal zones that should never see each
  other. Verify once per project: bake, Build & Test, same-camera on/off diff.
- **Never flag an always-visible giant `OccludeeStatic`** (sky dome, ocean or ground backdrop
  plane, terrain backdrop): it is never hidden, so it only adds false positives.
- **One `OcclusionArea` per separate zone** (each teleport island, a far garden), so Umbra does not
  compute one view volume spanning the empty space between them (islands: `.omp/skills/clip-planes/SKILL.md` §4).
- **Doors:** an `OcclusionPortal` sized to the opening of a door that really opens and closes, open
  only while the door is open or the player is near (a local trigger area, as in
  [JanSharp VRCOcclusionUtils](https://github.com/JanSharp/VRCOcclusionUtils)). It needs no renderer,
  static flag or collider, acts like a toggleable box and adds little occlusion data. Verify the Udon
  exposure of `OcclusionPortal.open` before relying on it. Teleport doors need none: their rooms are
  islands.
- **Colliders never occlude**; only static renderers (and EditorOnly proxies) enter the bake.
- Occlusion is also a layout tool: a corner or dogleg in a long corridor and a wall where no view is
  wanted cut more draws than any bake setting (`layout-reviewer` criterion 9).

## Proof

- Same-camera before/after captures with stable content (downloaded images loaded or hidden in
  both states) and an unchanged-state repeat; expect < 0.01 % differing pixels for an opaque merge,
  then look at the images.
- Mature-content play-mode samples at the same viewpoints, before and after: draws, SetPass,
  `Camera.Render`, GPU, quoted against the baseline noise.
- Indoor views after the occlusion re-bake: not worse than before.
- Z-fight gate on the touched roots (the disabled originals do not render, but a stray enabled
  duplicate will fight).

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

## Per-instance data a merge destroys

Before merging instanced or prefab clumps, list what the shader derives **per object**; a merge (and static batching)
removes the object:

1. **Variation hashed from the object origin** (`unity_ObjectToWorld` translation, e.g.
   `frac(sin(dot(o.xz, float2(12.9898, 78.233))) * 43758.5453)`). Static batching already collapses it.
2. **Per-instance probe SH.** One probe per cell or an LPPV is not close enough: inside 16 m cells the SH spread was
   median 45 % (21 % at 8 m), with 26.5k clumps more than 10 % off their cell mean. Reproduce Unity's exact sample with
   `LightProbes.GetInterpolatedProbe(r.probeAnchor ? r.probeAnchor.position : r.bounds.center, r, out sh)` (SH error 0).

Fix: a world-owned shader copy that reads both from vertex data or a table. **A hash input precomputed on the CPU must
reproduce the GPU's rounding exactly**, because `sin(...) * 43758` turns a 1-ulp difference into a different value:
emulate the `dp2` fused order in double (mode 0: `p = (float)(x*H1); (float)(z*H2 + p)`) and test the candidate orders
against a reference render. Mode 0 matched on the development GPU; [INFERENCE] other vendors may differ, which only
reshuffles the tint pattern, never the geometry.

## Probe-lit single-LOD clumps: vertex-pulled cells

For thousands of GPU-instanced single-LOD clump prefabs (each one LODGroup costs main-thread time every frame, visible or
not). Builder template: `../scripts/GroundCells.cs.txt`.

- **Why not a plain merge:** baked vertex data inflates the upload and LZ4 compresses quantized vertices poorly:
  1.225 M vertices took a scene bundle 182.5 → 218.0 MB at 48 B/vertex, 205.0 MB at 28 B (F16 position, SNorm8 normal,
  UNorm16 UV, RGBM8 irradiance); vertex pulling 189.1 MB.
- **Cells:** 16 m squares by clump bounds centre, split per blended reflection-probe set, one mesh per cell, one submesh
  per material (world-owned `<name>_Cell.mat` copies on the cell shader), shadows off, `lightProbeUsage` Off (the SH
  comes from the table), no static flags.
- **Vertex format:** one `VertexAttribute.Position`, `UNorm8 × 4` = (clump index lo, clump index hi, prototype vertex,
  prototype). Bounds from the clumps (the ids carry no positions), padded 1 cm.
- **Tables** (point-sampled, clamp, no mips, 2048 texels wide, one linear texel index per item, uncompressed by
  design; audits will flag them, never compress them):
  - prototypes `RGBAFloat`, 3 texels per prototype vertex: position.xyz + u, normal.xyz + v, vertex colour;
  - clumps `RGBAFloat`, 2 texels: cell-space origin + hash input, rotation quaternion × √scale (|q|² = scale);
  - SH `RGBAHalf`, 7 texels: `unity_SHAr, Ag, Ab, Br, Bg, Bb, C` of the clump's interpolated probe.
- **Shader contract** (vertex function of a copy of the clumps' shader; material gets `_CellProto`, `_CellClump`,
  `_CellSH`, `_ProtoStride`):
  ```hlsl
  float4 CellFetch(sampler2D t, float4 ts, float i) {       // ts = _TexelSize
      float y = floor(i * ts.x); float x = i - y * ts.z;
      return tex2Dlod(t, float4((x + 0.5) * ts.x, (y + 0.5) * ts.y, 0, 0)); }
  float4 id = round(v.vertex * 255);
  float clump = id.x + id.y * 256, pv = (id.w * _ProtoStride + id.z) * 3;
  float4 p0 = CellFetch(_CellProto, _CellProto_TexelSize, pv), p1 = CellFetch(_CellProto, _CellProto_TexelSize, pv + 1);
  float4 c0 = CellFetch(_CellClump, _CellClump_TexelSize, clump * 2), c1 = CellFetch(_CellClump, _CellClump_TexelSize, clump * 2 + 1);
  float qq = c1.w * c1.w - dot(c1.xyz, c1.xyz);              // rotate by q and scale by |q|^2
  v.vertex = float4(qq * p0.xyz + 2 * dot(c1.xyz, p0.xyz) * c1.xyz + 2 * c1.w * cross(c1.xyz, p0.xyz) + c0.xyz, 1);
  v.normal = normalize(qq * p1.xyz + 2 * dot(c1.xyz, p1.xyz) * c1.xyz + 2 * c1.w * cross(c1.xyz, p1.xyz));
  v.texcoord = float4(p0.w, p1.w, 0, 0); v.color = CellFetch(_CellProto, _CellProto_TexelSize, pv + 2);
  // hash: frac(sin(c0.w) * 43758.5453); probes: evaluate the 7 SH texels at clump*7 like ShadeSH9 at the
  // (wind-bent) world normal and add as indirect diffuse with `noambient` on the surface pragma
  ```
- **Limits** (the builder refuses): ≤ 255 prototypes, ≤ 255 vertices per prototype, ≤ 65,535 clumps, uniform positive
  scale, single-LOD clumps only. Probe-lit clumps only: lightmapped ground cover would lose its lightmap.
- **Cull:** cell cull height = the cull distance of the farthest clump in the cell (its own LODGroup cull height at
  lodBias 2, 90° FOV) plus the cell radius, so no clump culls earlier than before; the cost is a band of extra far
  clumps up to ~11 m past the old cull (≤ 0.14 % of pixels). Keep cross-fade.
- **Lifecycle:** sources stay in the scene inactive + `EditorOnly` (source data, stripped from the upload); `UseOriginals`
  to edit planting, `Build` again after every planting edit and every bake.
- **Proof:** build self-check position error ~1 µm, SH error 0; same-camera diff ≤ 0.14 % of pixels > 18/255 with wind
  frozen; bundle-size A/B. ~13 point fetches per vertex can't be measured in the editor: confirm with a client capture
  on a weak GPU.

## Ground cover that reads continuous: density field, not drifts

Scattering grass in parent drifts leaves visible patches with bare ground between them. Use a coverage field instead, then feed the plants to the cell builder above. Project tool: `BoothAssets/Source/_World/Temperate/scripts/veg_plan.py` (`field_factors`, `field_weights`, `field_try`).

- **Coverage D(x, z) in 0..1** on a 1 m grid from real site factors: light (canopy share, conifer share: open gaps dense, closed canopy sparse), slope (thin above ~14 deg), moisture (distance to water: more rush and sedge), a soft path edge (worn path, a sparse 1-3 m band, then full density) and low-frequency noise (8-20 m wavelength) so density rises and falls into meadows. **Light is the dominant term and it must be steep: open sun is the densest grass in the world** (Temperate fix round 4: D = 0.08 + 0.92 o^1.3 where o = open-sky share; the first version, D = 0.40 + 0.60 o with 0.40-1.0 noise, left the lawns at 1.2 plants per m² and the woods at 0.6, so the sunny lawns looked bare while shade got as many plants; the fix gave 5.2 per m² in open sun, 0.5 in shade, and the noise only modulates 0.70-1.0 so meadows thin but never go bare).
- **Sampling:** variable-radius dart throwing. Draw candidates with probability ~ D; keep one when no kept plant is within r = sqrt(0.7 / (RHO x D)) (0.7 / r^2 = saturated random-sequential-inhibition density). Calibrate RHO to the target count with 2-3 trial runs (count is near-linear in RHO). Hard keep-outs (paths, props, spawns, a bare ring round a fire) stay as rejection tests.
- **Species** from weights that are smooth functions of the same factors (grass: open and dry, ~3 o²; woodrush or rush: shade and wet shores; low bracken: part shade). The mix cross-fades instead of forming single-species islands. Sun should be grass-dominant (79 % in Temperate round 4, a woodrush accent of ~15 % from a constant weight and the shore moisture); species weights driven by moisture alone made the shade species win every area in round 2.
- **Check the exclusions, not just D.** Hard keep-outs (fire and seat rings, path and walk-route strips, spawn and board clearings, prop boxes) are what decide how a lawn reads at the camera: draw a rejection map of the view's area (ring, path, box, water, with the planted points on top) before judging a density change. Keep them as briefed, but make the ones that only protect tall plants (view cones, thumbnail cones) skip short ground cover, and keep spawn clearings to ~1 m for tufts.
- **Short tufts may stay non-casters: decide with an A/B.** Hide the cells, render the ground looking down 35° with the plants shown and hidden: if the baked ground has no visible contact shadow under the old casting tufts (a 0.35 m tuft's low-sun shadow is smaller than a lawn lightmap texel), the new plants stay non-casters (ContributeGI off) and no re-bake is needed.
- **Cost:** a vertex-pulled clump is about 300 B of bundle (36 vertices × 4 B + 72 indices × 2 B + 88 B of tables; +9.6 k clumps = +2.8 MB raw), and the cells cost nothing measurable at the main thread (P5 with the 24.9 k cells off: ±0 ms, draws 964 → 949 with 9.6 k more clumps). Attribute before blaming the grass: switch the cells and the shrub / young roots off separately (Temperate P6: cells 0 ms, shrubs / young −1.1 ms).
- **Drifts only where clusters are natural** (ferns, tall bracken, shrubs, young trees): parent + 70-95 % same species, Clark-Evans R below 1 per species. Large crowns: put the children on a ring just outside the parent's clearance and give each member several tries, or a crowded wood never clusters.
- **Underlay:** check the terrain splat under the cover (`TerrainData.GetAlphamaps`); paint the grass layer towards 1 under high-density open cells so the carpet reads continuous with fewer instances (cheaper than more tufts). Keep the original alphamaps for rollback.
- **Proof:** a top-down image of D beside the planted points by species, same-camera before/after from eye height, and the Clark-Evans table for the drift species. Count and draw limits are unchanged: the cell builder carries the draw cost. Do not put reflection probes on the cover (BlendProbes on shrubs/young cost +320 draws at one pose; probes Off stays instanced).

## Proof

- Same-camera before/after captures with stable content (downloaded images loaded or hidden in
  both states) and an unchanged-state repeat; expect < 0.01 % differing pixels for an opaque merge,
  then look at the images.
- Mature-content play-mode samples at the same viewpoints, before and after: draws, SetPass,
  `Camera.Render`, GPU, quoted against the baseline noise.
- Indoor views after the occlusion re-bake: not worse than before.
- Z-fight gate on the touched roots (the disabled originals do not render, but a stray enabled
  duplicate will fight).

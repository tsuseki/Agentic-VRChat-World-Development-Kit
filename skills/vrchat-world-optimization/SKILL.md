---
name: vrchat-world-optimization
description: Measure and fix VRChat world performance — play-mode A/B harness, cost attribution by root and by object category, no-bake static merging (rooms, glass, railings, light hardware), outside-the-room LODs, texture caps with controlled proof, Udon per-frame cost, merged-cell vegetation, and the traps where standard counters (draw calls, tris, FPS) sign off a broken frame. Use when a world "is laggy", before/after any perf work, or when placing large amounts of repeated geometry.
---

# VRChat world optimization

Lessons proven on the Airship audit (2026-08: 20 FPS report on a weak PC → world render cost cut from ~14–18 ms CPU + 8 ms GPU to ~3.5 ms + 0.2 ms). The methods are general; use them in any world project.

Two worlds behind it: Airship (outdoor; terrain trees/grass on the slow path) and a glass-walled penthouse (2026-10: draw-call bound, ~3,000 draws seen from the garden through glass; triangles within budget, trees ~10 draws).

## Reference docs (read the one your top cost row points at)

| Doc | Use when |
|---|---|
| [references/draw-call-attribution.md](references/draw-call-attribution.md) | Every run: Frame Debugger capture with object names, draws grouped **by category** (glass, railings, lamps, games, furniture, pictures…), why named objects did not batch. Scripts: `scripts/frame_debugger_export.cs.txt` (execute_code body, play mode, paused) then `scripts/draw_categories.py events.json` |
| [references/merging.md](references/merging.md) | Draw calls too high in dense interiors: per-room merges per material and lightmap page with no lighting re-bake; probe-lit radiance gate; transparent glass coplanar-only rule with paired inner/outer faces; light-emitting meshes. Tool: `scripts/StaticMergeTool.cs.txt` (+ `scripts/MeshDecimator.cs.txt`), modes ceiling / cell / glass / lod / heavy, reversible, rollback menu |
| [references/room-lods.md](references/room-lods.md) | Rooms and heavy props seen from far away (garden, through glass): LOD0 = merged cluster, gated seam-locked decimation for LOD1/LOD2, one world-wide far distance, lodBias / VR-FOV scaling |
| [references/texture-caps.md](references/texture-caps.md) | Texture memory over budget: small-prop caps, controlled A/B/A proof at the closest reachable view |
| [references/udon-cost.md](references/udon-cost.md) | `BehaviourUpdate` ms high: per-frame Udon work, gating without breaking sync |
| [references/client-capture.md](references/client-capture.md) | Verifying a fix in the real VRChat client, fully autonomous: test-only teleport tour + PresentMon + upload guard. Scripts: `scripts/perf-capture/` |

## Rule 0: measure, never guess — and attribute before fixing

The owner's guess ("stuff on the ship") was backwards: ship + furniture ≈ 0.7 ms, while the *6-triangle* tree billboards dominated the frame. Attribute cost by **toggling one system at a time in play mode** (disable renderers / set a distance to 0 / SetActive a parent) and re-sampling. Play-mode-only changes revert on exit, so A/B is free and the scene is never modified.

## The play-mode measurement harness

FPS in-editor is capped and carries ~10 ms editor overhead — **the honest signals are `Camera.Render` CPU ms and GPU frame ms**, and they transfer to weak PCs (which multiply them severalfold). Sample via `execute_code`:

- `UnityEngine.Profiling.Recorder.Get("Camera.Render")` / `("BehaviourUpdate")` → `.elapsedNanoseconds`, enabled once, summed per frame.
- `FrameTimingManager.CaptureFrameTimings()` + `GetLatestTimings(1, t)` → `t[0].gpuFrameTime` (skip frames where it's 0).
- Draw calls / tris / batches: reflection on `UnityEditor.UnityStats` (`typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.UnityStats")`, static NonPublic props `drawCalls`/`triangles`/`batches`).
- Structure: `EditorApplication.update` callback, guard on `Time.frameCount` change, wait `Time.timeSinceLevelLoad >= 15` (world init/network settle), ~40 warmup frames, **200-frame sample**, write JSON to disk, unhook. Poll for the JSON from a background shell loop.
- **Record what content was live** (active terrain/block names, instance counts). A number without its content phase is not comparable. Measure the **worst** content phase, not the average.
- Compare back-to-back runs on the *same* content. A/B on different content is noise.

## Where the cost actually hides (counters lie)

Standard VRChat guidance (draw calls, polygons, texture MB) can pass everywhere while the frame dies. The cost hides in **how geometry is submitted**:

- **Unity terrain trees**: every instance is a per-frame main-thread cull/LOD object. 34k six-tri billboards cost ~9 ms CPU + ~7.5 ms GPU (tiny alpha-tested `Cull Off` quads overshade). Cheap meshes on a slow path.
- **Unity terrain details (grass)**: patches are built **on the main thread inside `Camera.Render`**. Measured 15.6 ms CPU + 7.8 ms GPU for tufts. `detailObjectDistance = 0` deletes the whole cost.
- **ParticleSystem world collision at quality High**: ~uncached raycasts per particle per frame. 130k particles with collision = 7 FPS / 23k draw calls; same particles without = 85 FPS. Particle *count* is nearly free; kill collision with emission-shape holes (ring with `radiusThickness`) instead.
- **glTFast/GLB sub-asset textures ship uncompressed** (RGB24 + CPU copies, bypass the importer). Never ship GLBs; re-encode to compressed Unity assets.

## The structural fix: merged static cells (the 250 m chunk recipe)

For any large repeated-geometry population (trees, rocks, props). As built on Airship: 145,864 impostors + 4,625 rocks/bushes → 762 cell objects, ~130 live at a time, one draw per cell material.

1. Keep the placement data (terrain `treeInstances`, prop lists) as **source data** — never delete it; re-run the cell bake after any vegetation edit.
2. **Grid**: divide each content tile into cells ≈ 250 m (Airship: 8×8 cells per 2000 m block). 250 m balances cull granularity against object count; the cell must be big enough that its count stays in the low hundreds per tile.
3. **Bake each cell to one mesh**: for every instance in the cell, transform its prototype mesh's vertices by the instance TRS into the cell parent's local space (terrain-tree instances are normalized 0–1 positions × terrain size + per-instance widthScale/heightScale/rotation). Hierarchy stays shallow: `Tile/Cells/c##` — one GameObject per cell, nothing nested below.
4. **One material for all species**: pack the per-species sheets into a `Texture2DArray` and put the slice index in the UV (Airship: `uv0` as Vector3, slice in `.z` — `mesh.SetUVs(0, List<Vector3>)`); bake any per-species color grading into the array slices so the merged material has no per-species state.
5. **Merge secondary populations into the SAME cell object as extra submeshes** — submesh 0 = the impostor/array material, submeshes 1..n = the prop materials, renderer materials `[impostorMat, ...propMats]`. Mechanics that bite: pad Vector2 UVs to z=0 when mixing with Vector3 UVs, keep prop tangents / give impostors default `(1,0,0,-1)`, fall back normals to `Vector3.up` for unlit impostors, set `IndexFormat.UInt32` when a cell exceeds 65k verts, and offset each appended submesh's triangle indices by the running vertex count.
6. Cells go on their **own layer with a far cull distance** just past fog/visibility extinction (Airship: 1100 m vs fog death at 1000). Then hard-disable the per-instance path (`treeDistance` / `detailObjectDistance` = 0) — those values live in BOTH the scene and any generator script; change both or a regenerate restores the cost.
7. Verify **pixel-identical** before/after screenshots (same camera; diff programmatically — expect <0.01 % differing pixels — then look at the images).
8. Meshes orphaned by a later re-merge are unreferenced and stay out of the build; deleting them is optional cleanup.

This flattens cost across content density: draw calls become ~(live cells) regardless of instance count, and per-instance CPU disappears. Statically-baked yaw is what makes it legal — camera-facing billboards can't be merged, crossed-quad impostors can.

## Judge visibility from player-reachable viewpoints only

Before optimizing (or building) small geometry, screenshot it from where players can actually be. If it reads as 1–2 px, **remove it instead of optimizing it** — the ground texture/impostor already carries the look. Prove removals with a pixel-diff A/B from player-true cameras (expect <0.5 % scattered speckle). Corollary: defects invisible from reachable views (e.g. a clipped trunk base seen only at ground level nobody reaches) are also not worth frame cost to fix.

## Decimation gate: signed volume, not triangle count

Aggressive decimation passes every tri-count metric while the mesh **caves in**. Gate on mesh volume via the divergence theorem (`sum(Dot(a, Cross(b, c)))/6` over triangles): decimated/source volume **≥ ~0.8 reads fine; ~0.5 is intersecting paper shards**. Sweep targets and take the lowest count that holds volume; a mesh that "can't" hold volume at low counts needs a higher budget, not more tuning.

Decimation also leaves **zero-length vertex normals** (sliver collapse) that render as NaN — hard (0,0,0) pixel specks that crawl and twinkle in motion. They are invisible while the mesh is dark; any later brightness lift exposes them. After decimating, sweep `normals[i].sqrMagnitude < 0.25` and repair: accumulate adjacent-face normals per *welded position*, fall back to any valid unit vector for verts only slivers reference (shading there is moot — the faces have no area). ⚠ Unity's `Vector3.normalized` returns **zero** below ~1e-5 magnitude, so scale tiny accumulations up first (1/100-scale FBX local space underflows it and the "fix" silently re-creates the defect). Save to a fresh asset path and re-verify the count is 0 from a fresh load.

## Known cull/LOD traps

- `LODGroup.size` does NOT recompute after mesh/import rescale — a 1/100 stale size culls everything at ~4 m and reads as "props never placed". Audit `size / rendererBounds.maxDim` across the whole prototype class.
- `treeMaximumFullLODCount` (default 5000–20000): instances past the cap **vanish** (eviction pop). Only relevant while the terrain-tree path is live.
- Terrain trees ignore prefab LODGroup edits until `td.SetTreeInstances(td.treeInstances, true)`.
- Baked occlusion culling is incompatible with content that moves (treadmills/sliding blocks) — it bakes at parked positions.
- Occlusion that hides visible things or culls too little: [references/merging.md](references/merging.md) "Occlusion authoring" (EditorOnly proxy occluders, never-occludee giants, Occlusion Areas per island, OcclusionPortal per real door).

## Editor numbers vs VR feel: the workstation benchmark

Editor play mode is one mono view with no avatars, IK, menus or compositor, so editor FPS says almost nothing about the headset: Airship read 81 FPS in the editor in the state that ran 20 FPS in game on a weak PC. The benchmark replaces FPS with **bands on the honest metrics**, calibrated per machine:

- Profile: `.omp/local/benchmarks/<hostname>.json` (personal, never committed; start from `.omp/local.example/benchmarks/`) — the machine, the standard editor setup the bands assume (Game view size, Scene view closed, no RDP/Parsec), GREEN/AMBER/RED edges for `Camera.Render`, GPU ms, BehaviourUpdate, draw calls, SetPass, tris, texture VRAM and upload size, the measured anchors behind each edge, and player-feedback rows.
- Grade and attribute: `python .omp/scripts/perf_grade.py --baseline a.json --baseline b.json [variant.json ...]` — bands for the baseline, then a per-system delta table from the disable-one-at-a-time runs, with deltas inside the baseline noise marked.
- GPU edges are tighter than the workspace budget because a headset renders roughly 2–3× the pixels of the editor view; the default 8 ms GPU budget passes the Airship state that played badly.
- Calibrate from players, don't extrapolate: the target is smooth on weak graphics cards, and the ground truth is player feedback (smooth / ok / laggy) the owner records in the profile's `feedback.rows`. The agent fills each row's editor numbers from the world's worst viewpoint and refits edges only by the profile's rule. Never invent a verdict or an in-game FPS.

## Reporting

State the editor FPS cap when quoting FPS; lead with Camera.Render/GPU ms deltas on the same content pair, and the benchmark band. A weak PC multiplies those times — cost *ranking* transfers, absolute FPS does not.

Performance lessons checklist: [references/lessons-performance.md](references/lessons-performance.md).

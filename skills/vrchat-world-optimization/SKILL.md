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
| [references/room-lods.md](references/room-lods.md) | Rooms and heavy props seen from far away (garden, through glass): LOD0 = merged cluster, error-bounded LOD1/LOD2 (3 mm / 12 mm in metres), per-object billboard LOD3 with keep-mesh rules, switch distances derived from the error, impostors only as the last level. Tools: `scripts/StaticMergeTool.cs.txt` + `scripts/MeshDecimator.cs.txt` + `scripts/LodBillboards.cs.txt` |
| [references/texture-caps.md](references/texture-caps.md) | Texture memory over budget: small-prop caps, controlled A/B/A proof at the closest reachable view, world-owned copies, crunch for big cutout atlases, HDR sky formats |
| [references/bundle-size.md](references/bundle-size.md) | Upload size over budget: measure with a scene AssetBundle (`scripts/bundle_size.cs.txt`), the levers ranked by measured MB |
| [references/udon-cost.md](references/udon-cost.md) | `BehaviourUpdate` ms high: per-frame Udon work, gating without breaking sync |
| [references/client-capture.md](references/client-capture.md) | Verifying a fix in the real VRChat client, fully autonomous: test-only teleport tour + PresentMon + upload guard. Scripts: `scripts/perf-capture/` |

## Rule 0: measure, never guess — and attribute before fixing

The owner's guess ("stuff on the ship") was backwards: ship + furniture ≈ 0.7 ms, while the *6-triangle* tree billboards dominated the frame. Attribute cost by **toggling one system at a time in play mode** (disable renderers / set a distance to 0 / SetActive a parent) and re-sampling. Play-mode-only changes revert on exit, so A/B is free and the scene is never modified.

## The play-mode measurement harness

FPS in-editor is capped and carries ~10 ms editor overhead. **Rank and grade by `mainThreadMs`** (PerfSample's
main-thread time; the in-game FPS factor is fitted on it). `cameraRenderMs` can read larger than main (8.36 vs 7.43 ms
at one pose) [INFERENCE: it likely includes render-job time]; editor `gpuFrameMs` can sit at a hardware floor
(0.14–0.24 ms at every pose on a fast GPU), so read the machine profile before trusting it. Sample via `execute_code`:

- `AWDK.AgentTools.PerfSample.Start/Status` (`.omp/docs/unity-tools.md`): settle 15 s, 40 warm-up, 200 frames, JSON with
  `mainThreadMs`, `cameraRenderMs`, `gpuFrameMs`, draws, SetPass, tris.
- **Several poses in one play session:** `scripts/perf_tour.cs.txt` (ClientSim teleport + look per pose, one PerfSample
  per pose × variant, progress in `SessionState`). Poses are player stand points: a capture camera can float over water
  or sit on a roof, so derive the stand point and check it with a downward raycast onto a walkable surface first.
- **Record what content was live** (active terrain/block names, instance counts). A number without its content phase is
  not comparable. Measure the **worst** content phase, not the average.
- **Quiet CPU only.** Another heavy process (a headless Blender render, a sibling agent's job) shifts identical
  baselines by ms (9.43 vs 7.82). Before every timing block check `Get-Process blender` and
  `Get-Counter "\Process(*)\% Processor Time"`; the coordinator holds heavy launches for the whole timing window. A
  `gpuFrameMs` leaving its floor mid-run (~0.15 → 2.6–4.7 ms) flags contention: discard the run. Contended runs only rank
  roots.
- **Noise floor:** back-to-back baselines differ 0.01–0.47 ms; the same pose 6.79–8.07 ms across sessions. Compare only
  within one session; two baselines per pose (`now`, `now2`); final before/after as interleaved A/B/A passes.
- **Levers already applied, or across worlds:** recreate "before" by toggling the lever off in edit mode without saving,
  one play session per state; take "after" from the saved scene reopened with
  `UnityEditor.SceneManagement.EditorSceneManager.OpenScene(path, OpenSceneMode.Single)` (discards the toggles).
- **Marker breakdown** (what the frame is made of): `scripts/marker_profile.cs.txt`. Main-thread markers with
  `Recorder.FilterToCurrentThread()`; job markers (`CalculateLightProbeSamplingCoordinates`,
  `GetLightProbeInterpolationWeights`) with `CollectFromAllThreads()`, because a main-thread sample showed no change for a
  12.5 ms/frame worker saving. Composition only: ~25 recorders inflated `Camera.Render` 6.4 → 10.5 ms, so take ms deltas
  from separate PerfSample runs.
- Compare back-to-back runs on the *same* content. A/B on different content is noise.

## Where the cost actually hides (counters lie)

Standard VRChat guidance (draw calls, polygons, texture MB) can pass everywhere while the frame dies. The cost hides in **how geometry is submitted**:

- **Unity terrain trees**: every instance is a per-frame main-thread cull/LOD object. 34k six-tri billboards cost ~9 ms CPU + ~7.5 ms GPU (tiny alpha-tested `Cull Off` quads overshade). Cheap meshes on a slow path.
- **Unity terrain details (grass)**: patches are built **on the main thread inside `Camera.Render`**. Measured 15.6 ms CPU + 7.8 ms GPU for tufts. `detailObjectDistance = 0` deletes the whole cost.
- **ParticleSystem world collision at quality High**: ~uncached raycasts per particle per frame. 130k particles with collision = 7 FPS / 23k draw calls; same particles without = 85 FPS. Particle *count* is nearly free; kill collision with emission-shape holes (ring with `radiusThickness`) instead.
- **glTFast/GLB sub-asset textures ship uncompressed** (RGB24 + CPU copies, bypass the importer). Never ship GLBs; re-encode to compressed Unity assets.
- **Thousands of single-renderer LODGroups** (GPU-instanced ground-cover prefab clumps): `LOD.ComputeLOD` plus renderer
  cull and instancing prep run for every LODGroup every frame, visible or not. 33,656 clumps cost ComputeLOD 1.69 ms
  plus ~2 ms of cull, instancing prep and `RenderForwardOpaque.Prepare` at a pose with ~41 clump draws. Draw count is
  the wrong signal (draws rose 659 → 696 after the fix while main fell 2.36 ms), and a renderers-off sweep under-reports
  it (ComputeLOD stayed 1.73 ms with the renderers off): compare marker breakdowns. Fix: cells, one LODGroup each
  (below); ComputeLOD 1.69 → 0.19 ms.
- **Lightmapped renderers on BlendProbes** still run probe sampling on worker threads every frame (10,397 renderers
  13.0 ms/frame). After every bake set `lightProbeUsage = Off` on renderers with `0 <= lightmapIndex < 65534`
  (`scripts/LightmappedProbes.cs.txt`); pixel-identical, never on probe-lit renderers.
- **Static batching on instanced LODGroup foliage** stores a combined copy of every LOD0 in the scene: 469 MB
  uncompressed in one world (394.8 → 168.2 MB build after clearing `BatchingStatic` on 5,281 renderers, draws 622 → 340).
  Instanced foliage gets instancing, not batching; no rebake needed. Prove with a play-mode diff (batching happens at play).
- **`Terrain.drawInstanced` off**: −1,400 draws at spawn over 9 tiles when turned on, terrain pixels identical.
- **No occlusion data** in a scene copied from another or a new outdoor scene: flag scatter `OccludeeStatic`, bake
  (spawn 3,346 → 1,851 batches, `Camera.Render` 24 → 9 ms), prove with the on/off diff.
- **Before the first bake** a Baked sun renders realtime shadows (7.88 M tris vs 2.6 M after): budget after the bake.

## The structural fix: merged static cells (the 250 m chunk recipe)

For any large repeated-geometry population (trees, rocks, props). As built on Airship: 145,864 impostors + 4,625 rocks/bushes → 762 cell objects, ~130 live at a time, one draw per cell material.

1. Keep the placement data (terrain `treeInstances`, prop lists) as **source data** — never delete it; re-run the cell bake after any vegetation edit.
2. **Grid**: divide each content tile into cells ≈ 250 m (Airship: 8×8 cells per 2000 m block). 250 m balances cull granularity against object count; the cell must be big enough that its count stays in the low hundreds per tile.
3. **Bake each cell to one mesh**: for every instance in the cell, transform its prototype mesh's vertices by the instance TRS into the cell parent's local space (terrain-tree instances are normalized 0–1 positions × terrain size + per-instance widthScale/heightScale/rotation). Hierarchy stays shallow: `Tile/Cells/c##` — one GameObject per cell, nothing nested below.
4. **One material for all species**: pack the per-species sheets into a `Texture2DArray` and put the slice index in the UV (Airship: `uv0` as Vector3, slice in `.z` — `mesh.SetUVs(0, List<Vector3>)`); bake any per-species color grading into the array slices so the merged material has no per-species state.
5. **Merge secondary populations into the SAME cell object as extra submeshes** — submesh 0 = the impostor/array material, submeshes 1..n = the prop materials, renderer materials `[impostorMat, ...propMats]`. Mechanics that bite: pad Vector2 UVs to z=0 when mixing with Vector3 UVs, keep prop tangents / give impostors default `(1,0,0,-1)`, fall back normals to `Vector3.up` for unlit impostors, set `IndexFormat.UInt32` when a cell exceeds 65k verts, and offset each appended submesh's triangle indices by the running vertex count.
6. Cells go on their **own layer with a far cull distance** just past fog/visibility extinction (Airship: 1100 m vs fog death at 1000). Then hard-disable the per-instance path (`treeDistance` / `detailObjectDistance` = 0) — those values live in BOTH the scene and any generator script; change both or a regenerate restores the cost.
7. Verify **pixel-identical** before/after screenshots (same camera; diff programmatically — expect <0.01 % differing pixels — then look at the images). In foliage worlds make captures deterministic first: one persistent capture camera (never destroyed after `Render()`); every `LODGroup.fadeMode = None`, restored afterwards; wind frozen with a MaterialPropertyBlock (`_WindSpeed` = `_FlutterSpeed` = 0) on renderers whose `shader.name.Contains(<wind shader>)`, so cell and world copies freeze too; animated water and `ParticleSystemRenderer`s hidden (`forceRenderingOff`). Per pose an eye-height view, a look-down view (pitch 25°) and a back view, 1280×720 at 77.4° vertical FOV (≈ 110° horizontal). Two consecutive "before" sets must match at 0 px; report the % of pixels with summed RGB difference > 18 plus "any change". `SetPropertyBlock(null)` clears other systems' blocks too, and the fadeMode toggle dirties the scene: reopen it or re-save in edit mode.
8. Meshes orphaned by a later re-merge are unreferenced and stay out of the build; deleting them is optional cleanup.

This flattens cost across content density: draw calls become ~(live cells) regardless of instance count, and per-instance CPU disappears. Statically-baked yaw is what makes it legal — camera-facing billboards can't be merged, crossed-quad impostors can.

### Probe-lit single-LOD clumps: vertex-pulled cells

Hand-placed GPU-instanced clump prefabs (ground cover, grass, small plants; one renderer and one single-LOD LODGroup
each) are the same CPU problem at smaller scale: merge them into **16 m cells**, one LODGroup per cell, split per
blended reflection-probe set, one submesh per material. A plain vertex merge loses what the shader derived per object
(origin-hashed tint, per-instance probe SH) and bloats the bundle (1.225 M vertices: 182.5 → 218 MB), so the cells
carry 4-byte vertex ids and rebuild each clump in the shader from point-sampled tables (189.1 MB). Measured: 12,537
clumps → 142 cells, main 5.54 → 4.22 ms, draws 535 → 294. Builder: `scripts/GroundCells.cs.txt` (`Build`,
`UseOriginals`, `UseCells`, `Remove`); shader contract and limits: [references/merging.md](references/merging.md)
"Probe-lit single-LOD clumps: vertex-pulled cells". Sources stay in the scene inactive + `EditorOnly`; **rebuild after
every bake** (the SH table copies the baked probes) and every planting edit. Probe-lit clumps only (a lightmapped clump
would lose its lightmap). Confirm the GPU side (~13 point fetches per vertex) with a client capture on a weak GPU.

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

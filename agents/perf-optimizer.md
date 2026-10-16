---
name: perf-optimizer
description: >-
  D.2 of the world pipeline: measures and optimizes VRChat world performance in the open Unity editor: play-mode frame sampling
  (Camera.Render CPU ms, GPU ms, draw calls, SetPass, tris), a per-component attribution sweep that
  disables one part of the world at a time and reports what each part costs in draw calls, ms, tris
  and texture memory, graded against the workstation benchmark that maps editor numbers to in-VR
  feel; then applies REVERSIBLE fixes (LODs, texture compression and size, cull distances, static
  batching, cell merging, occlusion) proven by same-camera pixel diffs. Asks before destructive
  changes (deleting, decimating). PASS: (1) project + scene, (2) WORLD.md path, (3) player
  viewpoints or spawn, (4) target budget if different from the defaults in "Default budgets" below,
  (5) scope: measure-only or measure+fix.
---

# Performance optimizer

Read `.omp/skills/vrchat-world-optimization/SKILL.md` first: it holds the measurement harness, the
cost traps, the merged-cell recipe and the decimation gate, and indexes the reference docs
(category attribution, no-bake merging, room LODs, texture caps, Udon cost); open the reference
for each top cost row before fixing it. Then the project's `AGENTS.md`,
`WORLD.md`, and the benchmark profile for this machine, `.omp/local/benchmarks/<hostname>.json`
(`hostname` in a shell; personal, never committed to the kit). No profile for this host: measure
and attribute as usual, but give no in-VR feel verdict.

## Rule 0: attribute before you fix

Owners' guesses about what is slow have been backwards (the 6-triangle billboards, not the
furniture). Never optimise what you haven't measured, and never report a world total without the
per-component table that explains it.

## Default budgets (user rules)

PC defaults for pipeline stage D.2 and any perf check. The user may override them for a specific
world; the override and the user's words go in that world's `WORLD.md` Decisions log, and you then
follow `WORLD.md`.

- **At most 3 M triangles visible from any player viewpoint.** Budget worst-case sightlines;
  enforce with occlusion culling, far clip, LODGroups, decimation and sightline seals; check during
  area reviews.
- Per player viewpoint, measured with `PerfSample` in play mode: visible triangles ≤ 3 M,
  `Camera.Render` CPU ≤ 4 ms, GPU frame ≤ 8 ms, draw calls ≤ 1000 (≤ 500 preferred); texture VRAM
  estimate ≤ 400 MB; upload size ≤ 200 MB.
- Compressed textures; mirrors start off. Attribute cost before optimizing (Rule 0,
  `.omp/skills/vrchat-world-optimization/SKILL.md`).
- Android/iOS build (when WORLD.md plans one): use the Android budgets table in
  `.omp/skills/vrchat-android-worlds/SKILL.md` §4; these PC defaults still govern the PC build.

Budgets are pass/fail. The benchmark bands (below) are tighter on GPU and predict how the world
will feel in a headset; report both. Where a number passes the budget but is RED in the benchmark,
say so explicitly: the Airship state that ran 20 FPS in game passed every budget except CPU ms.

## Editor numbers vs how players feel it

The target is **players on weak graphics cards finding the world smooth**. Editor play mode renders
one mono view with no avatars, IK, menus, voice or headset compositor on a fast workstation, so
editor FPS overstates in-game smoothness badly (Airship: editor 81 FPS, a weak PC in game 20 FPS).
Never quote editor FPS as a verdict; it is capped near 90 on the workstation.

- Grade every sample with `python .omp/scripts/perf_grade.py` against the profile's bands:
  **GREEN** = in the range of worlds players called smooth/ok, **AMBER** = between, **RED** = in the
  range of a world players called laggy. The bands only hold under the profile's `standardSetup`
  (Game view size, Scene view closed, no RDP/Parsec); state any deviation.
- **Report every editor timing as in-game FPS too** (user, 2026-10-14: "report in those fps always
  from now on"). `perf_grade.py` prints it: in-game desktop FPS ≈ 1000 / (1.12 × editor
  `mainThreadMs`) (profile `machine.editorToInGame`), placed among the user's 8 reference worlds
  (the profile's `machine.editorToInGame.scale`, `reference: true`). For a spot that
  has an in-game measurement, scale from it instead (in-game FPS × baseline / variant main thread),
  which cancels editor drift between sessions. Quote the FPS first, then the raw editor stats.
  Method, the scale, the translation pairs, past experiments and capture gotchas:
  `.omp/local/benchmarks/ingame/README.md`; read it before measuring or capturing in game.
- Ground truth is player feedback the owner relays as `feedback.rows` (smooth / ok / laggy, with
  their words). **Never invent a row, a verdict or an in-game FPS.** When you work in a world that
  has a row with `editor: null` or `pending`, sample its worst player viewpoint under
  `standardSetup`, write the numbers and the JSON path into that row, and refit bands only by the
  profile's refit rule. Report any refit with the rows that justify it.

## Procedure

1. **Setup and baseline.** Apply the profile's `standardSetup`. Enter play mode, wait for ClientSim
   to initialize. For each viewpoint: move the ClientSim player (or the main camera if there is
   none) to the exact position and look direction via `execute_code`, wait a few frames, then
   `PerfSample.Start(outJson)` / poll `PerfSample.Status()` (15 s settle, 40 warm-up, 200 frames).
   Record the exact pos/look and **which content was live** (active roots, treadmill phase,
   instance counts) so every later sample reuses them. Sample spawn, the busiest room and the
   longest sightline; the worst viewpoint is the one you attribute. Take a second baseline at the
   end of the session: the two give the noise floor.
2. **Exact draw-call listing** (one frame, at the worst viewpoint). Enable the Frame Debugger
   (`manage_profiler` `frame_debugger_enable`, then page `frame_debugger_get_events`) and group the
   events by the GameObject/renderer they name, mapped to its top-level root. This gives exact
   draws per component, including the ones dynamic batching or instancing merged. The events are
   read by reflection, best-effort: if they carry no object names, say so and rely on step 3.
   Also group the same events **by object category** (glass, frames, railings, light fixtures,
   games, furniture, pictures, plants…) with `scripts/draw_categories.py` and report that table
   next to the by-root one; owners act on categories (references/draw-call-attribution.md).
   Disable the Frame Debugger before sampling anything (it freezes the frame).
3. **Attribution sweep** (play mode only; every change reverts on exit).
   - **Level 1**: one PerfSample per top-level root, with that root's renderers off
     (`PerfSample.Start(out, 15, 40, 200, "Root/Path")`). Then each system that is not a renderer
     under one root: terrain trees/details (zero the distances), particle systems (including
     their collision), water, mirrors, video players, UdonBehaviours, reflection probes,
     post-processing. `disableRootsCsv` covers renderer cost only; toggle those yourself via
     `execute_code` between samples and re-enable afterwards.
   - **Level 2, drill down**: any system costing ≥ 10 % of baseline draw calls, ≥ 0.5 ms
     `Camera.Render` or ≥ 0.5 ms GPU gets the same sweep over its children, recursively, until
     one leaf explains the cost (a material, an object class, a terrain setting). Stop a branch
     when its children each cost under the noise floor.
   - **Texture memory per component** (no rendering needed): for each root, collect the unique
     textures referenced by its renderers' materials and sum `Profiler.GetRuntimeMemorySizeLong`
     (play mode) or the imported size; textures used by more than one root go in a `shared` row.
     Flag uncompressed formats, missing mipmaps and textures > 2048 on small props.
   - Build the table with `perf_grade.py --baseline first.json --baseline last.json <variant
     JSONs> --label file.json=Name` (name the hand-toggled variants); `--sort drawCalls` by
     default, `--sort cameraRenderMs` or `gpuFrameMs` when the bands say time is the problem.
     Deltas inside twice the baseline noise are marked `~`; do not rank by them.
4. **Static audits** (edit mode, read-only):
   - Visible tris per viewpoint ≤ **3 M**, and the other "Default budgets" above unless WORLD.md
     overrides them; list the top 20 renderers by tris.
   - Textures: size vs on-screen size, compression format (uncompressed RGB24/RGBA32 is a finding;
     GLB-embedded textures bypass compression), mip maps, aniso; total VRAM estimate (grade it with
     `--static textureVramMB=<n>`).
   - Materials and draw calls per area; missing static flags; LODGroups with stale `size`;
     realtime lights (must be 0); mirrors on by default (should start off).
   - **Animators on static props**: count `Animator` components under static roots (rigged or
     animated FBX, avatar prefabs). One with no controller or no clips costs CPU every frame for
     nothing: list them, measure the delta with the attribution sweep, and fix at the importer
     (Rig → Animation Type None, Import Animation off).
     Removing the components is a delete: ask first.
   - **Upload size** (≤ 200 MB): attribute it per asset with VRWorld Toolkit's Build Report, and
     diff before/after builds with its Build Report Comparison (skill references/texture-caps.md
     "Upload size"). Size and frame cost are separate findings; never quote one for the other.
5. **Fix**, cheapest wins first, only after showing the attribution table, aimed at the top rows.
   Allowed without asking (reversible): texture max size / compression / mip settings, LODGroup
   add/tune, cull distances and layer cull distances, static flags, occlusion bake, disabling
   per-instance terrain paths when replaced, merged static cells (keep the source data). **Ask the
   orchestrator first** for: deleting objects, decimating meshes, changing materials' look.
6. **Prove each fix**:
   - Performance: re-run the same viewpoint sample on the same content; quote before/after values
     and both bands from `perf_grade.py`.
   - Visuals: same-camera before/after screenshots, programmatic pixel diff (expect < 0.5 %
     scattered speckle for removals, < 0.01 % for merges), **then look at both images**.
   - Decimation: signed-volume ratio ≥ 0.8 and zero-length normals swept to 0.
   - Client check: after structural fixes (merges, LODs, Udon gating), confirm in the real VRChat
     client with the autonomous Build & Test capture (skill references/client-capture.md),
     originals vs fixed, and quote both. Editor numbers alone do not close a structural fix.

## Report

1. Setup line: host, profile, Game view size, viewpoints with pos/look, content phase.
2. Baseline table per viewpoint: value, band and budget verdict per metric.
3. Frame Debugger draw listing by root (or why it was unavailable).
4. Attribution table (`perf_grade.py` output), drilled down to the leaves that explain the cost,
   plus the texture-memory-per-component table.
5. Fixes applied (each with deltas and diff %) → fixes proposed but needing approval → final
   numbers vs budget and bands.
6. Player feel: the band verdict, the feedback rows it rests on, and rows you filled or refits you made.

Lead with ms and draw calls, not FPS. Any fix that changed pixels beyond speckle goes back to
`final-reviewer` (D.2 visual regression check).

**Loop back to C.** A cost whose fix is a build change (replacing or remodelling an asset,
re-dressing an area, changing geometry or materials' look) is not yours to make: report it as a
→ C item (area, cause, proposed fix, expected saving) for a world-builder C pass; after it lands,
re-measure the affected viewpoints.

**Trial runs:** append an `attempt` event per fix tried (what, result with the metric deltas,
before/after image paths), a `timing` event per sampling pass and a `loop_back` event (stage, id,
to, reason) per → C item to `<project>/Trial/log.jsonl` with
`.omp/skills/pipeline-trial/scripts/trial_report.py --append`; schema in
`.omp/skills/pipeline-trial/SKILL.md` "Event log".

## Lessons that cost a session (Penthouse, 2026-10)

Details and evidence: the skill's `references/merging.md`.

- **Runtime hiding uses `renderer.forceRenderingOff`.** Toggling `enabled` or `SetActive` in play
  splits static batches for the rest of the session (library 253 → 375 draws after one garden visit).
  Likewise, a measurement sweep never toggles anything; measure each state in its own play session.
- **Merged furniture is never `OccluderStatic`.** Each source was below Smallest Occluder; the merged
  piece is not, so gappy furniture starts hiding visible things (player report: "furniture disappears
  when I'm not looking at it"). Only shell pieces occlude; strip the flag from cutout and glass too.
- **Culling complaints get the two-diff test first** (occlusion on/off; normal vs wide
  `cullingMatrix`, with a shrunk-bounds positive control) before anyone pads bounds. Padded
  `mesh.bounds` does not survive static batching, and bigger renderer AABBs change reflection-probe
  blending.
- **Smallest Hole 0.1 m** fixed thin-gap false culls and gave fewer draws and smaller data than 0.25 m.
- **Test views use a 110° FOV** (user directive 2026-10-13): it matches the headset's real field of
  view best and shows edge-of-view culling that a 60–90° desktop camera hides. Culling tests, capture
  sweeps and before/after renders all default to 110°; quote any other FOV explicitly.

## Safety

- Exit play mode when done; confirm `EditorApplication.isPlaying == false`.
- Never save the scene while in play mode. Save edit-mode fixes with `MarkSceneDirty` + save.
- `execute_code` freezes the editor; keep calls short and time-boxed; long samples run through
  `PerfSample` (an `EditorApplication.update` job writing JSON), polled with `Status()`.
- Leave the Frame Debugger disabled, and sweep `__*__` objects you created before handing back.

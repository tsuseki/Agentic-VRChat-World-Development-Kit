# Unity agent tools (`com.awdk.agenttools`)

An Editor-only UPM package in [.omp/unity-package/com.awdk.agenttools/](../unity-package/com.awdk.agenttools/).
Install: [bootstrap.md §3](bootstrap.md#3-wire-it). No hard dependency on the VRChat SDK (VRC types
are resolved by name via reflection), so it compiles in any 2022.3 project.

## Conventions

- Namespace `AWDK.AgentTools`. Every entry point is static and returns a plain-text
  report; call it from the MCP `execute_code` tool:
  `return AWDK.AgentTools.ZFightScan.Status();`
  The wrapper's C# traps (ambiguous `Object`, unqualified `EditorSceneManager`, blocked text patterns) and the
  one-`delayCall` launch for editor-blocking jobs: `.omp/skills/unity-mcp-scripting/SKILL.md` §2–§3.
- **Two-phase async.** Long work never blocks the editor more than ~2 s per call: `Start(...)`
  returns `STARTED ...` and the work is time-sliced on `EditorApplication.update`; poll `Status()`
  until it returns the final report. A timed-out MCP call is re-polled, never re-started (the idea
  comes from [Atelier](https://github.com/Ryan6-VRC/atelier)'s two-phase tools).
- Read-only unless stated. Numbers are parsed and printed with `InvariantCulture`.
- Paths: `rootPath` is a hierarchy path (`Building/Floor1`); `null` = whole loaded scene.

## ZFightScan: geometric z-fighting gate

```
ZFightScan.Start(string rootPath = null, float planeEps = 0.0015f, float minOverlapArea = 0.0004f,
                 bool includeSelf = false, bool includeOppositeFacing = false)   // → "STARTED ..."
ZFightScan.Status()   // → "STATE=running progress=.." or the report ending "PAIRS=<n> COMPLETE"
ZFightScan.RunBlocking(..., double maxSeconds)   // tests only
```

Finds same-facing coplanar triangle pairs from different renderers (or the same renderer with
`includeSelf`) whose overlap area ≥ `minOverlapArea` m². A hierarchical uniform grid (exact far from
the origin) and per-renderer groups keep it near-linear; overlap is measured by 2D polygon clipping. Each pair lists both
object paths, the plane and the overlap area. Gate: fix every pair ≥ 4 cm² on a player-visible
surface, re-run until `PAIRS=0 COMPLETE`. Only a report ending `PAIRS=0 COMPLETE` is clean. Other
endings mean re-run: `PAIRS=<n> PARTIAL (cancelled)` or `PARTIAL (superseded by a new Start())`
(someone else started a scan, so never start a second one while one is running), `ABORTED ...`,
`ERROR ...`, or `STATE=idle ...` (a script reload dropped the job). `ZFightScan.Cancel()` stops a
running scan.

Cost: a whole large outdoor world took ~330 s. When verifying a fix, scan only the roots you changed.

## ZFightRender: image-based z-fighting detector

```
ZFightRender.Start(string outDir, string shotsJson)
ZFightRender.Status()
```

Same `shotsJson` as `WorldCapture`. For each shot, draws every visible opaque MeshRenderer
off-screen in a flat per-renderer ID colour, in two passes: (1) the visible surface per pixel (ID +
linear eye depth, normal depth test); (2) every fragment of a *different* renderer whose eye depth is
within the tie tolerance of the visible surface is flagged with its ID. The tolerance at eye depth
`d`, with `C` the largest per-axis |coordinate| of the shot's camera, is
`tol = max(MinTolerance, DepthSteps * e)` where `e` depends on `DepthFormat`:

- `ZDepthFormat.Float32ReversedZ` (default; VRChat PC, measured D32_SFloat reversed-Z on 2022.3
  D3D11): `e = 2^-24 * C + 2^-23 * d`, float32 position rounding plus float depth precision,
  independent of the near clip. It bounds every separation measured in
  [clip-planes-and-precision.md](../skills/clip-planes/references/clip-planes-and-precision.md) §2.3.
- `ZDepthFormat.Fixed24` (conservative; Android/Quest and other non-reversed platforms):
  `e = 2^-24 * C + d² / (NearClip * 2^24)`.

Defaults: `DepthFormat = Float32ReversedZ`, `NearClip = 0.01` (used only by `Fixed24`; VRChat clamps
the runtime near to 0.001–0.05 m), `DepthSteps = 2`, `MinTolerance = 0.05 mm`. All are public static
fields. `ZFightRender.Tolerance(d, cameraCoord = 0)` returns the value.

| Camera | 1 m | 4 m | 20 m | 100 m |
|---|---|---|---|---|
| PC, at origin | 0.05 mm | 0.05 mm | 0.05 mm | 0.05 mm |
| PC, C = 500 m | 0.060 mm | 0.061 mm | 0.064 mm | 0.083 mm |
| Fixed24, near 0.01, at origin | 0.05 mm | 0.19 mm | 4.8 mm | 119 mm |

On PC only exactly or effectively coplanar pairs are flagged. It does not re-render at nudged
near/far planes: measured, that flips only ~0.2 % of a coplanar overlap. Writes `<name>_zmask.png`
(z-fight pixels magenta) and reports the tolerance model, then per shot pixel counts, bounding boxes,
`tol@20m` and renderer pairs, ending
`SHOTS=<n> ZFIGHT_PIXELS=<total> COMPLETE`. Not covered: skinned meshes, terrain, particles,
transparent queues; overlaps inside one renderer need `ZFightScan` with `includeSelf`. Use both:
the scan finds every coplanar overlap, the render shows which are visible.

## WorldCapture: screenshots

```
WorldCapture.Shoot(string outDir, string shotsJson)
WorldCapture.Status()
```

`shotsJson`: `[{"name":"01_wide","pos":[x,y,z],"look":[x,y,z],"fov":60,"w":1600,"h":900}]`, with optional
`"near"` / `"far"` (defaults 0.03 / 1000; other defaults fov 60, 1600×900, max 8192 px per side). Poll `Status()`
until the report ends `SHOTS=<n> COMPLETE`. Uses one persistent `__CapCam__` (destroying a camera after `Render()`
crashes the editor), renders with occlusion culling off (baked occlusion data still holds moved statics at their old
bounds) and adds no lights. PNGs land in `outDir/<name>.png`. Sweep `__*__` objects before saving the scene.

- **Quoting JSON inside `execute_code`:** write it with single quotes in the C# string and convert:
  `WorldCapture.Shoot(dir, "[{'name':'01','pos':[0,1.3,0],'look':[0,1.3,5]}]".Replace('\'', '"'))`.
- **LOD cross-fade is not settled.** Freshly registered LODGroups start mid-fade and a capture camera's fade state can
  follow the editor camera, so trees show grey dither right after a camera jump. Before a shot pass set every
  `LODGroup.crossFadeAnimationDuration = 0.001f` and take 2–3 throwaway shots of the first pose; restore 0.5
  afterwards. For before/after pixel diffs set every `LODGroup.fadeMode = None` and restore it after `COMPLETE`
  (recipe: `vrchat-world-optimization` SKILL.md "The structural fix" step 7).

## PerfSample: play-mode performance

```
PerfSample.Start(string outJson, float settleSeconds = 15, int warmupFrames = 40, int frames = 200,
                 string disableRootsCsv = null)
PerfSample.Status()
```

Play mode only. Waits `settleSeconds`, skips `warmupFrames`, then samples `Camera.Render` and
`BehaviourUpdate` recorders, GPU frame time (FrameTimingManager), and draw calls/batches/tris
(UnityStats via reflection). Writes `outJson`. Mutates only during play mode, which reverts on exit.

- **Rank by `mainThreadMs`** (the JSON also holds `cpuFrameMs`, `cameraRenderMs`, `behaviourUpdateMs`, `gpuFrameMs`,
  draws, batches, SetPass, tris); the in-game FPS factor in `perf_grade.py` is fitted on it. `gpuFrameMs` can sit at
  a hardware floor in the editor; a run where it jumps off that floor mid-run was contended by another process:
  discard it.
- **Several poses in one play session:** `.omp/skills/vrchat-world-optimization/scripts/perf_tour.cs.txt`.

- **It measures whatever cameras render.** It takes no camera or position. For a viewpoint sample,
  first (in play mode, via `execute_code`) move the ClientSim player, or the main camera if there
  is no player, to the viewpoint's position and look direction; close or minimise the Scene view
  (it renders too); then call `Start`. Use the same position/look for every A/B sample.
- **`disableRootsCsv` covers renderer cost only**: it sets `Renderer.enabled = false` under each
  root. UdonBehaviours keep updating, particle systems keep simulating (including world
  collision), and reflection probes and post-processing volumes aren't renderers. To attribute
  those, disable the GameObjects or components yourself via `execute_code` in play mode between
  samples, and re-enable them afterwards.

## WorldAudit: rule checks

```
WorldAudit.Run(string rootPath = null)
```

Reports, with object paths: `VRCStation`/`VRC_Station` components; `VRC_Pickup` with proximity ≠
0.1 or AutoHold ≠ No; realtime or Mixed lights; leftover `__*__` objects; MeshColliders on likely
walkable surfaces; colliders on props; static renderers missing UV2; uncompressed textures on
scene materials. Read-only; quick enough to run synchronously.

Expected findings, not defects: point-sampled data textures that a tool keeps uncompressed by design (e.g. the
merged-cell tables `RGBAFloat`/`RGBAHalf` of `vrchat-world-optimization` `scripts/GroundCells.cs.txt`). Never compress,
resize or mip them; list them as expected in the report.

The prop-collider check depends on names: it flags colliders only under an ancestor whose name
contains `Prop`/`Props`, `Dressing`, `Furniture`, `Decor` or `Clutter` as a separate word
(`Lounge/Props`, `Lounge_Decor`; not `LoungeProps`). Dressing must therefore live under
`<Area>/Props` (or `<Area>/Dressing`); a prop placed elsewhere is invisible to the check.

Two prop colliders are allowed, both recognised by name:

- `LieDownCollider`: a child GameObject of a bed, couch or cuddle platform with a `BoxCollider` on
  its top surface, inactive or disabled in the saved scene and switched on by the world's lie-down
  toggle. Counted on an informational `[LIE_DOWN_COLLIDERS]` line. An enabled one, a trigger, or a
  non-Box collider with that name is a `PROP_COLLIDERS` finding. The audit counts the colliders and checks their
  on/off state only; it does **not** check that every `LieDownCollider` is listed in the world toggle's
  `lieDownColliders` array or that the array has no null entries: check both by script (count in scene = count in
  the toggle's list, 0 nulls).
- `SolidCollider`: a child GameObject of big furniture (big tables, counters, cabinets, wardrobes,
  bookcases) with one always-on `BoxCollider` from the floor to the top surface. Counted on an
  informational `[SOLID_FURNITURE_COLLIDERS]` line. A disabled or inactive one, a trigger, or a
  non-Box collider with that name is a `PROP_COLLIDERS` finding. The audit can't tell big furniture
  from small; the dressing-reviewer checks that.

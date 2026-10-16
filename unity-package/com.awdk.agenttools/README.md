# AWDK Agent Tools

Editor-only Unity package (`com.awdk.agenttools`) with checks that a coding agent runs
while it builds a VRChat world: geometric and render-based z-fighting detection, review captures,
a play-mode performance sample and a world audit.

- Unity 2022.3 (tested on 2022.3.22f1), Built-in render pipeline, PC.
- Editor assembly only (`AWDK.AgentTools.Editor`): nothing ships in an upload.
- No dependency on the VRChat SDK: SDK components are matched by type name through reflection.
- Read-only unless a method says otherwise. Every report uses invariant culture (`.` decimals)
  whatever the editor locale.

## Install

Add the package as a local package in the world project's `Packages/manifest.json`:

```json
"com.awdk.agenttools": "file:<workspace>/.omp/unity-package/com.awdk.agenttools"
```

(an absolute path, so it works from any project depth; use forward slashes), or use
**Window > Package Manager > + > Add package from disk...** and pick `package.json`.

## Calling convention

Every entry point is a static method that returns plain text, made to be called from the Unity MCP
`execute_code` tool:

```csharp
return AWDK.AgentTools.WorldAudit.Run();
```

Long work never runs inside the call. `Start(...)`/`Shoot(...)` validate the arguments, schedule a
job and return `STARTED ...` (or `ERROR ...`) immediately. The job runs in slices of about 150 ms on
`EditorApplication.update`, so the editor stays responsive and no call blocks for more than a slice.
Poll the matching `Status()`:

- `STATE=running progress=... slices=... maxSliceMs=... elapsed=...` while it runs. Each `Status()`
  call also advances the job by one slice, so polling makes progress even when the editor window
  is in the background.
- the final report once done. Reports end with a fixed last line (`... COMPLETE`, or `ERROR ...`).
- `STATE=idle ...` when no job of that kind exists. Jobs are kept in memory only: a script
  recompile or a play-mode domain reload drops them, so start again after either.

Starting a new job of the same kind supersedes a running one. Shared plumbing lives in
`JobRunner` (`JobRunner.SliceBudgetMs`, `JobRunner.Cancel(kind)`).

### Shots JSON

`WorldCapture` and `ZFightRender` take the same shot list:

```json
[{"name":"01_wide","pos":[0,1.6,-6],"look":[0,1.2,0],"fov":60,"w":1600,"h":900}]
```

`name` is the file name stem; `fov` defaults to 60, `w`/`h` to 1600x900, optional `near` (0.03)
and `far` (1000). `outDir` is absolute or relative to the project folder; it is created if missing.

## ZFightScan: geometric z-fighting

Finds triangles of opaque MeshRenderers that face the same way, lie in the same plane within
`planeEps` and overlap. Reports renderer pairs whose summed overlap area is at least
`minOverlapArea` m², largest first, with both object paths, materials and a sample point.

```csharp
return AWDK.AgentTools.ZFightScan.Start();                       // whole scene
return AWDK.AgentTools.ZFightScan.Start("Building/Floor2");      // one subtree
return AWDK.AgentTools.ZFightScan.Start(null, 0.0015f, 0.0004f, true, false); // includeSelf
return AWDK.AgentTools.ZFightScan.Status();
```

Signature: `Start(string rootPath = null, float planeEps = 0.0015f, float minOverlapArea = 0.0004f,
bool includeSelf = false, bool includeOppositeFacing = false)`.

- `rootPath`: `Root/Child/...` in any loaded scene; null scans every loaded scene.
- `includeSelf`: also test triangles of one mesh against each other (duplicated or folded faces).
  Neighbouring triangles that share vertices are never counted.
- `includeOppositeFacing`: also count back-to-back coplanar faces; only matters for Cull Off
  materials.

Skipped: disabled or inactive renderers, `ShadowsOnly` renderers, EditorOnly-tagged objects,
transparent submeshes (render queue > 2500), and pairs of renderers that are different LOD levels
of one LODGroup (they never draw together). SkinnedMeshRenderers are not scanned.

The final report has a header (`renderers`, `tris`, `narrowTests`, timing: `slices`, `maxSliceMs`),
one entry per pair (`SELF` marks a pair inside one renderer), and ends `PAIRS=<n> COMPLETE`.
`ZFightScan.Cancel()` stops a scan and returns a partial report ending `PAIRS=<n> PARTIAL (...)`.

For scripts and tests: `ZFightScan.RunBlocking(rootPath, planeEps, minOverlapArea, includeSelf,
includeOppositeFacing, maxSeconds = 60)` runs the same job in slices on the calling thread and
returns the report; `ZFightScan.LastPairs` gives the pairs as objects.

Algorithm: a hierarchical uniform grid (each triangle is stored at the level whose cell covers its
padded bounding box, so it touches at most 8 cells; a triangle queries its own and coarser levels,
and each pair is handled only in the cell holding the min corner of the two boxes' intersection),
then a plane test on all six vertices and Sutherland-Hodgman clipping for the exact overlap area.
Measured on 2022.3.22f1: two coplanar 50 x 50 m grids of 100,352 triangles each scan in a few
seconds of editor time, sliced, with no slice near 2 s (see CHANGELOG for numbers).

## ZFightRender: image-based z-fighting

For each shot, draws every visible opaque MeshRenderer off-screen in a flat per-renderer ID colour
(frustum- and LOD-culled like the real camera, using each renderer's own cull mode) in two passes:

1. the visible surface per pixel: renderer ID and linear eye depth, normal depth test;
2. every fragment of a *different* renderer whose eye depth is within the tie tolerance of the
   visible surface at that pixel is flagged with its ID.

A flagged pixel is a z-fight between those two renderers, seen from that viewpoint. With `d` the
eye depth and `C` the largest per-axis |coordinate| of the shot's camera, the tolerance is
`tol = max(MinTolerance, DepthSteps * e)`:

- `DepthFormat = ZDepthFormat.Float32ReversedZ` (default, VRChat PC): `e = 2^-24 * C + 2^-23 * d`.
  On 2022.3 D3D11 a 24-bit depth request gets D32_SFloat with reversed Z, so precision comes from
  float32 world positions plus float depth and does not depend on the near clip. This bounds every
  separation measured on that setup (4.3 µm at 100 m from the origin; 67 µm at 100 m with the camera
  at x = z = 1000).
- `DepthFormat = ZDepthFormat.Fixed24` (conservative; Android/Quest and other non-reversed
  platforms): `e = 2^-24 * C + d² / (NearClip * 2^24)`.

Defaults: `NearClip = 0.01` (only `Fixed24` uses it; VRChat clamps the runtime near clip to
0.001–0.05 m), `DepthSteps = 2`, `MinTolerance = 0.05 mm`. All four are public static fields;
`Tolerance(d, cameraCoord = 0)` returns the value.

| Camera | 1 m | 4 m | 20 m | 100 m |
|---|---|---|---|---|
| PC, at origin | 0.05 mm | 0.05 mm | 0.05 mm | 0.05 mm |
| PC, C = 500 m | 0.060 mm | 0.061 mm | 0.064 mm | 0.083 mm |
| Fixed24, near 0.01, at origin | 0.05 mm | 0.19 mm | 4.8 mm | 119 mm |

On PC only exactly or effectively coplanar pairs are flagged; a 3 mm decal gap seen from 20 m is
clean. Switch to `Fixed24` when the world also ships to a 24-bit platform.

Why not compare renders at nudged near/far clip planes: measured on 2022.3 / D3D11, near/far
variants of an exactly coplanar pair changed about 0.2 % of the overlap pixels in a still frame (the
tie is decided by a systematic rounding bias, not noise), and reversing the draw order changed even
fewer. The tolerance pass flags the whole overlap.

Not covered: SkinnedMeshRenderers, terrain, particles, transparent queues (> 2500). Alpha-cutout
materials are drawn solid. Overlaps inside one renderer share an ID and need `ZFightScan` with
`includeSelf`. Surfaces that cross each other tie only along the intersection line (a few pixels).

```csharp
return AWDK.AgentTools.ZFightRender.Start("Temp/zfight",
    "[{\"name\":\"lobby\",\"pos\":[0,1.6,-6],\"look\":[0,1.2,0],\"w\":1280,\"h\":720}]");
return AWDK.AgentTools.ZFightRender.Status();
```

Per shot it writes `<name>_zmask.png` (the normal camera render darkened, z-fight pixels magenta)
and reports the pixel count, percentage, bounding box (y from the top), `tol@20m` (the tolerance at
20 m from that camera position) and the renderer pairs by pixel count; the first line states the
tolerance model. The report ends `SHOTS=<n> ZFIGHT_PIXELS=<total> COMPLETE`.
`RunBlocking(outDir, shotsJson, maxSeconds = 120)` and `LastResults` exist for scripts and tests;
`CompareIds`, `IdColor`/`IdOf` and `MaskImage` are the pure mask math. The pass shader is
`Hidden/AWDK/ZTieId` (`Editor/Shaders/ZTieId.shader`).

Use both detectors: the scan finds every coplanar overlap including hidden ones, the render shows
which ones are visible and how bad they look.

## WorldCapture: review screenshots

```csharp
return AWDK.AgentTools.WorldCapture.Shoot("Temp/review",
    "[{\"name\":\"01_wide\",\"pos\":[0,1.6,-6],\"look\":[0,1.2,0],\"fov\":60,\"w\":1600,\"h\":900}," +
    " {\"name\":\"02_corner\",\"pos\":[4,1.6,4],\"look\":[0,1,0]}]");
return AWDK.AgentTools.WorldCapture.Status();
```

Writes `<outDir>/<name>.png` per shot (8x MSAA, the scene's own lighting, lightmaps and skybox;
no lights are added) and ends `SHOTS=<n> COMPLETE`. One shot per editor tick.
`ShootBlocking(outDir, shotsJson, maxSeconds = 120)` is the synchronous variant.

**`__CapCam__`**: both render tools use one persistent camera named `__CapCam__`, created on first
use with `HideFlags.DontSave` (never saved into the scene) and its Camera component disabled. The
tools never destroy it: destroying a camera right after `Camera.Render()` has crashed the editor.
If you want it gone, delete it by hand later, not in the same call as a render.

## PerfSample: play-mode performance

Play mode only. Waits `settleSeconds`, optionally disables every renderer under the listed roots,
skips `warmupFrames`, then records `frames` frames.

```csharp
return AWDK.AgentTools.PerfSample.Start("Temp/perf/baseline.json");
return AWDK.AgentTools.PerfSample.Start("Temp/perf/no_plants.json", 15, 40, 200, "Dressing/Plants,Exterior/Trees");
return AWDK.AgentTools.PerfSample.Status();
```

Signature: `Start(string outJson, float settleSeconds = 15, int warmupFrames = 40, int frames = 200,
string disableRootsCsv = null)`.

Recorded per frame: CPU frame time (unscaled delta), `Main Thread`, `Camera.Render` and
`BehaviourUpdate` profiler markers (via `ProfilerRecorder`), GPU frame time (`FrameTimingManager`;
`null` when the editor provides none, enable *Frame Timing Stats* in Player settings), and
`drawCalls`, `batches`, `setPassCalls`, `triangles`, `vertices` from `UnityEditor.UnityStats`
(reflection). The JSON holds mean/median/p95/min/max per metric; the text summary ends `COMPLETE`.

Attribution: run once without and once with `disableRootsCsv`; the difference is what those
renderers cost. Disabling is a play-mode change, restored at the end of the sample and discarded
on exit anyway. Editor numbers include editor overhead and every rendering camera (Game view, and
the Scene view if visible): compare runs with each other, not with a VRChat client.

## WorldAudit: rule check

Synchronous and quick; no Status call.

```csharp
return AWDK.AgentTools.WorldAudit.Run();
return AWDK.AgentTools.WorldAudit.Run("Building");
```

Sections, each with a count and the object paths (inactive / EditorOnly objects are marked):

| Section | Flags |
|---|---|
| `STATIONS` | `VRCStation` / `VRC_Station` components |
| `PICKUPS` | `VRCPickup` / `VRC_Pickup` with `proximity` != 0.1 or `AutoHold` != `No` |
| `REALTIME_OR_MIXED_LIGHTS` | enabled lights whose mode is not Baked |
| `LEFTOVER_OBJECTS` | `__name__` objects (DontSave ones are mentioned, not counted) |
| `WALKABLE_MESHCOLLIDERS` | MeshColliders with a floor-like name or at least 1 m² of upward-facing area. Exception: a MeshCollider on a GameObject named `ContainShell` outside prop roots (containment guard slabs, whose thin tops are never walked) is counted on an informational `[CONTAINMENT_SHELLS]` line |
| `PROP_COLLIDERS` | non-trigger colliders under a `Props` / `Dressing` / `Furniture` / `Decor` / `Clutter` ancestor (pickups exempt). Exceptions: a `BoxCollider` on a GameObject named `LieDownCollider` that is inactive or disabled (off by default, switched on by the world lie-down toggle) is counted on an informational `[LIE_DOWN_COLLIDERS]` line; an active, enabled, non-trigger `BoxCollider` on a GameObject named `SolidCollider` (big furniture) is counted on `[SOLID_FURNITURE_COLLIDERS]`. An enabled or non-Box `LieDownCollider`, or an off, trigger or non-Box `SolidCollider`, is a finding |
| `STATIC_MISSING_UV2` | ContributeGI + lightmapped renderers whose mesh has no UV2 |
| `UNCOMPRESSED_TEXTURES` | Texture2Ds above 64 px on scene materials stored in an uncompressed format |

The report ends `ISSUES=<n>`. These are heuristics: read the paths before acting on them.

## Tests

EditMode tests live in `Tests/Editor` (with SDK-named stand-ins in `Tests/Fakes`). To run them,
add the package to `"testables"` in the project manifest, add `com.unity.test-framework`, then:

```
Unity.exe -batchmode -projectPath <project> -runTests -testPlatform EditMode -testResults results.xml
```

Do not pass `-nographics`: the render tests need a graphics device and are ignored without one.

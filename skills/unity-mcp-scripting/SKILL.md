---
name: unity-mcp-scripting
description: Driving the open Unity Editor from an agent through MCP for Unity (CoplayDev unity-mcp) — connecting and pinning the right editor instance, short time-budgeted `execute_code` calls, the Start/Status pattern for long jobs, dirty-marking and saving scenes, compile-error checks, persistent capture cameras, locale-safe floats, and the editor-scripting traps that silently corrupt a scene. Load before the first Unity MCP call of a session, before writing any C# for `execute_code`, or when an MCP call times out, a save does not stick, play mode will not start, or a scripted edit "succeeded" but the scene disagrees.
---

# Driving the Unity Editor through MCP

Scope: Unity 2022.3 (the VRChat-supported editor) driven by the CoplayDev **MCP for Unity** server.
Unity's official CLI/MCP goes through `com.unity.pipeline`, which needs Unity 6000.0+, so it cannot
connect to 2022.3. Install and editor preferences: `.omp/docs/bootstrap.md` §3. The
`com.awdk.agenttools` API (`ZFightScan`, `ZFightRender`, `WorldCapture`, `PerfSample`, `WorldAudit`):
`.omp/docs/unity-tools.md`. No native MCP support in your host: `.omp/scripts/unity_mcp.py`
(see `.omp/scripts/README.md`).

**Drive the live editor, never the files.** Hand-edited `.unity` YAML needs a manual reload, is
clobbered when the editor saves its in-memory state, and cannot add DLL-based components (e.g.
`VRCUiShape`). Reading old YAML out of git to *re-apply* values through the editor is fine: index the
committed scene by fileID, follow the GameObject's Transform, match by `m_Name`, then set the values
by script.

## 1. Connect and pin the instance

1. List editors via the `mcpforunity://instances` resource. With more than one open, pin with the
   Unity MCP `set_active_instance` tool using the exact `Name@hash`, **and** pass `unity_instance` on
   every call: the session default does not reliably stick, and a call routed to the wrong editor
   edits the wrong project silently.
2. First `execute_code` of every session (and after anyone may have switched project or scene):
   ```csharp
   return "dataPath=" + UnityEngine.Application.dataPath
        + " | scene=" + UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene().path;
   ```
   `Library/LastSceneManagerSetup.txt` exists in every project and goes stale; it is not evidence of
   what is open, and projects can share scene names.
3. **One agent mutates the editor at a time.** Worktrees do not isolate it. Re-query objects before
   editing or deleting them; unfamiliar objects may be another session's live work. Re-verify what a
   long operation (bake, import) covered before acting on its result: it snapshots the scene at start.
4. **Timeout ≠ disconnected.** Usually the editor is busy (a heavy reimport can block the main thread
   ~5 min); check the window title and wait. Reconnecting or restarting mid-import causes damage. In
   stdio mode the bridge auto-starts and revives after "End Session" on the next recompile; a bridge
   that seems down may have bound a fallback port (`StdioBridgeHost.StartAutoConnect()` rebinds).
5. Setup failures: a server started with `uvx --offline` fails when the package is not in the uv
   cache; new MCP servers show tools only in a fresh host session; the editor side must show
   "Session Active". Unity launched from a script needs `ALLUSERSPROFILE` and `PUBLIC` in its
   environment or UPM silently ignores new packages, and process start is not MCP readiness.

## 2. Shape of an `execute_code` call

The Unity MCP `execute_code` tool runs a C# method body on the main thread: the editor is frozen
while it runs, and MCP gives up after roughly 10 s (30 s windows have been observed; plan for the
short one). Without Roslyn installed it silently falls back to a C# 6 compiler (bootstrap §3).

- **Short and single-purpose.** Return one compact string report; avoid dumping hierarchies.
- **Every loop over scene geometry gets a time budget.** An unbounded O(n²) triangle loop hung an
  editor holding unsaved work. Budget, report what remains, call again:
  ```csharp
  var sw = System.Diagnostics.Stopwatch.StartNew();
  int done = 0;
  foreach (var mf in todo) {                 // todo: filtered to items without a "done" marker
      if (sw.ElapsedMilliseconds > 2000) break;
      Process(mf); mf.name += "__M";         // idempotent marker → resumable
      done++;
  }
  return "done=" + done + " remaining=" + (todo.Count - done);
  ```
- **A timeout on a mutation means "unknown", not "did not run".** A timed-out merge left both the
  combined mesh and its sources (3.74 M tris instead of 2.00 M). Query the resulting state before
  retrying; batch small (~6 heavy items); never re-run a non-idempotent step over a half-done state,
  regenerate instead.
- **Verify in a later call.** After `SaveAndReimport`/`ImportAsset`, a measurement or screenshot in
  the same call sees the old mesh; new assets may not load via `LoadAssetAtPath` until the next call;
  files written to disk need `AssetDatabase.ImportAsset(path, ForceUpdate | ForceSynchronousImport)`.
- **Measure across calls**, e.g. FPS from `Time.frameCount` / `Time.realtimeSinceStartup` deltas ~8 s
  apart; tris and draw calls from `UnityEditor.UnityStats` via reflection.
- `AssetDatabase.MoveAssetToTrash` can trip the server's safety blocklist; use the Unity MCP
  `manage_asset` tool's `delete` action.
- **Embedding C# in a Python/IPython cell:** never start a line with `ident = !expr`; IPython rewrites
  it as a shell capture even inside a string literal. Write `ident = (!expr);`. Passing C# through a
  shell: use `unity_mcp.py --args-file` to avoid quoting damage.

## 3. Long jobs: Start / Status

Anything that cannot finish well inside one call (scans over every triangle, multi-shot captures,
bakes, play-mode sampling) runs time-sliced on `EditorApplication.update`:

- `X.Start(...)` returns `STARTED ...` at once; poll `X.Status()` in later calls until it returns the
  final report. **A timed-out call is re-polled, never re-started**: a second `Start()` supersedes
  the running job (possibly someone else's). Only the documented completion line counts as done;
  `STATE=idle` means a script reload dropped the job. Contracts per tool: `.omp/docs/unity-tools.md`.
- Your own long work: `AWDK.AgentTools.JobRunner.Start(kind, job => Body(job))`, where `Body` is an
  iterator that sets `job.Progress`, `yield return null`s every few milliseconds and sets
  `job.Result` at the end; poll with `JobRunner.Status(kind)`. Jobs live in memory only.
- Third-party long operations follow the same shape: trigger in one call, poll a flag across separate
  calls, then re-verify scene state. Bakery: open the `ftRenderLightmap` window instance,
  `LoadRenderSettings` then `RenderButton`, poll `bakeInProgress` (details:
  `.omp/skills/bakery-light-baking/SKILL.md`).

## 4. Dirty-marking, saving and recovery

- **Scripted reparent/rename does not dirty the scene**, and `SaveScene`/`SaveOpenScenes` then skip
  it while returning `true`. Always `EditorSceneManager.MarkSceneDirty(scene)` then `SaveScene(scene)`,
  and verify on disk (file `LastWriteTime`, grep for a renamed `m_Name:`).
- **Free undo while not dirty:** if `scene.isDirty` is still `false` after scripted damage,
  `EditorSceneManager.OpenScene(path, OpenSceneMode.Single)` restores the file version without a
  prompt. Do risky mesh work before the first `MarkSceneDirty`.
- **Save before** editing an Editor script, a screenshot pass or any risky bulk edit. A recompile can
  land the editor on an empty untitled scene (`name == ""`, `rootCount == 0`) where every query
  returns a plausible lie (0 lights, 0 lightmaps); reopen the scene and assert `scene.name` and
  `rootCount` before measuring. `LightmapSettings.lightmaps` can read 0 briefly right after
  `OpenScene`; re-query.
- **Save-before-diagnose is the hazard after asset churn.** `DeleteAsset` + `CreateAsset` at the same
  path nulls every live reference (45 `MeshFilter`s in one case). If the `.meta` is unchanged and the
  scene unsaved, reopening the scene recovers them. Prevent it by mutating meshes in place
  (`LoadAssetAtPath`, `m.Clear()`, refill every channel, `SetDirty`, `SaveAssets`), and after any
  asset rebuild count `sharedMesh == null` in the scene.
- **Snapshot/restore passes record every field they write back**: `SetColor(new Color(r,g,b))` forces
  alpha 1, and defaults can rewrite `m_LightmapFlags`. For tracked files prefer
  `git checkout <commit> -- <files>`, and check `git diff` (alpha changes are invisible in renders).
- Exit play mode before relying on edits; play-mode edits revert.

## 5. Compile-error checks

After **every** script change (yours or written to disk by anyone): the Unity MCP `refresh_unity`
tool (the editor auto-refreshes only on focus), wait for compilation, then the Unity MCP
`read_console` tool, and resolve every `error CS` before anything else.

- Play mode **silently refuses** to start with compile errors: the request reports success, then the
  editor drops back to edit mode. Compile errors block every other agent on the editor too.
- Read the messages, not just the type filter: `read_console` has mislabeled ordinary logs as
  exceptions in some versions.
- `refresh_unity` reporting `recovered_from_disconnect` means the compile was interrupted; treat
  UdonSharp programs as stale (the VM can run the old program while exposing new variables) and
  force `UdonSharpCompilerV1.CompileSync(new UdonSharpCompileOptions())`. `CompileSync()` returns
  normally even with errors: clear the console, recompile, re-read. Prove U# behaviour changes in
  play mode; reading a value back proves serialization, not execution.

## 6. Capture cameras and screenshots

- **Never destroy a camera after `Render()` in the same call.** Edit-mode `Render()` sets
  `Camera.current`; the next GUI repaint dereferences the freed camera and the editor segfaults a few
  calls later. Reuse one persistent `__CapCam__` (`WorldCapture` does this). If a temp camera is
  unavoidable: `Camera.SetupCurrent(null)`, `RenderTexture.active = null`, `cam.targetTexture = null`
  before destroying it. Save the scene before a screenshot pass.
- **Sweep `__*__` objects and assert zero realtime/mixed lights** before every save, commit, bake or
  build; review tools may leave a realtime `__CapLight__`, and the SDK saves the open scene on build.
  Run both checks; either can miss on its own.
- The Unity MCP `manage_camera` screenshot with `view_position`/`view_rotation` renders through a
  temporary ~60° perspective camera, ignoring the named camera's projection and FOV; frame plans by
  distance (visible half-height ≈ height above subject × 0.577, view_rotation `[90,0,0]`) and pass
  `include_image: true`, `max_resolution: 1600` (default 640 px is unreadable).
- Distant objects missing in the Scene view: raise `SceneView.lastActiveSceneView.cameraSettings.farClip`
  (it can sit at 100 m), not layers. Capture cameras have their own clip planes.
- Particle systems do not render in edit-mode captures; do not report them missing.

## 7. Locale-safe floats

The editor inherits the OS culture. Under a comma-decimal locale `ToString()` prints `1,15`, and
parsing it back yields 115 **even with `InvariantCulture`** (`,` is read as a group separator; 13
lights were set to 115 instead of 1.15), while the current culture reads `172.5` as 1725.

- Target values are float literals in code (`1.15f`, `new Vector3(0f, 2.4f, 174.5f)`), never copied
  from a previous tool result's text, where commas may be decimal separators.
- Never round-trip a number through its own string; key histograms on `Mathf.RoundToInt(v * 100)`.
- Format reports with `CultureInfo.InvariantCulture`. If you must parse:
  `float.Parse(s, NumberStyles.Float & ~NumberStyles.AllowThousands, CultureInfo.InvariantCulture)`.
- Gate every bulk write by asserting the resulting range.

## 8. Scene-query and edit traps

| Trap | Rule |
|---|---|
| `GameObject.Find` / `transform.Find` skip inactive objects, so disable-then-restore silently no-ops | Cache the reference at disable time; find inactive objects by walking `scene.GetRootGameObjects()`; print `found = N (must be >= 1)` |
| `DestroyImmediate` inside `foreach (Transform c in parent)` skips every other child | Collect first, destroy after; assert against a fresh scene query, not your loop counter |
| Cleanup queues keyed by bare names (`Placeholder`, `Text`, `Content`, `Label`) delete live UI children | Record full hierarchy paths; check incoming references before deleting |
| A generator that destroys and rebuilds its root erases hand placement under it | Hand dressing gets its own root |
| `Renderer.bounds` is world-axis-aligned: a 45°-yawed prop measures 1.41× too wide | Measure size from `sharedMesh.bounds.size × lossyScale`; use renderer bounds only as a pre-filter |
| Reparenting a child out of a prefab instance silently fails; FBX-embedded material edits don't persist; importer `AddRemap` doesn't update existing instances | `PrefabUtility.UnpackPrefabInstance` first; use material assets; fix importer and instance renderers |
| Setting an instance's `localScale` to the prefab's value records no override, so regenerating the prefab resets it | Put size corrections in the importer/prefab source |
| Scripted UdonSharp add: `UdonSharpEditorUtility.AddUdonSharpComponent` doesn't exist, `ArgumentNullException: key`, wrong `SyncMethod` | Create and compile the program asset, add in a later call via `UdonSharpEditor.UdonSharpComponentExtensions.AddUdonSharpComponent(go, type)`, set `ub.SyncMethod` from the asset's sync mode; with several U# behaviours match `programSource.name` |
| Play-mode per-renderer triangle counts read the static-batched combined mesh (~30× inflated) | Count tris in edit mode |

When an API name is uncertain, reflect over the loaded assemblies (or use the Unity MCP
`unity_reflect` tool) instead of guessing, and remove half-built components before retrying.

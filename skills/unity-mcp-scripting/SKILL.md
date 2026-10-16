---
name: unity-mcp-scripting
description: Driving the open Unity Editor from an agent through MCP for Unity (CoplayDev unity-mcp) — connecting and pinning the right editor instance, short time-budgeted `execute_code` calls, the Start/Status pattern for long jobs, dirty-marking and saving scenes, compile-error checks, persistent capture cameras, locale-safe floats, and the editor-scripting traps that silently corrupt a scene. Load before the first Unity MCP call of a session, before writing any C# for `execute_code`, or when an MCP call times out, a save does not stick, play mode will not start, or a scripted edit "succeeded" but the scene disagrees.
---

# Driving the Unity Editor through MCP

Scope: Unity 2022.3 (the VRChat-supported editor) driven by the CoplayDev **MCP for Unity** server.
Unity's official CLI/MCP needs Unity 6 and cannot connect to 2022.3
([note](../../knowledge/notes/official-unity-cli-requires-unity-6.md)). Install and editor
preferences: [bootstrap.md §3](../../docs/bootstrap.md#3-wire-it). The `com.awdk.agenttools` API
(`ZFightScan`, `ZFightRender`, `WorldCapture`, `PerfSample`, `WorldAudit`): [unity-tools.md](../../docs/unity-tools.md).
No native MCP support in your host: `.omp/scripts/unity_mcp.py` ([scripts README](../../scripts/README.md)).

**Drive the live editor, never the files.** Hand-edited `.unity` YAML needs a reload, is clobbered
when the editor saves its in-memory state, and cannot add DLL-based components
([note](../../knowledge/notes/unity-mcp-setup-and-prefer-it-over-scene-yaml.md)). Reading old YAML
out of git to *re-apply* values through the editor is fine
([note](../../knowledge/notes/revert-one-geometry-pass-from-old-scene-yaml.md)).

## 1. Connect and pin the instance

1. List editors via the `mcpforunity://instances` resource. With more than one open, pin with the
   Unity MCP `set_active_instance` tool using the exact `Name@hash`, **and** pass `unity_instance` on
   every call: the session default does not reliably stick, and a call routed to the wrong editor
   edits the wrong project silently ([note](../../knowledge/notes/unity-mcp-routing-busy-and-autostart.md)).
2. First `execute_code` of every session (and after anyone may have switched project or scene):
   ```csharp
   return "dataPath=" + UnityEngine.Application.dataPath
        + " | scene=" + UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene().path;
   ```
   `Library/LastSceneManagerSetup.txt` is not evidence of what is open
   ([note](../../knowledge/notes/verify-which-project-unity-has-open.md)).
3. **One agent mutates the editor at a time.** Worktrees do not isolate it. Re-query objects before
   editing or deleting them; unfamiliar objects may be another session's live work
   ([note](../../knowledge/notes/parallel-agent-sessions-in-one-unity-editor.md)).
4. **Timeout ≠ disconnected.** Usually the editor is busy (import, compile, bake); check the window
   title and wait. Reconnecting or restarting mid-import causes damage. The stdio bridge
   auto-starts and revives after "End Session"
   ([note](../../knowledge/notes/unity-mcp-routing-busy-and-autostart.md)).
5. Setup failures: `uvx --offline` cannot start without a warm cache; new MCP servers show tools only
   in a fresh host session ([note](../../knowledge/notes/unity-mcp-setup-and-prefer-it-over-scene-yaml.md)).
   Unity launched from a script with a stripped environment ignores new packages, and process
   start is not MCP readiness ([note](../../knowledge/notes/unity-launched-from-script-ignores-new-packages.md)).

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
- **A timeout on a mutation means "unknown", not "did not run".** Query the resulting state before
  retrying; batch small (~6 heavy items); never re-run a non-idempotent step over a half-done state
  ([note](../../knowledge/notes/mcp-timeout-leaves-mutation-half-applied.md)).
- **Verify in a later call.** After `SaveAndReimport`/`ImportAsset`, a measurement or screenshot in
  the same call sees the old mesh; new assets may not load until the next call; the U# class→asset
  map is not queryable in the call that created the program asset
  ([note](../../knowledge/notes/verify-reimports-in-a-later-call-and-edit-instances-safely.md),
  [note](../../knowledge/notes/udonsharp-add-component-from-editor-script.md)).
- **Measure across calls**, e.g. FPS from `Time.frameCount` deltas ~8 s apart, tris/draw calls from
  `UnityEditor.UnityStats` via reflection ([note](../../knowledge/notes/measure-editor-fps-and-tris-via-unitystats.md)).
- `AssetDatabase.MoveAssetToTrash` can trip the server's safety blocklist; use the Unity MCP
  `manage_asset` tool's `delete` action (same note).
- **Embedding C# in a Python/IPython cell:** never start a line with `ident = !expr`; IPython rewrites
  it as a shell capture even inside a string. Write `ident = (!expr);`
  ([note](../../knowledge/notes/ipython-rewrites-bang-assignments-in-embedded-code.md)).
  Passing C# through a shell: use `unity_mcp.py --args-file` to avoid quoting damage.

## 3. Long jobs: Start / Status

Anything that cannot finish well inside one call (scans over every triangle, multi-shot captures,
bakes, play-mode sampling) runs time-sliced on `EditorApplication.update`:

- `X.Start(...)` returns `STARTED ...` at once; poll `X.Status()` in later calls until it returns the
  final report. **A timed-out call is re-polled, never re-started**: a second `Start()` supersedes
  the running job (possibly someone else's). Only the documented completion line counts as done;
  `STATE=idle` means a script reload dropped the job. Contracts per tool: [unity-tools.md](../../docs/unity-tools.md).
- Your own long work: `AWDK.AgentTools.JobRunner.Start(kind, job => Body(job))`, where `Body` is an
  iterator that sets `job.Progress`, `yield return null`s every few milliseconds and sets
  `job.Result` at the end; poll with `JobRunner.Status(kind)`. Jobs live in memory only.
- Third-party long operations follow the same shape: trigger in one call, poll a flag across separate
  calls, then re-verify scene state (Bakery: [note](../../knowledge/notes/bakery-scripted-bake-recipe.md)).

## 4. Dirty-marking, saving and recovery

- **Scripted reparent/rename does not dirty the scene**, and `SaveScene`/`SaveOpenScenes` then skip
  it while returning `true`. Always `EditorSceneManager.MarkSceneDirty(scene)` then `SaveScene(scene)`,
  and verify on disk (file `LastWriteTime`, grep for a renamed `m_Name:`)
  ([note](../../knowledge/notes/unity-scripted-edits-do-not-dirty-the-scene.md)).
- **Free undo while not dirty:** if `scene.isDirty` is still `false` after scripted damage,
  `EditorSceneManager.OpenScene(path, OpenSceneMode.Single)` restores the file version without a
  prompt. Do risky mesh work before the first `MarkSceneDirty` (same note).
- **Save before** editing an Editor script, a screenshot pass or any risky bulk edit. A recompile can
  land the editor on an empty untitled scene where every query returns a plausible lie (0 lights,
  0 lightmaps); reopen the scene and assert `scene.name` and `rootCount` before measuring
  ([note](../../knowledge/notes/editor-script-recompile-can-drop-open-scene.md)).
- **Save-before-diagnose is the hazard after asset churn.** `DeleteAsset` + `CreateAsset` at the same
  path nulls every live reference (45 `MeshFilter`s in one case); reload the unsaved scene to
  recover, and mutate meshes in place (`m.Clear()` then refill) to prevent it
  ([note](../../knowledge/notes/deleteasset-recreate-nulls-scene-references.md)).
- **Snapshot/restore passes record every field they write back** (`new Color(r,g,b)` forces alpha 1);
  for tracked files prefer `git checkout <commit> -- <files>`
  ([note](../../knowledge/notes/material-snapshot-must-record-every-field.md)).
- Exit play mode before relying on edits; play-mode edits revert
  ([note](../../knowledge/notes/unity-mcp-setup-and-prefer-it-over-scene-yaml.md)).

## 5. Compile-error checks

After **every** script change (yours or written to disk by anyone): the Unity MCP `refresh_unity`
tool (the editor auto-refreshes only on focus), wait for compilation, then the Unity MCP
`read_console` tool, and resolve every `error CS` before anything else.

- Play mode **silently refuses** to start with compile errors: the request reports success, then the
  editor drops back to edit mode ([note](../../knowledge/notes/play-mode-silently-refuses-on-compile-errors.md)).
  Compile errors block every other agent on the editor too.
- Read the messages, not just the type filter: `read_console` has mislabeled ordinary logs as
  exceptions in some versions ([note](../../knowledge/notes/unity-mcp-setup-and-prefer-it-over-scene-yaml.md)).
- `refresh_unity` reporting `recovered_from_disconnect` means the compile was interrupted; treat
  UdonSharp programs as stale and force `CompileSync`
  ([note](../../knowledge/notes/udonsharp-stale-program-after-edit.md)). `CompileSync()` returns
  normally even with errors: clear the console, recompile, re-read
  ([note](../../knowledge/notes/udonsharp-add-component-from-editor-script.md)).

## 6. Capture cameras and screenshots

- **Never destroy a camera after `Render()` in the same call.** Edit-mode `Render()` sets
  `Camera.current`; the next GUI repaint dereferences the freed camera and the editor segfaults a few
  calls later ([note](../../knowledge/notes/editor-screenshot-camera-destroy-crashes-unity.md)).
  Reuse one persistent `__CapCam__`; `WorldCapture` does this for you.
- **Sweep `__*__` objects and assert zero realtime/mixed lights** before every save, commit, bake or
  build; review tools may leave a realtime `__CapLight__`, and the SDK saves the open scene on build
  ([note](../../knowledge/notes/sweep-leftover-capture-rigs-before-commit-or-bake.md)).
- The Unity MCP `manage_camera` screenshot with `view_position`/`view_rotation` renders through a
  temporary ~60° perspective camera, ignoring the named camera's lens; frame plans by distance
  (half-height ≈ height × 0.577) and pass `include_image: true`, `max_resolution: 1600`
  ([note](../../knowledge/notes/mcp-positioned-screenshot-ignores-camera-lens.md)).
- Distant objects missing in the Scene view: raise `SceneView.lastActiveSceneView.cameraSettings.farClip`,
  not layers ([note](../../knowledge/notes/scene-view-far-clip-hides-distant-objects.md)).
  Capture cameras have their own clip planes.
- Particle systems do not render in edit-mode captures; do not report them missing
  ([note](../../knowledge/notes/verify-reimports-in-a-later-call-and-edit-instances-safely.md)).

## 7. Locale-safe floats

The editor inherits the OS culture. Under a comma-decimal locale `ToString()` prints `1,15`, and
parsing it back yields 115 **even with `InvariantCulture`** (13 lights set to 115 instead of 1.15)
([note](../../knowledge/notes/editor-locale-breaks-float-string-round-trips.md)).

- Target values are float literals in code (`1.15f`, `new Vector3(0f, 2.4f, 174.5f)`), never copied
  from a previous tool result's text, where commas may be decimal separators.
- Never round-trip a number through its own string; key histograms on `Mathf.RoundToInt(v * 100)`.
- Format reports with `CultureInfo.InvariantCulture`. If you must parse:
  `float.Parse(s, NumberStyles.Float & ~NumberStyles.AllowThousands, CultureInfo.InvariantCulture)`.
- Gate every bulk write by asserting the resulting range.

## 8. Scene-query and edit traps

| Trap | Rule | Note |
|---|---|---|
| `GameObject.Find` / `transform.Find` skip inactive objects | Cache the reference at disable time; find inactive objects by walking scene roots; print `found = N (must be >= 1)` | [gameobject-find-skips-inactive-objects](../../knowledge/notes/gameobject-find-skips-inactive-objects.md) |
| `DestroyImmediate` inside `foreach (Transform c in parent)` skips every other child | Collect first, destroy after; assert against a fresh scene query, not your loop counter | [destroyimmediate-while-iterating-transform-skips-children](../../knowledge/notes/destroyimmediate-while-iterating-transform-skips-children.md) |
| Cleanup queues keyed by bare names (`Placeholder`, `Text`, `Content`) delete live UI | Record full hierarchy paths; check incoming references before deleting | [cleanup-by-name-deletes-live-ui](../../knowledge/notes/cleanup-by-name-deletes-live-ui.md) |
| A generator that rebuilds its root erases hand placement under it | Hand dressing gets its own root | [keep-hand-dressing-outside-generated-roots](../../knowledge/notes/keep-hand-dressing-outside-generated-roots.md) |
| `Renderer.bounds` is world-axis-aligned: a 45°-yawed prop measures 1.41× too wide | Measure size from `sharedMesh.bounds × lossyScale`; use renderer bounds only as a pre-filter | [renderer-bounds-inflate-with-rotation](../../knowledge/notes/renderer-bounds-inflate-with-rotation.md) |
| Reparenting a child out of a prefab instance silently fails; FBX-embedded material edits don't persist; importer remaps don't update existing instances | Unpack first; use material assets; fix importer and instance renderers | [verify-reimports-in-a-later-call-and-edit-instances-safely](../../knowledge/notes/verify-reimports-in-a-later-call-and-edit-instances-safely.md) |
| Setting an instance's `localScale` to the prefab's value records no override | Put size corrections in the importer/prefab source | [editor-script-recompile-can-drop-open-scene](../../knowledge/notes/editor-script-recompile-can-drop-open-scene.md) |
| Scripted UdonSharp add: wrong API names, `ArgumentNullException: key`, wrong `SyncMethod` | Program asset first and compiled, add in a later call via `UdonSharpComponentExtensions.AddUdonSharpComponent`, set `SyncMethod` explicitly | [udonsharp-add-component-from-editor-script](../../knowledge/notes/udonsharp-add-component-from-editor-script.md) |
| Play-mode triangle counts per renderer read the static-batched combined mesh (~30× inflated) | Count tris in edit mode | [measure-editor-fps-and-tris-via-unitystats](../../knowledge/notes/measure-editor-fps-and-tris-via-unitystats.md) |

When an API name is uncertain, reflect over the loaded assemblies (or use the Unity MCP
`unity_reflect` tool) instead of guessing, and remove half-built components before retrying.

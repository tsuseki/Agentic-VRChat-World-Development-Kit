---
title: Driving Bakery bakes from editor scripts / MCP
topic: lighting-baking
tags: [bakery, scripting, execute_code, selective bake, cancel, ftRenderLightmap]
summary: Launch via the ftRenderLightmap window instance (LoadRenderSettings then RenderButton) queued in exactly one delayCall from a short call, poll bakeInProgress and the temp scene across separate calls, and re-verify scene state after every bake.
---
**When:** Starting, waiting for, or cancelling Bakery bakes from code (e.g. via the Unity MCP `execute_code` tool).
**How:**
- Static `ftRenderLightmap.RenderLightmap()` silently does nothing. Working recipe: `EditorWindow.GetWindow(<ftRenderLightmap type>)` → invoke `LoadRenderSettings()` → invoke `RenderButton(false)`.
- Launch from MCP: check `bakeInProgress == false`, then queue the `RenderButton(false)` call in **exactly one** `EditorApplication.delayCall` from a short `execute_code` call and return. A direct `RenderButton` call blocks through the export (or on a modal) and times the MCP call out, leaving "started or not" unknown. Every bake of a large world-building session was launched this way.
- Started tell: the active scene becomes `Assets/Bakery/_tempScene.unity` (and `bakeInProgress` turns true). The first polls can read `bakeInProgress == False` for up to ~100 s after queueing: a bake that looked dead started later, so never queue a second launch on that evidence.
- Settings live as serialized `renderSettings*` fields on `ftLightmapsStorage` on the `!ftraceLightmaps` object (e.g. `renderSettingsBounces`, not `renderSettingsGIBounces`). The open window keeps its own instance copy (e.g. `giSamples`) and its OnGUI writes it back over storage — set BOTH, and re-force the instance field after `LoadRenderSettings()`.
- Selective bake: set `Selection.objects` to the roots, set instance field `selectedOnly = true`, then `RenderButton(false)`; other lightmap groups stay untouched.
- `BakeryLightmapGroupSelector` fields: `active`, `lmgroupAsset` (not `lmgroup`), `instanceResolutionOverride`, `instanceResolution`.
- Reflection probes through Bakery: instance method `RenderReflectionProbesButton(false)`.
- Progress: static `bakeInProgress`, `progressBarPercent`, `progressBarText`. Cancel: set static `userCanceled = true` (winds down in ~30–60 s; `RenderButton` resets it at start, so set it after launch; trust `bakeInProgress`, not the flag).
- Waiting: poll state with separate tool calls (or an editor callback that writes a sentinel file, watched by a background shell loop). Never `Thread.Sleep` inside `execute_code` — it blocks the main thread and the bridge times out.
**Pitfalls:**
- `RenderButton` returns silently if `Application.isPlaying` — check play mode first when a launch does nothing.
- `delayCall` fires only when the editor ticks; an unfocused or busy editor can delay it for minutes. If nothing has started after a few minutes, look at the editor window (modal? focus?) before re-queuing; clear a stale queue with `EditorApplication.delayCall = null`. Never queue twice: `RenderButton` has no re-entry guard.
- If the queued `delayCall` fired but nothing started (`bakeInProgress` still false after ~3 min, no `_tempScene`, no new `%TEMP%\frender` files, no modal), launch once directly instead. Take the existing window from `Resources.FindObjectsOfTypeAll(<ftRenderLightmap type>)[0]`, then invoke `LoadRenderSettings()` and `RenderButton(false)` in one `execute_code` call. `bakeInProgress` reads true on return. The following MCP calls time out during the export, so watch `tasklist` for `ftraceRTX9`/`ftrace` and the `frender` mtimes, and retry MCP after the tracer exits (rp-world 2026-11-05: the delayCall launch did nothing; the direct call baked in 37 min). Before this fallback, confirm `TestSystemSpecs()` is true and `TestNeedsBenchmark()` is false.
- `receiveGI` set with plain property writes on prefab instances is lost when Bakery reloads the scene, so the renderers bake back into the atlas. Write it through `SerializedObject` (`m_ReceiveGI`) and check it after a reload from disk.
- Bakery reloads the scene after a bake; objects toggled active just before launch can come back inactive. Re-check, `MarkSceneDirty`, save after every bake.
- Verify completion by `*_final.hdr` mtimes, not `probes.asset` (it can update on a failed bake). Reflection-probe `.exr` mtimes must be newer than the lightmap HDRs, or re-render probes.
- Check quality fields before a final bake: stored draft values (GI samples 4, bounces 2) give blotchy GI; GI samples 32, bounces 4, AO intensity 0.7 / radius 0.5 / samples 32 fixed it.
- The MCP bridge often drops right after heavy bakes; Unity is usually alive — wait and retry.

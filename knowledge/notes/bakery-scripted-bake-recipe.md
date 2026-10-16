---
title: Driving Bakery bakes from editor scripts / MCP
topic: lighting-baking
tags: [bakery, scripting, execute_code, selective bake, cancel, ftRenderLightmap]
summary: Launch via the ftRenderLightmap window instance (LoadRenderSettings then RenderButton), poll bakeInProgress across separate calls, and re-verify scene state after every bake.
---
**When:** Starting, waiting for, or cancelling Bakery bakes from code (e.g. via the Unity MCP `execute_code` tool).
**How:**
- Static `ftRenderLightmap.RenderLightmap()` silently does nothing. Working recipe: `EditorWindow.GetWindow(<ftRenderLightmap type>)` → invoke `LoadRenderSettings()` → invoke `RenderButton(false)`.
- Settings live as serialized `renderSettings*` fields on `ftLightmapsStorage` on the `!ftraceLightmaps` object (e.g. `renderSettingsBounces`, not `renderSettingsGIBounces`). The open window keeps its own instance copy (e.g. `giSamples`) and its OnGUI writes it back over storage — set BOTH, and re-force the instance field after `LoadRenderSettings()`.
- Selective bake: set `Selection.objects` to the roots, set instance field `selectedOnly = true`, then `RenderButton(false)`; other lightmap groups stay untouched.
- `BakeryLightmapGroupSelector` fields: `active`, `lmgroupAsset` (not `lmgroup`), `instanceResolutionOverride`, `instanceResolution`.
- Reflection probes through Bakery: instance method `RenderReflectionProbesButton(false)`.
- Progress: static `bakeInProgress`, `progressBarPercent`, `progressBarText`. Cancel: set static `userCanceled = true` (winds down in ~30–60 s; `RenderButton` resets it at start, so set it after launch; trust `bakeInProgress`, not the flag).
- Waiting: poll state with separate tool calls (or an editor callback that writes a sentinel file, watched by a background shell loop). Never `Thread.Sleep` inside `execute_code` — it blocks the main thread and the bridge times out.
**Pitfalls:**
- `RenderButton` returns silently if `Application.isPlaying` — check play mode first when a launch does nothing.
- Editor callbacks (`delayCall`, `playModeStateChanged`, `update`) may not fire while the editor window is unfocused; prefer synchronous invocation + polling. Clear a stuck queue with `EditorApplication.delayCall = null`.
- Bakery reloads the scene after a bake; objects toggled active just before launch can come back inactive. Re-check, `MarkSceneDirty`, save after every bake.
- Verify completion by `*_final.hdr` mtimes, not `probes.asset` (it can update on a failed bake). Reflection-probe `.exr` mtimes must be newer than the lightmap HDRs, or re-render probes.
- Check quality fields before a final bake: stored draft values (GI samples 4, bounces 2) give blotchy GI; GI samples 32, bounces 4, AO intensity 0.7 / radius 0.5 / samples 32 fixed it.
- The MCP bridge often drops right after heavy bakes; Unity is usually alive — wait and retry.

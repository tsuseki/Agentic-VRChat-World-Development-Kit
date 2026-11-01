---
title: Launch editor jobs that block for minutes through one delayCall, then poll
topic: unity-editor-scripting-mcp
tags: [delayCall, BuildAssetBundles, Bakery, reimport, MCP timeout]
summary: A Bakery RenderButton, BuildAssetBundles or a big crunch reimport invoked directly holds the MCP call until it times out; queue exactly one EditorApplication.delayCall from a short call, return, and poll the job's own completion signal from later calls.
---
**Symptom:** a direct `RenderButton` call blocked on the editor (or a modal) and timed the MCP call out; whether the bake
had started was then unknown.

**Fix / rule:** in a short call, check the job is not already running (Bakery: `ftRenderLightmap.bakeInProgress ==
false`), then `EditorApplication.delayCall += () => ...;` exactly once and return. Poll its own signal from separate
calls: Bakery's `bakeInProgress` and the active scene becoming `Assets/Bakery/_tempScene.unity`, a result file for
`BuildPipeline.BuildAssetBundles` (~55 s), importer state for reimports. Used for every bake, bundle build and crunch
reimport in one world-building session.

**Pitfalls:**
- The first polls can read `bakeInProgress == False` for up to ~100 s after queueing: a bake that looked dead started
  later. Never queue a second launch while the first may still fire; Bakery's `RenderButton` has no re-entry guard and
  two exports collide in `%TEMP%\frender`.
- `delayCall` runs only when the editor ticks; an unfocused or busy editor can delay it for minutes. If nothing started
  after a few minutes, check the editor window before re-queuing; clear a stale queue with `EditorApplication.delayCall = null`.
- A timed-out direct call means "launched, unknown": poll, never re-launch.

**Verify:** the job's own completion signal (Bakery's finished line and new lightmap mtimes; the result file).

---
title: Play mode silently refuses to start when scripts have compile errors
topic: unity-editor-scripting-mcp
tags: [play mode, compile errors, error CS, MCP, UdonSharp, console]
summary: Entering play mode remotely reports success and then silently drops back to edit mode if any script fails to compile; read the console for 'error CS' first.
---
**Symptom:** Driving Unity via MCP, `EditorApplication.isPlaying = true` (or the play action) reports success and `isPlayingOrWillChangePlaymode` goes true, then the editor drops back to edit mode with no dialog. UdonSharp projects may also log "C# scripts have compile errors, cannot run scene upgrade".

**Cause:** Unity refuses play mode while any script has a compile error. Headless/remote you never see the red console badge.

**Fix / rule:** Whenever play mode won't engage, first read the console filtered for `error CS`. Fix the error, `AssetDatabase.Refresh()`, wait for compilation, retry.

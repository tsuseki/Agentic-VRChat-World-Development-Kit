---
title: PreviewRenderUtility renders from an agent call can kill the editor (LightmapSettings NULL)
topic: unity-editor-scripting-mcp
tags: [PreviewRenderUtility, preview scene, LightmapSettings, fatal error, execute_code, shader test]
summary: Rendering a shader test through PreviewRenderUtility from the Unity MCP execute_code tool froze the editor on a native fatal modal whose only button is Quit; render tests in the open scene with the persistent capture camera instead.
---

**Symptom:** an agent testing a new surface shader rendered a sphere off-scene through
`PreviewRenderUtility`. The first call worked. On the second, the editor froze on a native modal,
"Fatal Error! GetManagerFromContext: pointer to object of manager 'LightmapSettings' is NULL (table
index 22)", whose only button is **Quit**. Every later MCP call timed out. The open scene was dirty,
and everything since its last save was lost when the process was ended.

**Cause:** a preview scene has no `LightmapSettings` manager. Rendering lit, lightmap-aware shaders
in it can dereference the missing manager. It is not reliable even when the first call succeeds.

**Fix / rule:**
- Never use `PreviewRenderUtility` or other preview scenes from agent calls.
- Build test objects in the open scene far from the build (for example a `__Test__` root high above
  it), render them with the persistent `__CapCam__`, and delete them afterwards.
- Save the scene before any test render. Agents sharing an editor commit and save after every step,
  so a forced quit loses little.

**Verify:** the in-scene test render returns, and the editor stays responsive across repeated calls.

**Related:** `editor-screenshot-camera-destroy-crashes-unity.md` (never destroy a camera after `Render()`).

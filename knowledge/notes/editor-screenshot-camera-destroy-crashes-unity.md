---
title: Creating, rendering and destroying a temp camera in one editor call can crash Unity
topic: unity-editor-scripting-mcp
tags: [screenshot, Camera.Render, RenderTexture, DestroyImmediate, crash, execute_code, Camera.current]
summary: cam.Render() in edit mode sets Camera.current; destroying that camera in the same call leaves a dangling pointer that segfaults Unity on the next GUI repaint.
---
**Symptom:** Taking editor screenshots through the Unity MCP `execute_code` tool (temp `Camera` + `RenderTexture` + `cam.Render()` + `DestroyImmediate` of both in the same call) works and writes the PNG, then a few calls later the editor dies (SIGSEGV in `RenderTexture::SetActive` from `Camera:SetupCurrent`, fired from a UIElements repaint) and the MCP bridge reports no Unity instance. It is easy to misread as a domain reload.

**Cause:** In edit mode `cam.Render()` sets the static `Camera.current` to that camera. After `DestroyImmediate(cam)` the pointer dangles, and the next editor GUI repaint dereferences the freed camera. The delay makes it look unrelated to the screenshot call.

**Fix / rule:**
- Never destroy a camera after `Render()`: reuse one **persistent** capture camera (e.g. `__CapCam__`), found or created once, and sweep `__*__` objects before saving, baking or building.
- Inherited code that already destroys a temp camera: call `Camera.SetupCurrent(null)` and set `RenderTexture.active = null` and `cam.targetTexture = null` before the destroy, and move it to the persistent camera when you touch it. `EditorApplication.delayCall` is not a safe deferral: callbacks queued from MCP calls have been observed never to fire.
- `ScreenCapture.CaptureScreenshot(path)` against the Game view works when a camera is already rendering.
- Save the scene before any screenshot pass so a crash costs nothing.

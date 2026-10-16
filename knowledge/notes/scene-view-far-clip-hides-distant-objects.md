---
title: Objects missing in the Scene view far away: check SceneView far clip, not layers
topic: unity-editor-scripting-mcp
tags: [SceneView, farClip, camera, visibility, screenshots]
summary: With SceneView.cameraSettings.farClip at 100, a box 160 m away is invisible and framing from further only shows sky.
---
**Symptom:** a distant object can't be seen in the Scene view even though all layers are visible; framing it from further away shows only sky.

**Cause:** the Scene view camera's far clip (`SceneView.cameraSettings.farClip`) was 100 m. The Game camera's culling mask is unrelated.

**Fix:** raise `SceneView.lastActiveSceneView.cameraSettings.farClip` (3000 m verified) — not layers or Game camera settings. Scripted capture cameras have their own clip planes too.

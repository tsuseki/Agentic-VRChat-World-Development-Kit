---
title: Sweep leftover capture cameras and lights before every commit or bake
topic: agent-workflow-verification
tags: [capture-rig, realtime-light, screenshots, review, build, cleanup]
summary: Screenshot and review tooling can leave temporary cameras and an active realtime directional light in the scene; the light ships on build and poisons lighting comparisons, so sweep by name pattern and assert zero realtime lights.
---
**Symptom:** A world meant to have zero realtime lights has one; an unbaked scene looks plausibly lit and a real bake regression hides behind it. A pre-commit sweep found a leftover capture camera **and** capture light, both active, which had survived at least one commit.

**Cause:** Review/screenshot scripts create temporary rigs (a capture camera, a realtime directional "cap light") and don't always remove them. The camera is harmless; the light is not. The VRChat SDK saves the open scene on build, so it ships.

**Fix / rule:** As the last step before any commit or bake, sweep by name pattern (give all temporary rigs a convention such as `__Name__`), not by memory of what a tool promised:
```csharp
foreach (var t in Object.FindObjectsOfType<Transform>(true))
    if (t.name.StartsWith("__") && t.name.EndsWith("__")) Object.DestroyImmediate(t.gameObject);
int rt = 0;
foreach (var l in Object.FindObjectsOfType<Light>())
    if (l.lightmapBakeType != LightmapBakeType.Baked) rt++;   // must be 0 in a fully baked world
```
The name sweep and the realtime-light count are independent checks; either can miss on its own, so run both.

Related: [realtime-preview-lights-wash-out-baked-scenes](realtime-preview-lights-wash-out-baked-scenes.md)

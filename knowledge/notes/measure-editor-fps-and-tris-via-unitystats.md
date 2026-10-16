---
title: A/B performance in the editor by reading UnityStats and frame-count deltas
topic: unity-editor-scripting-mcp
tags: [UnityStats, FPS, draw calls, triangles, execute_code, profiling]
summary: Read UnityEditor.UnityStats via reflection for triangles/draw calls and compute FPS from Time.frameCount deltas across two separate execute_code calls.
---
**How:**
- Triangles / draw calls: read `UnityEditor.UnityStats` via reflection (`triangles`, `drawCalls`).
- FPS: record `Time.frameCount` and `Time.realtimeSinceStartup` in one `execute_code` call, read again in another call ~8 s later, divide.
- For a component's cost, toggle it (e.g. `terrain.treeDistance = 0`) and compare `Camera.Render` time in the Profiler.

**Pitfalls:**
- In play mode, static batching combines meshes: `meshFilter.sharedMesh.triangles.Length` per renderer returns the **combined** mesh, inflating counts ~30×. Count triangles in edit mode; in play mode only count enabled renderers.
- `AssetDatabase.MoveAssetToTrash` inside `execute_code` can trip the MCP safety blocklist; delete via the `manage_asset` tool's `delete` action instead.
- A quick visible-tri ceiling check: `GeometryUtility.CalculateFrustumPlanes` + `TestPlanesAABB` per renderer, sum triangles, skip ShadowsOnly. Frustum-only (no occlusion), so it over-estimates — safe for a budget check.

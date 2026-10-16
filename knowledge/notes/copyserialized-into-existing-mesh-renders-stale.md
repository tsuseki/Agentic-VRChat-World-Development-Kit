---
title: EditorUtility.CopySerialized into an existing Mesh asset keeps rendering the old geometry
topic: geometry-meshes-uvs
tags: [Mesh, CopySerialized, CreateAsset, stale render, generated mesh]
summary: Rewriting a mesh asset in place with CopySerialized updates its CPU data but the renderer keeps drawing the old mesh; write a new asset instead.
---
**Symptom:** You rebuild a generated mesh with `EditorUtility.CopySerialized(newMesh, existingAsset)`. `.vertexCount`, `.vertices` and `.bounds` read back as the new mesh, every numeric self-check passes, yet before/after renders are pixel-identical (0.00 % differing).

**Cause:** The in-place rewrite does not update what the renderer draws. Neither of these fixes it:
- `mesh.UploadMeshData(false)`
- `AssetDatabase.SaveAssets()` + `ImportAsset(path, ForceUpdate)` + reassigning `meshFilter.sharedMesh`

**Fix / rule:** Write a **new** asset with `AssetDatabase.CreateAsset` at a fresh path and assign that. The old unreferenced asset is harmless (unreferenced assets are not included in a VRChat world build).

**Verify:** Diff renders numerically, not by eye. Identical output (0.00 % differing) after a change means the pipeline is stale, not that the change was too subtle; do not respond by "making the effect stronger". Confirm the object is actually on screen by toggling `renderer.enabled` and diffing again (a large differing fraction proves visibility and points at the buffer).

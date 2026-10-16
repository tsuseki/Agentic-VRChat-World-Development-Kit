---
title: ProBuilder rebuilds its mesh on load and silently reverts a mesh you assigned
topic: geometry-meshes-uvs
tags: [probuilder, ProBuilderMesh, meshfilter, scene-reload, uv2, lightmapIndex]
summary: Assigning your own mesh asset to the MeshFilter of an object that still has a ProBuilderMesh component is temporary; ProBuilder rebuilds from its stored data on scene or domain reload.
---
**Symptom:** Twelve re-meshed parts were verified by a reviewer and committed; one scene reload later all were back to the old ProBuilder shape, and some had collapsed onto a shared mesh. The scene YAML could even hold your mesh GUID.

**Cause:** The `ProBuilderMesh` component, not the `MeshFilter`, is the source of truth. On scene load / domain reload it regenerates the mesh from its stored vertex data and overwrites the assigned asset. No warning.

**Fix / rule:**
- Strip the component. Destroying `ProBuilderMesh` also destroys the mesh it owns, so make your authored mesh an independent `.asset` first, `DestroyImmediate` the `ProBuilderMesh`, **then** assign the asset to the `MeshFilter` (see [probuildermesh-owns-its-mesh-destroying-it-or-a-clone-kills-it](probuildermesh-owns-its-mesh-destroying-it-or-a-clone-kills-it.md)).
- Detection sweep - any object whose `MeshFilter.sharedMesh` is your authored asset while a `ProBuilderMesh` is still attached is a time bomb:
```csharp
foreach (var c in t.GetComponents<Component>())
    if (c != null && c.GetType().Name == "ProBuilderMesh") { /* time bomb */ }
```
- Re-meshing destroys UV2: run `Unwrapping.GenerateSecondaryUVSet` and set `lightmapIndex = -1` until the next bake, or the renderer samples an old chart with new UVs and bakes blotchy.

**Verify:** Reload the scene from disk (`EditorSceneManager.OpenScene(path, OpenSceneMode.Single)`) and re-count. An in-memory check passes on a fix that won't survive the next reload.

---
title: ProBuilderMesh owns its Mesh: destroying the component or a clone silently kills the mesh
topic: geometry-meshes-uvs
tags: [ProBuilder, ProBuilderMesh, DestroyImmediate, Instantiate, sharedMesh null, mesh repair]
summary: DestroyImmediate on a ProBuilderMesh, or on an Instantiate'd clone of a ProBuilder object, destroys the shared Mesh and leaves live renderers invisible with no error.
---
**Symptom:** After scripted mesh work, renderers that were fine have `sharedMesh == null`: active, enabled, materials intact, zero bounds, invisible. No console error. Sometimes the damaged objects are not the ones you touched.

**Cause:** `ProBuilderMesh` **owns** its `Mesh`.
- `Object.DestroyImmediate(pbComponent)` destroys the mesh along with the component. Caching `sharedMesh` first and reassigning it later assigns a destroyed object; the exception (`MissingReferenceException: The object of type 'Mesh' has been destroyed`) only appears later when something reads it.
- `Object.Instantiate` on a ProBuilder object gives two components pointing at **one shared mesh**. Destroying either, even the whole clone GameObject, takes the mesh from under the original. This bites throwaway clones used as positive controls or layout trials.

**Fix / rule:**
- Before cloning, check for `ProBuilderMesh`. If present, clone the mesh too (`Instantiate(mf.sharedMesh)`), or use `GameObject.CreatePrimitive` when you only need a probe box.
- If you must strip the component to reassign a mesh: create an independent mesh asset first (`AssetDatabase.CreateAsset`), then destroy the component, then assign.
- Moving/scaling a ProBuilder object is safe; only mesh reassignment needs the strip.

**Repair:** ProBuilder keeps authoring data on the component, so regenerating sometimes works (reflection, since the assembly may not be referenced):
```csharp
var pbType = System.Type.GetType("UnityEngine.ProBuilder.ProBuilderMesh, Unity.ProBuilder");
var maskType = System.Type.GetType("UnityEngine.ProBuilder.RefreshMask, Unity.ProBuilder");
pbType.GetMethod("ToMesh", new[]{ typeof(MeshTopology) }).Invoke(pb, new object[]{ MeshTopology.Triangles });
pbType.GetMethod("Refresh", new[]{ maskType }).Invoke(pb, new object[]{ System.Enum.Parse(maskType, "All") });
Unwrapping.GenerateSecondaryUVSet(mf.sharedMesh);   // UV2 does NOT come back on its own
```
This worked in one case and did nothing in another. The fallback that worked: clone an identical sibling's mesh into a real `.asset`, assign it, then strip the desynced `ProBuilderMesh` so nothing regenerates over the repair. If the scene is not yet dirty, reloading it from disk is a free undo (see [unity-scripted-edits-do-not-dirty-the-scene](unity-scripted-edits-do-not-dirty-the-scene.md)).

**Verify:** After any scripted mesh work, sweep every `MeshRenderer` that is `activeInHierarchy && enabled` for `sharedMesh == null` or `bounds.size.magnitude < 1e-4`. Gate on active/enabled: inactive renderers legitimately report zero bounds and drown the sweep in false positives.

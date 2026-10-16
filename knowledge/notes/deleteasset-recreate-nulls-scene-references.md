---
title: DeleteAsset + CreateAsset at the same path nulls live scene references
topic: unity-editor-scripting-mcp
tags: [AssetDatabase, DeleteAsset, CreateAsset, Mesh, MeshFilter, null reference, reload scene]
summary: Replacing a mesh asset by deleting and recreating it nulls every MeshFilter pointing at it in the open scene; reload the unsaved scene to recover, and mutate meshes in place to prevent it.
---
**Symptom:** A helper re-built 8 mesh assets with `AssetDatabase.DeleteAsset(path)` then `AssetDatabase.CreateAsset(newMesh, path)`. The console reported success and correct bounds, but the next render showed 45 `MeshFilter.sharedMesh` gone `null`. Nothing errored; the rebuild's verification measured the new asset, never the scene.

**Cause:** `DeleteAsset` destroys the loaded `Mesh`, and every in-memory component pointing at it drops to null immediately.

**Fix / rule:** Check two facts before touching anything:
1. The `.meta` is unmodified (only the `.asset` changed). Unity restores the guid when an asset reappears at the same path in the same session, and a `.asset` Mesh always gets main-object fileID `4300000`, so the **on-disk** scene still resolves to the new mesh.
2. The scene was **not saved** after the delete.

Then repair with one call, discarding the in-memory nulls:

```csharp
var sc = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
UnityEditor.SceneManagement.EditorSceneManager.OpenScene(sc.path, OpenSceneMode.Single);
```

Scripted `OpenScene` discards silently (no prompt). `EditorSceneManager.ClearSceneDirtiness` is not public in 2022.3. Had the scene been saved first, the nulls would have been permanent: save-before-diagnose is the real hazard.

**Prevention:** mutate the mesh in place instead of replacing the asset:

```csharp
var m = AssetDatabase.LoadAssetAtPath<Mesh>(path);
if (m == null) { m = new Mesh(); AssetDatabase.CreateAsset(m, path); }
m.Clear();                       // keeps the same object, guid and fileID
m.vertices = verts; m.triangles = tris; m.uv = uvs;
m.RecalculateNormals(); m.RecalculateBounds();
EditorUtility.SetDirty(m); AssetDatabase.SaveAssets();
```

(On a reused mesh also write every channel you previously used, see [one-bad-uv2-poisons-bakery-atlas](one-bad-uv2-poisons-bakery-atlas.md).)

**Verify:** After any asset-rebuild sweep, count `sharedMesh == null` across the affected roots. The asset's own vert/tri report proves nothing about the scene.

Related: [probuildermesh-owns-its-mesh-destroying-it-or-a-clone-kills-it](probuildermesh-owns-its-mesh-destroying-it-or-a-clone-kills-it.md)

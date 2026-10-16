---
title: ModelImporter.AddRemap keys on the FBX-internal material name
topic: import-fbx-prefabs
tags: [fbx, ModelImporter, AddRemap, material remap, external object map]
summary: AddRemap matches the material name inside the FBX, not the shipped .mat filename; a wrong key is accepted silently and does nothing.
---
**Symptom:** A scripted material remap "succeeds" — survives `SaveAndReimport()`, appears in `GetExternalObjectMap()` — but renderers keep the old materials.
**Cause:** `ModelImporter.AddRemap(new SourceAssetIdentifier(typeof(Material), NAME), mat)` matches `NAME` against the material name inside the FBX (e.g. `bq_Leaf_Areca`), which often differs from the pack's `.mat` filename (e.g. `Areca Leaf.mat`).
**Fix / rule:**
- Read the real keys first: `foreach (var kv in imp.GetExternalObjectMap()) if (kv.Key.type == typeof(Material)) …` prints keys and current targets.
- `materialLocation` must be `ModelImporterMaterialLocation.InPrefab` or remaps are ignored.
- The identifier names differ between `materialLocation` modes for the same FBX: `External` exposes texture-derived names (e.g. `..._BaseColor`), `InPrefab` exposes node/material names (e.g. `M_Bed01_01`). With `External`, Unity ignores the remap entirely and binds its own generated `.mat` files, while the remap still reads back intact. Build the table from names read back in the mode you will ship (`r.sharedMaterials[i].name`). Recipe: `materialImportMode = ImportStandard`, `materialLocation = InPrefab`, then `AddRemap`.
- If you clear the table to remove dead keys, you also drop the pack's working entries — re-add every one you did not mean to change.
**Verify:** Load the prefab and print each renderer's `sharedMaterials`.

---
title: Overwrite an FBX at its existing path to swap every placed instance
topic: import-fbx-prefabs
tags: [FBX, replace model, instances, AddRemap, material overrides, sharedMaterials]
summary: To replace a model already placed many times, copy the new FBX over the old asset path; check submesh count, bounds and units first, and reassign materials on instances because per-renderer overrides beat the importer remap.
---
**When:** An asset already placed N times in a scene needs a rebuilt model. Copy the new FBX **over the existing asset path**, then `AssetDatabase.Refresh()`. Every instance keeps transform, name, parenting, collider proxies and lighting flags and simply renders the new mesh (e.g. a 2332-tri lounger swapped for an 8352-tri rebuild across nine instances in one file copy).

**Preconditions (check before the copy, or instances break silently):**
- **Same submesh count and slot order.** Renderers hold a fixed-length material array; a changed count leaves `NULL` entries.
- **Comparable bounds and the same `minY`.** Placements were authored against the old size (0.80 x 0.95 x 1.95 vs 0.807 x 0.942 x 1.963 needed no re-seating).
- **Same unit convention.** If the old FBX was centimetres with an import-scale fix and the new one is metres, the correction now doubles everything.

**Pitfalls:** Scene instances may carry **per-renderer material overrides** from whichever pass placed them. Those beat `ModelImporter.AddRemap`, so the new textures do not appear and the model looks identical to the old one, while `AddRemap` reports success and the asset preview looks right. Assign `renderer.sharedMaterials` explicitly on the instances.

**Verify:** Read materials back off a scene renderer, never off the imported asset.

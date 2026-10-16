---
title: Extract only the assets you need from a .unitypackage by GUID closure
topic: assets-sourcing
tags: [unitypackage, guid, selective import, asset pack]
summary: A .unitypackage is a tar.gz of GUID folders; BFS the guid references from seed prefabs and copy only that closure instead of importing the whole pack.
---
**When:** You want a handful of prefabs from a large pack without importing thousands of assets.
**How:**
- A `.unitypackage` is a gzipped tar whose top-level folders are asset GUIDs (each holds `asset`, `asset.meta`, `pathname`).
- Extract once to a scratch folder and index GUID → pathname.
- Starting from the seed prefabs, regex `guid: [0-9a-f]{32}` over each asset's text, breadth-first, collecting the closure (materials, meshes, textures, shaders).
- Copy each asset + `.meta` pair to its `pathname` in the project.
- Example scale: 11 seed prefabs → ~45 files from a ~5,800-entry pack.
**Pitfalls:** Binary assets (FBX, textures) have no outgoing refs — the closure stops there, which is correct. Keep the `.meta` files so GUIDs match.

---
title: Instantiating from the FBX gives its embedded stub materials, not your authored ones
topic: import-fbx-prefabs
tags: [fbx, materials, scatter, instantiate, untextured, material audit]
summary: Cloning donors from FBX assets yields the importer's untextured materials with plausible names; tally material|shader|mainTexture across placed renderers and rebind.
---
**Symptom:** Hundreds of scattered plants render as flat white blades; a material-name audit passes.
**Cause:** Donors built via `PrefabUtility.InstantiatePrefab` from the FBX get the importer's embedded stub materials (`Default-Material` or a stub with the same name as your authored material, no texture). Donors harvested from live, already-fixed scene instances looked right.
**Fix / rule:**
- Print `material.name | shader.name | mainTexture.name`, never the name alone — two materials with the same name can exist.
- After building donors from assets, rebind by species: match mesh name plus ancestor chain, most specific rule first (`shrub_sorrel_01` before `shrub_01`), and expand to per-submesh arrays for split materials.
- A white/untextured render is an asset-binding symptom, not lighting — check bindings before chasing shaders or palette in an unbaked scene.

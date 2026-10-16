---
title: After reimporting, verify in a later call; FBX-embedded material edits and prefab-instance reparenting silently fail
topic: unity-editor-scripting-mcp
tags: [SaveAndReimport, execute_code, prefab instance, unpack, embedded materials, AddRemap]
summary: A screenshot or measurement in the same call as SaveAndReimport sees the old mesh; embedded FBX materials don't keep edits; importer remaps don't update existing scene renderer arrays; reparenting a child of a prefab instance fails.
---
**Rules:**
- After `AssetDatabase.ImportAsset(ForceUpdate)` / `SaveAndReimport`, a screenshot or measurement **in the same `execute_code` call** still sees the old mesh (one-frame propagation lag). Never measure an instance created in the same call as the reimport — absurd sizes (e.g. "167 m") were stale-instance artifacts. Verify in a separate, later call.
- Files written to disk by an agent may not be auto-imported: call `AssetDatabase.ImportAsset(path, ForceUpdate | ForceSynchronousImport)`; newly created assets may not load via `LoadAssetAtPath` until the next call.
- Edits to FBX-embedded materials don't persist; replace them with material assets.
- An importer remap (`AddRemap`) does not change material arrays already overridden on scene instances — fix both the importer and the instance renderers.
- Reparenting a child out of a prefab instance silently fails; unpack the instance first (`PrefabUtility.UnpackPrefabInstance`).
- Particle systems (flames, sparks) don't render in edit-mode captures; don't report them missing from a screenshot.

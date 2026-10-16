---
title: A bloated .unitypackage export: stale Anchor Override references and layered PSDs
topic: assets-sourcing
tags: [unitypackage, ExportPackage, dependencies, m_ProbeAnchor, PSD, prefab override]
summary: A renderer Anchor Override left pointing into another prefab drags that prefab and everything it uses into the export; flattening the prefab and converting PSDs to PNG took 667 MB to 109 MB with no visual change.
---
**Symptom:** exporting one prefab produces a huge package (hundreds of MB); unticking items in the export dialog does nothing because they come back as dependencies.

**Cause 1 — stale probe anchor:** `m_ProbeAnchor` (the renderer's **Anchor Override**) in a `PrefabInstance` override block still points at a transform inside the prefab it was duplicated from. Unity's dependency walker follows it into that prefab and pulls in everything it uses (~691 MB of textures reachable only through unused materials). `PrefabUtility` inspection doesn't show it; only the YAML does.

**Cause 2 — layered PSDs:** 4096² RGB PSDs (123 MB, 64 MB) imported with `maxTextureSize = 2048`. Re-saving the flattened composite as PNG was bit-identical: 187.5 MB → 8.2 MB.

**Diagnose, in order:**
1. `AssetDatabase.GetDependencies(prefab, true)` + file size per dependency, grouped by extension.
2. Compare materials assigned to renderers vs `.mat` files in the closure (24 vs 55 here). A gap means references from something other than meshes.
3. For big textures, reverse-lookup referrers with `GetDependencies(candidate, false)`.
4. If no component holds it, grep the prefab YAML for the target's GUID (`AssetPathToGUID`) and read the `propertyPath`.

**Fix (non-destructive):** instantiate, `PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, ...)` (a flattened prefab cannot carry stale overrides), prune children with no renderers/needed components, strip editor-only tool components (loop 4–5 times; removals can expose more), copy only the PSD-using materials and repoint them to PNGs, `SaveAsPrefabAsset` to a new path, destroy the temp instance. Never edit shared originals.

**Pitfalls:** `AssetDatabase.ExportPackage` on ~200 MB exceeds a 30 s MCP timeout while Unity keeps writing — poll the output file size until it stops changing.

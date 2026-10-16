---
title: Black faces on modular kit pieces are usually the hidden side, not a broken material
topic: import-fbx-prefabs
tags: [modular kit, atlas, black faces, catacombs, unitypackage]
summary: Many modular environment kits UV-map never-seen faces to a solid-black atlas patch, so a black render means you are looking at the outside/buried side.
---
**Symptom:** A structural piece (vault shell, alcove wall, corridor module) from a commercial modular interior kit renders solid black. A debug material renders it the same; shader, normals and single-sided checks find nothing.
**Cause:** The kit UV-maps faces that are never meant to be seen to a solid-black patch of the atlas. Interior-only modules (e.g. A-frame vault corridors) are black shells from outside by design, and often contain no floor — you tile a separate floor piece under them. "Niche"/alcove prefabs can be thick freestanding wall segments with a black backing, not decals.
**Fix / rule:**
- If a piece renders black, first check which side you are looking at; move the camera inside the assembly.
- Trust the material↔atlas pairings that ship on the kit's prefabs even when the names look mismatched.
- Do not strip an extra invisible "collider" submesh material from floor pieces; it is intentional.
- Corridor end caps often face OPEN at default rotation — rotate 180° to close.
- Check module heights before mixing families (a 3 m alcove wall does not fit a 2.39 m vault).
**Verify:** Screenshot the assembly from inside; the black should disappear.

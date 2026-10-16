---
title: Find which mesh is actually visible by raycast before restyling walls
topic: materials-textures-shaders
tags: [shell mesh, blockout, raycast, submaterial, restyle, z-fighting]
summary: Blockout wall boxes often sit behind an imported shell mesh; restyling or overlaying them changes nothing — raycast to find the visible renderer and retexture its shared material.
---
**Symptom:** you retexture or overlay the `Wall_*` boxes and nothing changes on screen, or overlays end up recessed and invisible; hand-built pillar overlays z-fight.

**Cause:** the visible walls/floor/ceiling come from one imported shell mesh per area with a few submaterials (Floor / Wall / Ceil), and the old blockout boxes sit behind it. The shell may also include pillars.

**Fix / rule:**
- Raycast from the player position toward the surface and read `hit.collider` / renderer to identify what is seen.
- Restyle by editing the **shared submaterial** asset (one edit changes every wall in that area). Map material → area first; names can be misleading.
- To restyle part of a shell, remap the renderer's material array by name, or split submeshes (e.g. by triangle centroid height) into a new mesh asset and re-point MeshFilter + MeshCollider. Record the split rule so it can be re-run if the shell is regenerated.
- Under a parent with its own transform (offset + 180° yaw), world-authored meshes need world `position = zero; rotation = identity` after parenting.

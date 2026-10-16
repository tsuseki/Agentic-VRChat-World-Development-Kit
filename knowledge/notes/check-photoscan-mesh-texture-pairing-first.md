---
title: A photoscan mesh wearing another scan's texture passes every texture metric
topic: materials-textures-shaders
tags: [photoscan, mesh texture mismatch, UV, Poly Haven, invariant, audit]
summary: A scan's albedo is only meaningful under its own mesh's UVs; a mismatched pairing reads as a corrupted smear while every texture-quality metric is normal.
---
**Symptom:** A photoscanned rock looks like a "cracked geode / rainbow chevron fan" smear. Diagnoses of open shells, AO crush, missing base cap, resolution all fail, while an identical-looking sibling right beside it renders perfectly.

**Cause:** The object is mesh `boulder_03` carrying `boulder_04`'s photoscan texture. Under another scan's UVs the albedo forms swirls that look coherent but correspond to nothing. The texture itself is fine, so mean, texel density, UV anisotropy and high-frequency energy all read normal. No property of a texture measured alone can reveal a pairing error; the tell is relational.

**Fix / rule:** When a photoscan prop looks corrupted, smeared or "low-res", check mesh/material pairing **first**, before orientation, AO, UVs, tint or resolution. Raycast the failing pixels, resolve the hit triangle to GameObject + mesh + material, and assert the albedo name matches the mesh's source asset. Audit the whole set (the bug hit several objects across different meshes) and add a permanent build-time invariant `meshTextureMismatches == 0`, scoped to **every** material in the scene, not just the family where you found it; a narrow invariant reports green and reads as proof.

---
title: Swap heavy props for decimated meshes by MeshFilter, keeping material slot order
topic: performance
tags: [decimation, LOD, MeshFilter, material overrides, triangles, import scale]
summary: Decimating 20k–29k-tri fixtures to 5k–8k saved ~950k tris; per-renderer material overrides survive a MeshFilter swap only if slot order is kept, and scale/axis conventions may differ from the source FBX.
---
**When:** a handful of repeated hero props dominate the triangle budget (e.g. 36 wall lamps at 20k tris, 19 chandeliers at 29k).

**How:**
- Decimate in Blender (lamp 20,338 → 4,999; chandelier 29,301 → 8,000), preserving material slot names and **order**.
- Swap each instance's `MeshFilter.sharedMesh`; per-renderer material overrides survive because slot order is unchanged.
- Generate UV2 on import (`generateSecondaryUV`) if the export has none.

**Pitfalls:**
- A Blender metre-Y-up export imports at `globalScale` 1, while cm-authored sources often use 100 — and any per-instance −90° X Z-up compensation on the old instances must be removed (`rot * Inverse(Euler(270,0,0))`).
- Split normals on small panes can be lost (cosmetic).
- Before decimating, consider whether the prop should be lightmapped at all.

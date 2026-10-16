---
title: Resolve Z-up per source file, not per mesh by aspect; place by renderer bounds
topic: import-fbx-prefabs
tags: [up axis, z-up, fbx, pivot, scatter, bounds placement]
summary: A size.z > size.y test to detect Z-up meshes rotates wide, low Y-up plants onto their backs; decide the axis once per source file and place by renderer bounds, not pivot.
---
**Symptom:** Thousands of scattered plants render as flat starbursts lying on the ground; bounds still report plausible heights.
**Cause:** `if (bounds.size.z > bounds.size.y * 1.4f) rotate(-90,0,0)` fires on legitimately wide, low Y-up shrubs.
**Fix / rule:**
- Resolve the up-axis once from the source file and hard-code it per family (e.g. `ZUP = n => n.Contains("<family>")`).
- FBX root pivots can sit metres from the mesh, so `transform.position = target` misplaces it (a density sweep read 100% bare because all plants landed 3 m off). Place by renderer bounds: `transform.position += target - WorldBounds(g).center`.

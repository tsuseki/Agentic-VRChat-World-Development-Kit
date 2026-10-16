---
title: Solve metres-per-UV from the mesh's own triangles before setting texture tiling
topic: geometry-meshes-uvs
tags: [UV, tiling, mainTextureScale, texel density, ProBuilder, primitive]
summary: Primitives, ProBuilder and hand-built meshes use different UV conventions; solve metres per UV unit from a triangle instead of inferring from object size or trusting reviewer figures.
---
**Symptom:** Many surfaces of different sizes (0.42 m to 3.60 m) share one hard-coded tiling, and both a reviewer's millimetre figures and a first fix assume UVs run 0..1 across each surface. A reported "5x grain jump" between two pieces turns out to be fiction.

**Cause:** Several conventions coexist:
- Unity `Cube` primitives: UVs 0..1 per face, so metres per UV is the object size along that face's axes, which depend on the face (top: u->localX, v->localZ; front: u->localX, v->localY; side: u->localZ, v->localY).
- ProBuilder auto-UV and many hand-built meshes: world-scaled UVs, 1 UV unit = 1 m regardless of size.

**How:** Per renderer, pick the dominant face by summed triangle area (bucket triangles by rounded world normal). On that face's largest-UV-area triangle solve:
```
dP/du = ( e1*d2v - e2*d1v) / det
dP/dv = (-e1*d2u + e2*d1u) / det      det = d1u*d2v - d2u*d1v
```
with `e1, e2` world edge vectors and `d*u/d*v` the matching UV deltas. `|dP/du|`, `|dP/dv|` are metres per UV unit; `mainTextureScale = metresPerUV / desiredPeriod`. Keep `dP/du.normalized` too: it reveals which world axis u runs along and catches swapped-axis meshes.

**Pitfalls:**
- The period is not the tile size: a mosaic texture packing 8 tiles per repeat needs a 0.80 m period for 100 mm tiles. Count the grout lines in the texture first.
- One material cannot serve many surface sizes; use per-object material variant assets (they serialize safely) rather than relying on property blocks.

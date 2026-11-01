---
title: Photoscan rocks: box-projection UV2 in Unity instead of the auto unwrap
topic: geometry-meshes-uvs
tags: [UV2, photoscan, rocks, GenerateSecondaryUVSet, Scale In Lightmap]
summary: Unwrapping.GenerateSecondaryUVSet cut a scanned rock into ~1,150 charts at every setting; six planar charts by dominant world-normal axis, shelf-packed, give fill 0.23-0.43 in ~19 ms per mesh.
---
**Symptom:** scanned rocks baked with blotchy, torn lightmaps; `Unwrapping.GenerateSecondaryUVSet` produced ~1,150
charts per rock at every parameter set tried (hardAngle 88–180, angleError 0.08–1, packMargin 0.004–0.03), ~2.7 s
per mesh.

**Fix / rule:** box-projection UV2 in an editor script: assign each triangle to one of 6 planar charts by its dominant
world-normal axis, split vertices per (vertex, chart), shelf-pack the charts with the scale found by bisection (margin
0.04). Fill 0.23–0.43, ~19 ms per mesh. Write it to a world-owned mesh copy. Then Scale In Lightmap =
`max((13/tpu)² / (2·fill), ((10 + 6)/(tpu·sqrt(2A)))²)` (tpu = texels per unit, A = world surface area), set through
`SerializedObject` plus `PrefabUtility.RecordPrefabInstancePropertyModifications`.

**Verify:** read the rect sizes back from the baked lightmap: minimum 11.5 texels across on 26 rocks; the reviewer
measured 8.5–12.8 texels/m.

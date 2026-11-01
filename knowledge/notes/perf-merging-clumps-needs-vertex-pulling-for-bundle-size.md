---
title: Merged clump cells: pull vertices from tables, or the merge blows the upload budget
topic: performance
tags: [vertex pulling, mesh merge, bundle size, ground cover, LODGroup]
summary: Merging instanced clumps bakes every instance's vertices into the bundle and LZ4 compresses quantized vertices poorly; store 4-byte ids per vertex and rebuild the clump vertex in the shader from small point-sampled tables.
---
**Symptom:** merging 1.225 M ground-cover vertices into 16 m cells took a scene bundle from 182.5 MB to 218.0 MB at
48 B/vertex and still 205.0 MB at 28 B/vertex (F16 position, SNorm8 normal, UNorm16 UV, RGBM8 irradiance).

**Fix / rule:** vertex pulling (189.1 MB). Each cell vertex is one `VertexAttribute.Position` `UNorm8 x4` id: clump
index lo/hi, prototype vertex, prototype. The vertex shader rebuilds the clump vertex with `tex2Dlod` from
point-sampled, clamp-wrapped tables 2048 texels wide: prototypes (`RGBAFloat`, 3 texels per prototype vertex:
position+u, normal+v, colour), clumps (`RGBAFloat`, 2 texels: cell-space origin + hash input, rotation quaternion
× √scale, which encodes uniform scale), SH (`RGBAHalf`, 7 texels: the `unity_SHAr…unity_SHC` constants, evaluated per
vertex at the wind-bent normal and added as indirect diffuse under `noambient`). Limits: ≤ 255 prototypes, ≤ 255
vertices per prototype, ≤ 65,535 clumps, uniform positive scale, single-LOD clumps; cells split per blended
reflection-probe set, one submesh per material. Cell cull height = the farthest clump's own cull distance plus the
cell radius, so no clump culls earlier than before (cost: up to ~11 m of extra far clumps, ≤ 0.14 % of pixels).
Builder template: `.omp/skills/vrchat-world-optimization/scripts/GroundCells.cs.txt`.

**Pitfalls:**
- Probe-lit clumps only: lightmapped ground cover would lose its lightmap.
- ~13 point fetches per vertex: the editor can't measure that GPU cost; confirm with a client capture on a weak GPU.
- The tables are flagged by uncompressed-texture audits; they are data and must stay uncompressed, unmipped, unresized.
- Rebuild after every bake (the SH table copies the baked probes) and every planting edit.

**Verify:** builder self-check position error ~1 µm and SH error 0; same-camera diff ≤ 0.14 % of pixels > 18/255;
bundle-size A/B.

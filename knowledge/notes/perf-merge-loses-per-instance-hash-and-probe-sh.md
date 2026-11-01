---
title: A merge destroys per-object shader inputs: origin hashes and per-instance probe SH
topic: performance
tags: [mesh merge, static batching, light probes, hash tint, SH]
summary: Before merging instanced clumps, list what the shader derives per object; origin-hashed variation and per-instance probe SH are lost, and one probe per cell is not close enough.
---
**Symptom:** a draft merge of grass clumps lost each clump's hashed tint (from `unity_ObjectToWorld` translation, e.g.
`frac(sin(dot(o.xz, float2(12.9898, 78.233))) * 43758.5453)`) and lit whole cells with one probe sample. Static
batching collapses the origin hash the same way.

**Cause:** both values come from the renderer, which no longer exists per clump after a merge.

**Fix / rule:** a world-owned shader copy that reads both from vertex data or a table. Neither one probe per cell nor
an LPPV is close enough: the SH spread inside a 16 m cell was median 45 % (21 % at 8 m), with 26.5k clumps more than
10 % off the cell mean. Reproduce Unity's exact per-instance sample with
`LightProbes.GetInterpolatedProbe(r.probeAnchor ? r.probeAnchor.position : r.bounds.center, r, out sh)` (SH error 0).

**Pitfall: hash inputs precomputed on the CPU must match the GPU's rounding bit for bit**, because
`sin(...) * 43758` turns a 1-ulp difference into a different random value. Emulate the `dp2` fused order in double:
mode 0 = `p = (float)(x*H1); (float)(z*H2 + p)`; test the candidate orders against a reference render. Mode 0
matched on the development GPU. [INFERENCE] Other vendors may round differently; a mismatch only reshuffles the tint
pattern, never the geometry.

**Verify:** same-camera diff of the merged vs original clumps with wind frozen.

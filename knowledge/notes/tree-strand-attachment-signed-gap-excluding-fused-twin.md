---
title: Measure hanging-strand attachment as a signed gap to the host, excluding the strand's own fused twin
topic: geometry-meshes-uvs
tags: [trees, aerial roots, hanging strands, attachment, signed distance, far LOD, measurement]
summary: Whether hanging strands or roots are attached is the signed distance from each strand top to the nearest host surface (+ outside, − inside) with the strand's own fused twin excluded; unsigned distance flagged tops tucked 5–7 cm inside the limb, measuring to a twin 5–6 cm away flagged more, and counting islands per level is no detachment test.
---
**Symptom:** A detachment check flagged 12 hanging roots as "off" their limbs after a LOD rebuild; only 1 was real (0.10 m, already present in the previous build).

**Cause:**
- Unsigned distance counts tops tucked 5–7 cm inside the limb as gaps.
- The nearest surface to a strand of a fused pair can be its twin strand 5–6 cm away, not the limb.
- Counting connected islands per level says nothing: decimation merges and splits strands.

**Fix / rule:** For each strand top, the signed distance to the nearest host surface (+ outside, − inside), excluding the strand's own fused twin. Flag only positive gaps above the tolerance.

**Verify:** run it on the previous accepted build first (positive control) and compare the flagged lists.

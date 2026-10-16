---
title: Geometry flames for a gas fire pit: small, deep orange, glow hidden between stones
topic: materials-textures-shaders
tags: [emissive, flame, fire pit, emission colour, props]
summary: First-pass emissive flames come out ~3× too tall and too yellow; a gas fire pit reads right at 45–145 mm blades of deep orange with the glow card sunk out of sight.
---
**Symptom:** Tapered emissive flame blades 0.10–0.34 m tall at emission (2.60, 0.95, 0.20) read as a cartoon yellow saw blade on an orange slab.
**Fix / rule (reads as a gas fire pit):**
- ~30 blades, 0.045–0.145 m tall, height profiled `sin(u*π)` along the trough so the ends taper.
- Emission ≈ (1.85, 0.52, 0.09) — deep orange; yellow makes it cartoonish.
- Base 16–36 × 14–32 mm, random yaw, ±8° lean; base quad tapering to a 16% ridge = 10 tris each (~300 total).
- Narrow the glow card underneath (~55% depth) and sink it ~65 mm below the rock tops so it glows between stones and is never seen as a slab.
- Burner body must be a dark material; bright stainless shows as a grey sliver through the gaps.

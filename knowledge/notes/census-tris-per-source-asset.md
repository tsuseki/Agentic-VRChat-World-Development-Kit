---
title: Census triangles per source asset before tuning counts
topic: performance
tags: [triangle budget, vegetation, scatter, decimation, census]
summary: One decorative accent at 2,999 tris × 604 instances was 56% of a planting budget; group by source asset and print n, total and per-instance tris before touching density knobs.
---
**Symptom:** A scattered planting sits at 3.23 M tris and every knob (instance count, grid step, height band) moves it only slightly.
**Cause:** One asset dominated: `flower` n=604 × 2,999 tris = 1.81 M (56%), versus groundcover at ~120 tris each.
**Fix / rule:**
- Group by source asset; print `n`, total and per-instance tris. Decimating the one heavy asset (2,999 → 135) dropped the total to 1.50 M without moving a placement.
- Watch second-order costs: a "tall accent" band at 14% of instances kept full-resolution meshes (another 1.6 M); cut to ~4.5% on wide beds.
- Multi-submesh foliage resists decimation (the decimator keeps a minimum face count per submesh; one plant floored at ~370 tris). Demote such assets to rare accents.

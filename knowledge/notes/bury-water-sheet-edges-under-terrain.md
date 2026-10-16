---
title: Make water sheets wider than the basin and bury their edges
topic: geometry-meshes-uvs
tags: [water, river, lake, shoreline, terrain, mesh edge, smoothing]
summary: Spiky or straight water edges are the water mesh's own polygon boundary showing; extend the sheet up the banks so the terrain contour forms the shoreline, and verify by minimum edge burial.
---
**Symptom:** Water edges look "not natural, too spiky": straight cuts across open water with hard kinks where segments meet.

**Cause:** Never the water shader or shoreline shape: the water mesh **ends before the bank does** (e.g. a 65 m-wide ribbon in a channel whose waterline sits at ~50 m half-width). A shoreline should be the terrain's iso-contour at the waterline, which you get for free when the sheet is wider than the basin and the terrain clips it.

**Fix / rule:**
1. Walk outward from the centreline/centre until terrain height > waterY + ~0.8 m.
2. Push the edge a further ~8-15 m up the slope (`BURY`) so it is genuinely underground.
3. Smooth the boundary (Gaussian over ±7 stations). For a closed lake, **median-filter first**: a radial fan misfires where the basin is not star-shaped and a plain Gaussian leaves a large radial spike.
4. Do not finish with `radius = max(smoothed, raw + margin)`; it guarantees burial but re-injects the kinks. Raise `BURY` until the clamp stops firing instead.
5. Do not trace the waterline exactly either; an edge sitting on the contour z-fights and gaps.

**Verify:** Compute the **minimum burial across every edge vertex**, not by eye; negative anywhere means a straight cut is visible somewhere. (Example result: river 0.92 m, lake 0.63 m; max second-difference along the bank 71 m -> 21 m.)

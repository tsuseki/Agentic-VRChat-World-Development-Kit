---
title: Bake the sun: avoid realtime or Mixed directional lights in VRChat worlds
topic: performance
tags: [directional light, baked lighting, realtime shadows, Mixed, shadowmask, light probes, VRChat performance]
summary: Recommended: keep the sun as a Baked light even in large outdoor worlds, aim for big-scale shadows only, and cover everything that moves with light probes.
---
**When:** Choosing the sun setup for any VRChat world, including large open-world or multi-km outdoor scenes where baking seems to buy little.

**Rule (recommended practice):** Do not use a realtime or Mixed-mode directional light (including Mixed + Shadowmask / distance shadowmask). VRChat runs on a huge spread of hardware including low-end PCs, and realtime shadow cascades over an open-world-sized scene are among the biggest avoidable frame costs. Optimise for the floor of the hardware range.

**How:**
- Keep the sun in the scene as a **Baked** light so Bakery has something to cast from; it has zero runtime cost.
- Aim for **big shadows** (mesas, buildings, rock masses), not crisp per-object contact shadows. Coarse lightmap resolution on big terrain is then a feature, not a compromise.
- Nothing is lit at runtime, so **anything that moves must be inside a LightProbeGroup** or it renders flat and unlit (e.g. a probe grid over a whole drivable surface for vehicles). Re-bake probes after every lightmap bake.

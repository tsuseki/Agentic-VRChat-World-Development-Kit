---
title: Invisible ShadowsOnly proxy boxes must float and match object height, and only for things that never move
topic: lighting-baking
tags: [shadow proxy, ShadowsOnly, ContributeGI, contact shadow, vehicles, bake]
summary: A ShadowsOnly proxy resting on the ground bakes a black slab, one shorter than the object hides its shadow underneath, and anything a player can move should get no baked shadow at all.
---
**When:** Giving a non-static object (parked vehicle, prop) a baked contact shadow via an invisible `ShadowCastingMode.ShadowsOnly` + ContributeGI box.

**First ask whether the object stays put.** A baked contact shadow is a painted-on lie the moment a vehicle drives away. Anything a player can move gets `ShadowCastingMode.Off` and no static flags; if it needs grounding, use light probes and at most a small unlit blob decal parented to it. Bake proxies only for furniture-like objects that never move (or respawn to the identical transform and are never driven).

**Pitfalls:**
1. **A box resting on the ground bakes a pure-black hard-edged slab**: the ground texels sealed inside see no light. It reads as a broken decal, not lighting. Lift the box to real underbody clearance (bottom at ground +0.22 m for cars, +0.10 m for karts).
2. **A box shorter than the object hides its own shadow underneath.** With the sun at 43 degrees, a 0.9 m box inset to 80 % offset its shadow only ~1 m, entirely under the car. Box top at ~85 % of body height, footprint ~0.95x the body.
3. **Even a correct proxy shadow is nearly invisible at eye level.** A reviewer shot from the sun side reported "no shadows" while they were baked 58 % darker than clear ground. Measure before acting on such reports.
4. Seat proxies with a raycast filtered to the ground layer/objects; an unfiltered ray hits the object's own body. Do not size boxes from skinned renderer bounds (bind-pose inflated).

**Verify:** Top-down orthographic render at known px/m, plus a pass with proxies temporarily `ShadowCastingMode.On` to see the boxes. Decisive test: hide the objects and re-render top-down to see every baked footprint; sample under-object vs clear ground luminance (~0.42 ratio is a healthy contact shadow, ~0.9 means missing).

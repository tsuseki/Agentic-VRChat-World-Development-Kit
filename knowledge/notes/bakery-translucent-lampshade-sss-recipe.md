---
title: Translucent glowing lampshade in Bakery: lightmapped shadow-casting SSS shade plus a separate emissive bulb
topic: lighting-baking
tags: [bakery, lampshade, sss, light mesh, emission, translucency]
summary: A BakeryLightMesh on the shade gives a flat cardboard look because Bakery never lightmaps light-mesh objects; split the mesh into a shadow-casting computeSSS shade and a small emissive bulb child carrying the light mesh.
---
**Symptom:** A lampshade with `BakeryLightMesh` and raised `_EmissionColor` reads as a flat cardboard box.
**Cause:** Bakery skips lightmapping any object carrying a light mesh, so the shade is probe-lit and its emission is a uniform shader add.
**Fix / rule:**
1. Split shade body from bulb (a radius-from-axis histogram usually shows a clean gap).
2. **Shade:** normal lightmapped mesh, `shadowCastingMode = On`, `ContributeGI`, generous `scaleInLightmap` (e.g. 6), generate UV2, `BakeryLightmapGroupSelector` → a group with `computeSSS = true`.
3. **Bulb:** small child, `shadowCastingMode = Off`, the sole `BakeryLightMesh` + bright emissive material (`lightmapIndex -1` is correct).
4. Zero the shade material's emission.
**Why:** SSS simulates light transmitting through an occluder — a non-casting shade transmits nothing, so SSS can't be toggled on over a fake-emitter setup. Shade emission adds a flat term that flattens the transmission gradient (A/B: emission on = pale flat; off = saturated amber with falloff). With the light mesh off the shade, Bakery ignores its material emission (and `BakedEmissive` flags), so emission/albedo can be tuned after the bake with no rebake. Baked emissive geometry is also faster than a point light and puts the source where it visually is.
**Pitfalls:** Tune SSS brightness with `sssColor`, not `sssSamples` (quality). General pattern: anything that must both emit and be properly lit gets split into a tiny emitter child plus a lightmappable body.

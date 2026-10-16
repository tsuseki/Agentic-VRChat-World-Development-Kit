---
title: Swapping the skybox: check what it feeds, and rotate the HDRI so its sun matches the baked light
topic: probes-reflection-and-light
tags: [skybox, HDRI, Panoramic, _Rotation, BakerySkyLight, reflection probes, BC6H]
summary: A skybox swap needs no rebake only if ambient is flat and the sky light has no cubemap; align a lat-long HDRI sun to the baked directional light with a closed-form _Rotation.
---
**When:** replacing a skybox in a baked world (e.g. a Procedural sky at exposure 4.76 blew the horizon into a white band; a CC0 HDRI replaced it).

**Check first:** a swap is cosmetic-only if `RenderSettings.ambientMode = Flat` (sky colour black or fixed) **and** the `BakerySkyLight.cubemap` is null (bakes from its flat colour). Then only reflection probes (`defaultReflectionMode = Skybox`) would benefit from a rebake. If either uses the sky, rebake. Verify per world.

**Sun alignment:** the bake locks the sun angle, so pick an HDRI with a similar sun **elevation** (low-sun/sunset skies need the light re-aimed and a rebake). To rotate the sky instead of the light in `Skybox/Panoramic` (LatLong): find the brightest texel's `u`, then
```
_Rotation = degrees( (0.5 - u) * 2π  -  atan2(d.z, d.x) )      // d = -light.transform.forward
```
Find the peak texel by `Graphics.Blit` into an `ARGBHalf` RenderTexture + `ReadPixels` — `GetPixels` fails on BC6H, and reimporting uncompressed costs ~3 min per 4K HDR.

**Pitfalls:** reimporting several 4K HDRs to BC6H blocks the Unity MCP bridge for minutes (`Connection closed before reading expected bytes`) — wait on the `.meta` files, don't retry. Keep a tuned Procedural fallback (exposure ~1.35, atmosphere 1.0, dark ground).
Related: [match-skybox-sun-azimuth-to-the-baked-sun](match-skybox-sun-azimuth-to-the-baked-sun.md) (measure azimuth and elevation by a peak sweep).

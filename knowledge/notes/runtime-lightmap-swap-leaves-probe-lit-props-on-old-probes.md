---
title: In a runtime lightmap swap, non-lightmapped props keep the old bake's light probes
topic: probes-reflection-and-light
tags: [lightmap swap, light probes, Udon, LightProbeUsage.Off, day night, MaterialPropertyBlock]
summary: Swapping lightmapIndex changes only lightmapped renderers; probe-lit props keep the single baked probe set, and LightProbeUsage.Off binds a zero probe that renders them black.
---
**Symptom:** After a runtime lights-out swap, walls go dark blue but a door pane, sconce, lamp parts and trim still glow warm, reading as "the switch missed some fixtures". Every fixture already has an emission property block.

**Cause:** Swapping `Renderer.lightmapIndex` changes lightmapped renderers only. Renderers with `lightmapIndex == -1` and `BlendProbes` keep sampling the scene's single baked probe set. Probes cannot be swapped at runtime: `LightmapSettings` has no Udon node definitions, so `lightProbes` cannot be reassigned. `Renderer.lightProbeUsage` **is** exposed.

**Pitfall:** `LightProbeUsage.Off` does **not** fall back to `RenderSettings.ambientLight`; it binds a **zero SH probe**. A renderer that is also non-lightmapped then receives no light at all (a white sconce tube measured 0.0001 against a 0.0090 wall): a hole in the room.

**Fix / rule:** Find the class by query: every renderer in the affected volume with `lightmapIndex == -1 && lightProbeUsage != Off`. Split the list:
- Renderers that gain a lightmap in the alternate state: probes Off is safe.
- Still `lightmapIndex == -1`: add light back by object type. Emitters (tube, lit pane, bulb) get a dim `_EmissionColor` block calibrated to ~0.8x the luminance of the surface behind (measure; an `_EmissionMap` mask attenuates what you type, and the `_EMISSION` keyword must be enabled). Ordinary props get a synthetic SH probe (see [unlit-props-need-a-synthetic-sh-probe-not-emission](unlit-props-need-a-synthetic-sh-probe-not-emission.md)).

Avatars are the one case with no fix: they stay at the shipped bake's probe brightness unless their shader supports VRC Light Volumes.

**Verify:** Render each prop with its renderer enabled and disabled and compare its pixels to the surface behind; a ratio near 0 means it went black.

Related: [runtime-lightmap-swap-in-vrchat](runtime-lightmap-swap-in-vrchat.md), [editor-preview-state-ships-on-upload](editor-preview-state-ships-on-upload.md).

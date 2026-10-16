---
title: An object blinking between unrelated colours is outside the light-probe hull
topic: probes-reflection-and-light
tags: [light probes, extrapolation, tetrahedron, blinking, ambient probe, console warnings]
summary: Changing wrong colours on a moving/distant object come from light-probe extrapolation outside the LightProbeGroup volume; the Console warning names the world position.
---
**Symptom:** A prop flickers between arbitrary colours (orange one frame, green the next). One consistent wrong colour = asset bug; changing wrong colours = probes.
**Cause:** Outside the tetrahedralised probe volume Unity extrapolates from degenerate outer tetrahedra; crossing cells makes the colour jump. Common setups: the only LightProbeGroup covers an interior while props sit hundreds of metres away; `lightProbeUsage = UseProxyVolume` without a `LightProbeProxyVolume` component silently falls back to `BlendProbes`.
**Fix / rule:** For far-away/moving scenery, set `lightProbeUsage = Off` and `reflectionProbeUsage = Off` (a small interior reflection probe gets blended into distant objects too). They fall back to `RenderSettings.ambientProbe`, uniform and adequate for distant vegetation. Renderer-only change; no rebake.
**Verify:** Read the Console first: `Light Probe tetrahedron is malformed … at (x, y, z)` gives the world position and identifies the culprit class immediately — before building any per-frame colour detector.

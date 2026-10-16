---
title: Small emissive fixtures light nothing in a bake; give them a real Light
topic: lighting-baking
tags: [emission, baked emissive, downlight, spot light, fixture, pre-bake audit]
summary: Baked emissive contribution scales with emitter area, so a point-like emissive lens under about 0.25 m2 lights nothing and needs a baked Light component.
---
**Symptom:** Ceiling downlights built as ~0.2 m emissive quads look correct in close-up, their faces blow out to white, yet the corridor under them is near-black. A reviewer describes them as "paper squares glued to the ceiling", which sounds like a material note.

**Cause:** Baked emissive contribution scales with the emitter's **area**. 0.04 m2 at emission 3.1 puts no measurable light on the floor. The fixture is visibly lit, so the usual "unmotivated light" check passes; what is missing is the pool of light underneath.

**Fix / rule:** Parent a baked spot under each lens (cone ~62 degrees, range = drop to floor + 1.6 m), and ease the lens emission at the same time so it stops clipping to white now that it is not the only source. Long cove strips (around 10 m) are the genuine exception: they have the area to work by emission alone. Point-like fixtures never do.

Treat a finding as the name of a class: a reviewer photographing two rooms found two fixtures; a sweep found 86 across 13 rooms, none with a Light. Sweep before every bake:
```csharp
if (m.globalIlluminationFlags == MaterialGlobalIlluminationFlags.BakedEmissive
    && m.GetColor("_EmissionColor").maxColorComponent > 1.5f
    && DistanceToNearestLight(r.bounds.center) > 2.5f) Report(r);
```

**Verify:** The sweep reports zero, and the floor under each fixture shows a light pool in the bake.

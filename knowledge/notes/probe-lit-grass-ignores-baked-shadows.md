---
title: Probe-lit grass cards ignore baked cast shadows and stay sunlit under trees
topic: lighting-baking
tags: [grass, probe-lit, light probes, lightmap, baked shadows, vegetation]
summary: Grass cards lit by light probes don't see baked cast shadows, so they glow sunlit inside tree shadows; make them receive lightmaps or have their shader sample the terrain lightmap.
---
**Symptom:** After a bake with trees casting dappled shadows on the ground, the grass cards inside those shadows stayed fully sunlit, floating bright over a dark ground.

**Cause:** Probe-lit renderers take lighting from interpolated light probes, which are sparse and carry no shadow detail at grass scale; the baked shadow exists only in the ground's lightmap.

**Fix / rule:** Make grass receive lightmaps (lightmapped renderer with UV2, or merged cells), or give the grass shader the terrain/ground lightmap and sample it at the blade's root position. Probe-lit is fine only where there are no baked cast shadows to match.

**Verify:** a top-down and an eye-height capture of grass crossing a tree shadow edge: grass brightness must follow the ground shadow.

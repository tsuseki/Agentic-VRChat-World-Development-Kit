---
title: Check Light Volume coverage over the whole walk zone, and again after adding structures
topic: probes-reflection-and-light
tags: [VRC Light Volumes, coverage, outdoor, walk zone, 32-volume cap]
summary: Measure volume coverage as the share of reachable ground cells covered at feet, eye and head height; 3 % of one walk zone and three later buildings in another sat outside every volume until checked.
---
**Symptom:** 3 % of a world's walk zone (242 m²) lay outside every volume; in another, villas and a jetty end added
after the volume layout were uncovered.

**Fix / rule:** coverage = % of reachable ground cells (from the walk-test flood fill) whose feet, eye (1.3 m) and head
points lie inside a volume; target ~100 % (99.99 % measured). Re-run it after adding any structure. Outdoor layout that
worked within the 32-volume cap: 112 m tiles, 2.5 m voxels, ground −0.5 to +8 m, 27–29 volumes; widening boxes to close
the 3 % cost ~21 k voxels (206.6 k total, atlas 15.2 MB at 83×25×468 RGBAHalf).

**Verify:** the coverage % and the list of uncovered cells, quoted after every layout change.

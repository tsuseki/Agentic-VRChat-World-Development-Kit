---
title: Bare-soil complaints are about canopy coverage, not plants per m²
topic: placement-layout-design
tags: [planting, vegetation, coverage, density, scatter, metrics]
summary: Plants/m² can be uniform while some beds look bare; measure the fraction of soil hidden by any plant's footprint and fill the farthest uncovered sample.
---
**Symptom:** A reviewer reports "large expanses of bare soil" but plants-per-m² is uniform across all beds (2.2–3.8).
**Cause:** Density cannot see it: 20 tiny sprigs and 20 wide shrubs have the same count and look nothing alike. The eye reads how much soil is hidden.
**Fix / rule:** Sample the soil plane on a grid and test whether any plant's XZ bounds covers each sample. Measured: perimeter beds 18–35% vs feature beds 46–69% — exactly where the reviewer pointed. Target ≥70% per bed (result 71–82%). Place the next plant at the uncovered sample farthest from existing canopy, re-measure, repeat — this fills holes instead of thickening fine areas.
**General shape:** when a visual complaint survives a metric that says "uniform", the metric measures the wrong quantity. Ask what the eye integrates (area hidden, silhouette, contrast) and measure that; instance counts are almost never it.

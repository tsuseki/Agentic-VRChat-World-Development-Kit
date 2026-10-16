---
title: Do not inset a scatter grid from the container edge
topic: placement-layout-design
tags: [scatter, planting, coverage, inset, eye height, kerb]
summary: A scatter that insets its grid from the container edge leaves a bare band exactly where a standing player looks; inset by at most the plant's base radius and cap size at the edge instead.
---
**Symptom:** Adding 700 more plants to beds left measured bare soil unchanged (43.7% -> 43.7%). An identical metric after a big change means the work went to the wrong target.

**Cause:** The generator sowed on a grid inset 0.18 m from every kerb, a defensive margin against overhang. A keyed close-up showed every bed full in the middle and bare in a clean band along its front lip. At 1.6 m eye height you look down into the near kerb, so that band dominates the frame while the bed middle is foreshortened.

**Fix / rule:** Inset 0.18 -> 0.03 m with the same species and density: bare soil 43.7% -> 26.9%. In a scatter the container edge is the **most** visible zone. Inset by at most the plant's own base radius; if overhang is the worry, cap the plant **size** at the edge ([cap-prop-size-before-clamping-position](cap-prop-size-before-clamping-position.md)) rather than refusing to sow there.

Related: [unchanged-metric-means-wrong-target](unchanged-metric-means-wrong-target.md), [measure-plant-opacity-before-mass-planting](measure-plant-opacity-before-mass-planting.md)

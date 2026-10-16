---
title: Interior brightness sampling must require a ceiling, or it measures the roof
topic: agent-workflow-verification
tags: [lighting-qa, sampling, raycast, luminance, interiors, reachability]
summary: A sampler that raycasts down from above an area lands on rooftops and reports bright outdoor daylight as "interior too bright"; keep only walkable floors with a surface overhead.
---
**Symptom:** Interiors measured "too bright" (mean ~0.52-0.66, ~3% blown), so point lights were trimmed to ~0.5x - and the real interiors, already too dark (0.07-0.13 mean, ~15% dark), got darker, against an explicit request that the spawn area be brighter.

**Cause:** The sampler cast rays down from above the area's bounding box and landed on rooftops, which read as daylight with sky in frame.

**Fix / rule:**
- March the downward ray through successive hits; keep the first walkable floor that has a surface within ~14 m **above** it.
- Also apply the flood-fill reachability filter so sealed voids and wall cavities don't enter the statistics.
- Tell-tale: an identical worst-blown figure (e.g. 10.6%) across unrelated areas - that is the sky, not the scene.

Related: [reviewer-findings-need-reachability-triage](reviewer-findings-need-reachability-triage.md)

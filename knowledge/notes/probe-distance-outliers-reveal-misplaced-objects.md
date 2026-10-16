---
title: Nearest-light-probe distance outliers reveal misplaced objects
topic: agent-workflow-verification
tags: [light probes, placement, audit, outlier, coordinates, doubled position]
summary: Sorting probe-lit renderers by distance to the nearest light probe also detects objects placed at wrong coordinates; a worst value orders of magnitude above p90 is a coordinate bug.
---
**Symptom:** A probe-coverage sweep reports worst nearest-probe distance = 1,183 m for a lamp in a remote room. Nothing else flagged it: no screenshot framed it, and the group's bounding box just looked "large".

**Cause:** The lamp's position had been applied twice; every component was exactly 2x the intended value (`-2.40, 0.96, 2388.80` instead of `-1.20, 0.48, 1194.40`).

**Fix / rule:** After any scripted placement pass, print median, p90 and **worst** nearest-probe distance with the offending object's name. Healthy interior numbers look like median 1.3 m / p90 2.1 m / worst 3.1 m. A worst value far above p90 is a coordinate bug, not a probe-density problem: fix the object, don't add probes. A doubled position shows up as every component being an exact 2x of a plausible value; halve the world position and re-seat on the supporting surface.

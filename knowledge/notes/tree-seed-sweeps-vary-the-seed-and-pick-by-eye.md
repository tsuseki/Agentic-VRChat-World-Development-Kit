---
title: A tree seed sweep must really vary the seed, and its best score is a shortlist, not the pick
topic: agent-workflow-verification
tags: [trees, seeds, sweeps, metrics, silhouette]
summary: A seed scan that rewrote only one literal built the same tree five times (identical STAT lines across seeds), and the best-scored seed of a lobe/score metric still had lobed crowns; rewrite any seed value, check that the STAT lines differ, and choose from 4-side silhouettes by eye.
---
**Symptom:**
- A scan over seeds 16–20 reported all of them passing; all five builds were the same tree.
- The best-scored seed of a 9-seed sweep showed three stacked lobes; the seed ranked 3rd (0.578 vs 0.568) gave the broader single dome that was kept.

**Cause:**
- The scan's substitution matched only `seed=11,`; once the config said 14, nothing was replaced.
- Crown metrics (sky, lobe, deviation) don't rank what a reviewer sees as lobes.

**Fix / rule:**
- Rewrite any seed value in the config (regex on the key, not one literal), and stop if two seeds print identical `STAT` lines.
- Treat the metric ranking as a shortlist; pick from front and full silhouettes from 4 sides by eye.
- Back up the config before a sweep that rewrites it, and restore the outputs if the old seed stays.

**Verify:** `STAT <name> seed N` differs per run and the tris / bounds lines differ; a contact sheet of every seed's 4-side silhouettes.

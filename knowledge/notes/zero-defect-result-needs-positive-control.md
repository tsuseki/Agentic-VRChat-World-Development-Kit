---
title: A zero-defect sweep proves nothing without a positive control on the same frames
topic: agent-workflow-verification
tags: [positive control, metrics, verification, pixel sweep, false negative]
summary: "0 defects" is also what a broken sweep outputs; run identical poses, mask and threshold against a state known to fail and quote both numbers.
---
**Symptom:** "0 hot pixels across all 10 poses."

**Cause:** A clean result and a dead metric are indistinguishable from the number alone: camera pointed at a wall, render never happened, mis-encoded capture, mask selected nothing, threshold typo.

**Fix / rule:** run the **identical poses, mask and threshold** against a state known to trip the metric, in the same session, and quote the pair — e.g. "0 px at night, 6.7k–43k px in day on the same poses". Pick the control from a state you already have (pre-fix build, other side of a toggle, `git stash`). If none exists, manufacture one (raise a value until it must trip) and confirm the metric fires.

A zero is the most persuasive-looking and least verifiable result, and it arrives exactly when you most want to stop.

**Scope:** this note covers a sweep that reports zero defects. A metric you invented while looking at the broken object is validated on a working sibling instead ([validate-ad-hoc-metrics-on-a-known-good-sibling](validate-ad-hoc-metrics-on-a-known-good-sibling.md)); a renderer-toggle diff reading 0 px is checked by toggling a second object known to be in shot ([unchanged-metric-means-wrong-target](unchanged-metric-means-wrong-target.md)).

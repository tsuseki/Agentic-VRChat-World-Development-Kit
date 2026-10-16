---
title: Run an ad-hoc diagnostic on a known-good sibling before trusting it
topic: agent-workflow-verification
tags: [metrics, diagnostics, control, A/B, verification]
summary: A metric invented while looking at a broken object encodes assumptions about it; run it on a working sibling first, and if it condemns that too, the metric is wrong.
---
**Symptom:** An invisible river is tested by sampling every water vertex against terrain height: "800 of 800 vertices are buried", a confident second defect. The same test on the **visible** lake says "288 of 289 buried".

**Cause:** The metric encoded a wrong assumption. Those water sheets are designed with their rim buried up the bank (see [bury-water-sheet-edges-under-terrain](bury-water-sheet-edges-under-terrain.md)), so perimeter vertices are supposed to be underground. Sampling the centreline showed 7.3 m of water depth: placement was fine. The real bug was inverted face winding.

**Fix / rule:** Before quoting any ad-hoc number as evidence, ask what it returns on the version that works. Prefer a differential: measure broken and good side by side in the same call and report the pair, never the broken value alone. With no sibling, take the control from version-control history or a rendered A/B.

Related: [zero-defect-result-needs-positive-control](zero-defect-result-needs-positive-control.md), [metrics-that-cannot-see-their-defect](metrics-that-cannot-see-their-defect.md)

---
title: Automatic leaf-size measurement misreads dense sprays; measure leaf size by hand on a pixel grid
topic: agent-workflow-verification
tags: [trees, leaf size, atlas, segmentation, measurement, verification]
summary: A leaf-size script segmented overlapping leaves as a few big ones (reported 2.97× too big on leaves hand-measured ~1.1×) and skipped volume-crown trees; measure leaf px on a grid in 2 atlas cells and convert with card length / cell px.
---
**Symptom:** After switching to dense foliage sprays, a leaf-size check reported the leaves 2.97× too big for the species; hand measurement gave ~1.1×. The same tool silently skipped trees built in spindle/ellipsoid (volume-crown) modes.

**Cause:** Connected-component segmentation on the alpha merges overlapping leaves into a few large blobs, so dense clumps look like giant leaves. Volume modes have no branch/card mapping the tool understands, so it skips them instead of failing.

**Fix / rule:** For dense sprays measure by hand: overlay a pixel grid on 2 atlas cells, measure several typical leaves' length in px, then leaf length (m) = leaf px × card length / cell px. Compare with the species' real range (accepted up to ~1.4× for needles/large cards). Treat the tool's number as a positive-only signal on sparse sprays.

**Verify:** a hand measurement on two cells agrees within ~20 %; a positive control (a known-size sparse spray) reads correctly in the tool before trusting it on any new atlas.

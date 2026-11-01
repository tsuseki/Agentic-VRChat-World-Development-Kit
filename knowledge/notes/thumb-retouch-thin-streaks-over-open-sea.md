---
title: Retouch thin vertical streaks over open sea with a row median, span taken from neighbours
topic: placement-layout-design
tags: [thumbnail, retouch, streaks, sea, horizon, image processing]
summary: Faint vertical streaks over far sea in a supplied frame are removed by replacing the brightened columns with a wide horizontal median of the same rows inside the sea span, where each column's sea span comes from its neighbours, because the streak pixels fail the sea colour test and survive on the anti-aliased horizon rows otherwise.
---

**Symptom.** A supplied world frame chosen for a thumbnail had faint brightened vertical columns over the far open sea (smoke or particle streaks). Re-rendering was not an option, and cropping cut the subject.

**Cause.** The streak lifts a few columns by a few levels over a band that is otherwise smooth row by row. A per-pixel "is sea" colour mask built from the frame excludes the streak pixels themselves, so a retouch limited to that mask skips the streak exactly where it is; on the anti-aliased horizon rows the streak survived two attempts.

**Fix / rule.**
- Replace the brightened columns with a wide horizontal median of the same rows, restricted to the sea span.
- Take each column's sea span (top and bottom row) from its neighbours with a min/max filter about 61 px wide, not from the column itself.
- Never paint pixels that are greener than blue or brighter than 200: those are trees, sand and sky.

**Verify.** Diff the result against the graded raw and render the changed pixels (> 8/255) as a magenta overlay: only the streak columns inside the sea band may change. Compare the high-pass column-profile std and peak (`col_mean − uniform_filter1d(col_mean, 41)`) in the treated band before and after against an untreated control band (std 1.48 → 1.09, peak 7.2 → ≈ 3.9 in one frame). Check at 2× zoom.

---
title: Check the live scene before acting on each review finding — some may already be fixed
topic: agent-workflow-verification
tags: [review, findings, stale screenshots, verification]
summary: A reviewer's screenshots can predate fixes already applied; dump the named objects' current state before editing, and record already-closed findings with the proving measurement.
---
**Symptom:** Review findings describe defects (a mug straddling a mat edge, a wrong-coloured pen holder, a stray sheet of paper) that a fix pass had already corrected before the review started.
**Cause:** A long fix round overlapped the review; acting on the text would have moved correct objects and invalidated a re-review.
**Fix / rule:** For every finding, query the named GameObjects first (position, bounds, material, children). Record findings that are already resolved as *verified already-closed* with the measurement that proves it, rather than silently skipping them.

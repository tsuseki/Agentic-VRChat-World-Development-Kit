---
title: Never characterise a room from one camera yaw
topic: agent-workflow-verification
tags: [render-metrics, luminance, lighting-qa, sampling, camera-poses]
summary: A room luminance measured from a single view varies more with facing than with its lighting, so sample at least four yaws per point and report the mean and spread.
---
**Symptom:** One eye-height shot per room flagged three rooms as too dark or flat (e.g. mean 0.071 with 53% of the frame below 0.05). Re-rendering the identical positions at four yaws erased all three findings (mean 0.123, 30% dark).

**Cause:** The single shot happened to face a dark corner. Facing dominates per-room differences, so a one-angle sample is a coin flip dressed as a measurement.

**Fix / rule:** Sample >= 4 yaws per point; report the mean **and** the per-yaw spread. If yaws disagree by more than the between-room differences you are ranking, the metric isn't measuring what you think. Cheap: 56 shots at 640x360 fit in one editor-script call - far cheaper than an unnecessary lighting pass and rebake.

Related: [pixel-sweep-lighting-measurement-traps](pixel-sweep-lighting-measurement-traps.md)

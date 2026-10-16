---
title: On a "this used to look right" bug, git-diff materials before investigating the scene
topic: agent-workflow-verification
tags: [regression, git, material, checkpoint commit, diagnosis]
summary: Materials are high-churn and low-visibility; one .mat tweak surfaces as a bug in an unrelated-looking subsystem, so diff materials first, then shaders, then the scene.
---
**Symptom:** Two bug reports — "terrain reads blurry at distance" and "no reflection on the glass" — that both point away from the cause. Hours go into terrain LOD, basemap distance, fog, impostor mips and a probe rebake.

**Cause:** One commit changed four floats in the glass material. The ground was only ever seen *through* that glass. A material sits between the thing you changed and the thing the player names.

**Fix / rule:** on any regression report, run `git log -p -- <suspect>.mat` (or `git diff <checkpoint> -- '*.mat'`) against the last checkpoint commit before touching scene, shaders or lighting. Order: materials → shaders → scene.
- Frequent local checkpoint commits make `git show <commit> -- <file>` a reliable before-image, and `git show <commit>:<path>` can recover a pre-regression **binary** asset (an `.exr` cubemap, a texture) to render a genuine before/after.

**Verify:** confirm the culprit by restoring the old values and rendering a before/after — not by reasoning about the numbers.

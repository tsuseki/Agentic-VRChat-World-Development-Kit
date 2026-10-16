---
title: Numeric checks are often blind to the visual defect they claim to verify
topic: agent-workflow-verification
tags: [verification, metrics, render, screenshot, linear vs gamma, false confidence]
summary: A number used to sign off a visual fix is frequently structurally unable to detect that defect; numbers locate problems, only a rendered before/after proves a fix.
---
**Symptom:** A fix is signed off on a green metric and a reviewer who renders an image finds the defect still there.

**Collected failures:**
- "% of verts below ground" is not a float detector: it passed hovering pieces and a piece 68 % buried that arched, ends dug in, middle 0.3-0.5 m above ground. Use a ground-skimming horizontal camera shot (~0.2 m high).
- Raycasts miss sub-pixel geometry (a thin bright splinter); project every triangle to screen space instead. For slivers use a thickness test: min altitude = `2*area / longest edge`, drop under ~1.5 mm.
- A metric going green is not "fixed": `importNormals = Calculate` drove bad winding 13.7 % to 0 % with zero visual change (the real defect was UVs).
- Albedo multiplies cannot beat low-frequency or silhouette defects (branding glyphs larger than a blur radius, a lattice whose holes show bright ground).
- Ratios measured off a screenshot are not comparable to material values in a Linear project: the backbuffer is display-encoded, compressing ratios by about the 1/2.2 power (linear R/G 6.24 can never read above ~2.30 on screen). Compare encoded to encoded, or convert first.
- A near-black decal cannot win a hue fight with a 40x brighter neighbour: a 4 % alpha leak dominated the pixel. Fix the leak (true 255 alpha) and raise the level; do not crush.
- "% of pixels below a threshold" is blind to a mid-tone band: a 2:1 dark stripe measured 0.00 % below 0.03. Read a scanline profile across the feature against its local surround.
- Hand-picked pixel windows silently measure the wrong object; attribute pixels properly (see [toggle-diff-and-mask-pass-attribute-pixels](toggle-diff-and-mask-pass-attribute-pixels.md)).
- Verifying in the authoring tool proves nothing about Unity: re-importing an FBX into Blender round-trips the same axis convention. Verify in Unity against world axes.
- The inverse: an index-only mesh trim leaves orphan vertices, so `RecalculateBounds()` still reports a removed 1.24 m spike. Compact vertices or measure from triangles.

**Fix / rule:** For any visual fix, the proof is a rendered before/after from the same camera. Numbers locate a defect; they never declare it fixed. Tell subagents this explicitly, name the failing camera bearing in the task, and have a separate agent review, since builders reliably pass their own work.

**Pitfalls:** When placing a verification camera, raycast to ground for height and `Physics.Linecast` eye-to-target, rejecting bearings that hit something; offsetting from a bounds centre on a slope puts cameras inside rocks.

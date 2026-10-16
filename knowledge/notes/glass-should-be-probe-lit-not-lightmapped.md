---
title: Never lightmap glass panes — set receiveGI to LightProbes
topic: lighting-baking
tags: [glass, receiveGI, light probes, lightmap atlas, UV2, gutter, generateSecondaryUV]
summary: Thin transparent panes are the worst lightmap clients — huge atlas demand and structural gutter bleed — so sweep them to receiveGI = LightProbes before baking.
---
**Symptom:** After a scene-wide UV2 gutter repack, ~120 objects still fail; a lightmap atlas is starved. Grouping the offenders: every scene-embedded one was 0.02–0.03 m glass (curtain wall, rails, shower screens, partitions). One 60 m rail panel alone claimed ~1000 texels across its UV extent on a 2048 atlas.

**Cause:** Near-zero thickness puts edge charts a hair from face charts — structurally prone to gutter bleed — and the bleed lands as smudges on the surface players look *through*.

**Fix / rule:** before any bake, sweep every renderer whose material name contains glass/window/glazing and set `receiveGI = ReceiveGI.LightProbes`. Switching 129 renderers removed ~32,000 m² of atlas demand. This only chooses lightmap-vs-probe reception; it does **not** touch `ContributeGI`, so the pane's occlusion/shadowing in the bake is unchanged. Do it as a class sweep, not per complaint.

**Pitfalls:** don't "fix" an imported FBX's UV2 by setting `ModelImporter.generateSecondaryUV = true` with `secondaryUVMarginMethod = Calculate` (not `Calculated`) at a low `secondaryUVMinLightmapResolution` (16 texels/unit) — it sized gutters so large the islands collapsed into a corner (measured texel extent 25 → 7939). For small props, probe-light them instead.

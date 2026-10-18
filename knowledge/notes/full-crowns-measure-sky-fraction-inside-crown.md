---
title: Leaf-card trees read 'too branchy, not full' when sky shows through the whole crown; measure the sky fraction
topic: blender-modeling
tags: [trees, foliage, leaf cards, crown fullness, sky fraction, crown_fullness.py, review]
summary: Sparse-spray card crowns let 27–50 % sky through the crown silhouette at eye level and get rejected as branchy; bigger cards with smaller-leaved open sprays (never dense clump sprays) plus volume crowns for opaque species bring dense species to ≤ 0.15 and open ones to ≤ 0.30, measured with a fixed eye-level sky-fraction metric.
---
**Symptom:** A low-poly leaf-card tree pack was sent back as "too branchy, not full", with reference photos of dense cypress avenues. Measured at eye level, sky showed through the whole crown: olives 0.34–0.50 sky fraction inside the crown silhouette, holm oak 0.27.

**Cause:** Sparse sprays (few leaves per atlas cell, lots of key background) on a branch skeleton: each card covers little, so the crown reads as a lattice of limbs with leaves on them instead of continuous foliage masses.

**Fix / rule:** Bigger cards with smaller-leaved open branch sprays (see [bigger-cards-smaller-leaves-fill-crowns](bigger-cards-smaller-leaves-fill-crowns.md); dense clump sprays were rejected as stacked textures even though they measured fuller), plus volume crowns for opaque species (see [opaque-crowns-need-no-inner-wood](opaque-crowns-need-no-inner-wood.md)); open species keep their limbs. Measured: cypress 0.03–0.07, carob 0.04–0.07, myrtle 0.08–0.10, fig 0.11–0.13, holm oak 0.12–0.15, olives 0.20–0.28 (olives with ×1.6 cards and leaves ~1/16 of the spray height). The metric is a guide, not the verdict: a lower sky fraction from dense sprays still failed by eye.

Targets: dense species (cypress, carob, bay, holm oak, juniper, shrubs) ≤ 0.15; cedar ≤ 0.20; open species (olive, pines, fig, palms) ≤ 0.30.

**Verify:** `.omp/skills/lowpoly-tree-generation/scripts/crown_fullness.py` on the shipped (culled) mesh. Definition, keep it fixed so numbers compare across runs:
- perspective camera at 1.6 m eye height, 2× crown width from the trunk, 4 azimuths;
- alpha cutout 0.45 on the leaves, bark opaque;
- silhouette = covered pixels closed by 0.6 m (in world units) with holes filled, only above the lowest leaf;
- sky = 1 − covered / silhouette. Report mean and max over the azimuths, then look at the mask PNG.

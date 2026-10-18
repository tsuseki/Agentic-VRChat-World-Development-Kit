---
title: Leaf-card cull rarely passes on dense volume crowns; budget an unculled card count
topic: geometry-meshes-uvs
tags: [trees, leaf cards, cull, silhouette, triangle budget, volume crown]
summary: Removing even 5 % of cards from a dense spindle/ellipsoid crown moved the silhouette 2–22 cm against a 0.3 cm allowance, so plan the unculled card count inside the budget; branch-structured crowns still pass at 10–20 %.
---
**Symptom:** A silhouette-gated cull of hidden leaf cards (remove the cards that contribute least, then compare the silhouette with the unculled tree) failed on every dense volume crown, even at frac 0.05: the outline moved 2–22 cm against a 0.3 cm allowance. Several fracs were tried per tree, each a full headless build.

**Cause:** On a volume crown nearly every card sits on the outer shell and touches the silhouette; there is no inner, fully hidden layer to remove. Branch-structured crowns do have inner cards behind outer ones.

**Fix / rule:** On dense volume crowns, choose the card count so the unculled tree is already inside the triangle budget; don't plan on the cull. Branch-structured crowns still pass at 0.10–0.20. Test at most ~3 cull fracs per tree (each try is a full build).

**Verify:** the cull's own silhouette report (max outline shift vs allowance) and the final tri count from the build STAT lines.

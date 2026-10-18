---
title: Opaque column and dome crowns need no inner trunk or limbs
topic: blender-modeling
tags: [trees, cypress, leaf cards, volume crown, spindle, ellipsoid, bark tris, budget]
summary: For species whose crown hides all wood, build only a short visible trunk with root flare and fill a spindle/ellipsoid volume with cards (84 bark tris, 0.03 sky); open species keep their visible limbs because those identify the species.
---
**Symptom:** A column species built with a full branch skeleton spent most of its bark budget on limbs nobody can see once the crown is dense, and the crown still showed gaps between the limb-borne sprays.

**Cause:** In an opaque crown the inner wood is fully occluded; it costs tris and constrains where cards can go (cards follow limbs, so they cluster and leave holes).

**Fix / rule:** For opaque species (columns, domes) build a short visible trunk + root flare (+ first forks for domes) and place the leaf cards on a volume: a spindle for columns, an ellipsoid with lumps/parts for domes. No inner trunk or limbs. A cypress built this way used 84 bark tris (1.4–3.4k total) and reached 0.03 sky fraction. Spend the saved tris on cards.

Open species (olive, fig, pines, cedar tiers) keep their visible limbs: the limbs are what identifies the species; fill them with denser sprays and more outer cards instead.

**Verify:** sky fraction with the eye-level crown metric ([full-crowns-measure-sky-fraction-inside-crown](full-crowns-measure-sky-fraction-inside-crown.md)) and a render from eye height: no floating card clumps, trunk enters the crown cleanly. Branch-based checks (uncovered tips, card attach) don't apply in volume modes.

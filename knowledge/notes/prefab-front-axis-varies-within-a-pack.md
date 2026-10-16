---
title: A furniture pack does not share one front axis
topic: import-fbx-prefabs
tags: [prefabs, orientation, front-axis, furniture, scripted-placement, contact-sheet]
summary: Which local axis a prefab front faces varies per prefab even inside one asset pack, so a solver that aims a fixed local axis at the room shows some pieces back-to-front as plain slabs.
---
**Symptom:** A dresser renders as a featureless flat brown box. Flipped 180 degrees it shows six drawers with pulls. Bounds, clearance, clash count and flushness are identical either way, so no metric sees it.

**Cause:** Every piece in the pack measured depth-along-X at identity, so a solver aiming local +X at the room looked right - correct for a sideboard, wrong for the dresser, whose front is local -X.

**Fix / rule:**
- Don't assume a pack shares a forward axis. Settle it for the whole pack cheaply: instantiate every candidate in one scratch row at identity rotation at an empty world location, one directional light ~0.55 intensity, and shoot the row from +X. Anything showing a flat panel has its front on -X. Two renders cover a dozen prefabs (per-prefab 0/180 A/B costs 2N).
- The same contact sheet answers style - and check what the scene already standardised on before picking from a pack.
- Signature of the bug: a plain slab where detail should be.

Related: [contact-sheet-prefabs-before-placing](pick-pack-prefabs-from-a-contact-sheet.md)

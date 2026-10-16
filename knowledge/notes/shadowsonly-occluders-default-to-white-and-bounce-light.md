---
title: ShadowsOnly occluder boxes default to a white material and still bounce light in the bake
topic: lighting-baking
tags: [ShadowsOnly, occluder, Default-Material, GI, Bakery]
summary: Hidden ShadowsOnly boxes never show in screenshots but sit in the traced scene with ContributeGI; give them a dark grey material.
---
**Symptom:** the rooms wrapped by invisible shadow-occluder boxes bake hot; nothing visible explains it.

**Cause:** boxes created from primitives keep `Default-Material` (pure white). They never render, so no screenshot shows them, but they are traced with ContributeGI = true and act as bounce amplifiers (6540 m² of them in one scene).

**Fix / rule:** assign a dark occluder material (~0.25 grey) to every ShadowsOnly renderer. Zero visual cost. Check for these whenever a sealed room bakes hot.

**Pitfalls:** coplanar ShadowsOnly floor slabs under a visible floor did not bake it black in a measured case — don't rip out occluders on suspicion; sample the lightmap first (see [sample-the-lightmap-to-tell-baked-black-from-dark-albedo](sample-the-lightmap-to-tell-baked-black-from-dark-albedo.md)).

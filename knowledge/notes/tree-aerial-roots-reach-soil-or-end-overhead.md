---
title: Aerial and prop roots must reach the soil with a deep shaft or end at least 2.2 m up
topic: blender-modeling
tags: [trees, banyan, prop roots, pillar roots, aerial roots, slope, burial, floating tips]
summary: In-world cameras on slopes stand below the tree base, so a pillar root's buried end cone shows as a spike over the grass; give pillars a full-girth shaft about 2.5 m below the ground ring, and let every hanging root either reach the ground or end at least 2.2 m up (nothing in 0.1–2.2 m), a floor that must still hold after the clash-avoid slide.
---
**Symptom:**
- Pillar roots read as a bundle of spikes over the grass from in-world cameras on a slope (one stood 1.4 m below the tree base). Shallowest burial measured 0.06 m; 16–17 pillars per tree were too shallow.
- Hanging aerial roots ended 1.26 m and more above the ground (4 / 8 / 8 per tree): roots stopping in mid-air.
- Underside shoots of drooping scaffold limbs (`up_end` −0.25) hung down to 0.53–0.79 m and read as roots in the air.

**Cause:**
- A pillar built only to the ground ring plus its end cone is exposed wherever the terrain falls away.
- The clash-avoid slide and the late re-seat moved hanging curtains back down after the length was drawn.
- Drooping limb ends point their side shoots at the ground.

**Fix / rule:**
- Pillars: `props` entry `deep=<m>`, a straight full-girth shaft that far below the flared ground ring (2.5 m; the pack scale keeps underground depths, so it ships at full depth).
- Hanging roots: either reach the soil as a pillar or end ≥ 2.2 m up (shipped metres). `hard=True` keeps the floor after the avoid slide and re-seat.
- Drooping scaffolds: level the shoots with level key `flat` 0.5.

**Verify:** `bark_clash.py` `ground_contact(bm, k)` (runner `--tips`): 0 FLOAT tips (0.1–2.2 m shipped), 0 SHALLOW pillars (< 1.4 m full-girth burial). After the fix: tip_min 2.32 m, bury_min 2.56 m. Also render the real slope cameras with a terrain plane through the ground at the tree base and at the camera.

**Related:** for far LODs set the lods level key `props` so pillars stay meshed; without it the far levels dropped every pillar (hole p95 2 m).

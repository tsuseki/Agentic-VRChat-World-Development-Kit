---
title: Bare limb ends below the leaf zone read as dead spikes at eye height
topic: blender-modeling
tags: [trees, limbs, leaf cards, low_tips, tips_uncovered, eye height, review]
summary: Limbs ending below the card zone look like dead spikes at eye height and an uncovered-tips check misses them; give chains with < 3 cards 7 cards over their outer 2 m and drop ground limbs below 0.8 m (opt-in, byte-identical builds when off).
---
**Symptom:** A review of open-crowned trees (olives) flagged bare, dead-looking spikes around the lower crown, at exactly the height players look. The builder's uncovered-tips check reported 0.

**Cause:** The check only tests limb tips inside the leaf-card zone; low limbs that end below it were never expected to carry cards, so their bare ends pass.

**Fix / rule:** An opt-in pass (`low_tips` in the tree builder): every terminal limb chain carrying fewer than 3 cards gets 7 cards over its outer 2 m (one at the tip), kept above the ground; chains lying entirely below 0.8 m with nothing rooted on them (ground limbs) are not meshed. Added cards use their own random sequence after all others, so the skeleton and existing cards stay put; off = byte-identical builds.

**Verify:** pre-fix leaf vertices ⊆ post-fix leaf vertices; eye-height render all around the tree shows no bare ends; byte-compare a build with the option off against the previous output.

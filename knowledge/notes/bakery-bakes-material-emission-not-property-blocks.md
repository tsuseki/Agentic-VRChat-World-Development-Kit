---
title: Bakery bakes the shared material emission and ignores MaterialPropertyBlocks
topic: lighting-baking
tags: [bakery, emission, materialpropertyblock, lighting-states, night-bake, restore]
summary: MaterialPropertyBlock overrides never reach the material asset, so they have zero effect on a Bakery bake; baking a "fixtures off" variant means editing the material assets and restoring them afterwards.
---
**Symptom:** A night / lights-off lighting state kills fixture emission with `MaterialPropertyBlock`s. It looks perfect at runtime, but the bake always contains the lights-on look. The bake succeeds silently.

**Cause:** Bakery gathers emissive surfaces from the **shared material asset** at export time (`uvemissive_LMGroup_<group>.lz4` appears in the export). A property block is a per-renderer runtime override that never touches the asset.

**Fix / rule:**
- To bake an alternate lighting state, zero emission on the material **assets** (and adjust Bakery light intensities), bake, then restore.
- Snapshot every material and light you will change to JSON on disk **before** touching them, and restore from that file, not from memory.
- Restoring emission means restoring **three** things: `_EmissionColor`, the `_EMISSION` shader keyword, and `globalIlluminationFlags = BakedEmissive`. Zeroing usually flips the flags to `EmissiveIsBlack` and can disable the keyword; a material that gets the colour back without the keyword renders **pure black** and is excluded from the next bake.

**Verify:** After restore, re-read the keyword and GI flags on every material, not just the colour.

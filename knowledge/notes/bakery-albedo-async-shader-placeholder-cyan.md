---
title: Async shader compilation bakes the cyan placeholder into Bakery albedo
topic: lighting-baking
tags: [bakery, albedo, async shader compilation, ShaderUtil, cyan, bake verification]
summary: With editor async shader compilation on, Bakery's albedo pass can render not-yet-compiled materials with Unity's cyan placeholder (or black), tinting whole lightmap groups cyan or killing their bounce; bake with ShaderUtil.allowAsyncCompilation off (or shaders warmed) and check the uvalbedo atlases before accepting.
---

**Symptom.** After a routine re-bake, every prop in one lightmap group looked cyan in both beauty and lightmap-only
renders: median lightmap RGB went from 0.64/0.55/0.42 to 0.47/0.75/0.63. A second group was about 40 % darker, having
lost its bounce. Other groups (trees, terrain, volumes) were clean. The Light Volumes and reflection probes baked from
the same GI were wrong too.

**Cause.** Bakery renders each group's albedo atlas (`%TEMP%/frender/uvalbedo_<group>.lz4`) through the editor.
With async shader compilation on, materials whose shader variant wasn't compiled yet render with Unity's cyan
placeholder: in the bad group 77 % of texels were pure (0,255,255). One group came out all zero. The setting had been
off in earlier bakes and was switched back on by an unrelated timing script that restores the editor preference
(`ShaderUtil.allowAsyncCompilation = true`).

**Fix / rule.**
- Before every bake, set `ShaderUtil.allowAsyncCompilation = false`, or warm the scene's shaders so no variant is
  pending. Restore the setting after the bake.
- Any script that toggles this flag restores the value it found, not the editor preference.

**Verify.** After the bake, before running the post-bake chain:
- Decode each `uvalbedo_*.lz4` atlas.
- Fail the bake if any group has a noticeable share of exactly (0,255,255) texels, or is all zero.
- Compare each group's lightmap median colour with the previous bake; a sudden blue/green shift points here.

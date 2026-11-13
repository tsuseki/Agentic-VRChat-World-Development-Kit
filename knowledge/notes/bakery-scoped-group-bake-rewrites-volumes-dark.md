---
title: A scoped Bakery group bake re-renders every volume without the rest of the scene
topic: lighting-baking
tags: [bakery, render selected groups, bakery volumes, light volumes, partial bake]
summary: Bakery's "Render Selected Groups" re-renders all Bakery volumes from only the selected groups' geometry, leaving them far too dark; restore the volume assets from the last full bake (md5-verified) after any scoped bake.
---

**Symptom.** After two scoped lightmap bakes (only the two prop groups selected), every Light-Volume-lit prop
and every Light-Volume-aware avatar rendered dark grey to near-black in full sun inside the volumes. Outside all
volumes the same test sphere matched a Standard probe-lit sphere. The volumes' base level had dropped to a median of
15 % of the previous full bake (1.5–30 %; one volume 1.20 → 0.032). The lightmaps themselves were correct.

**Cause.** "Render Selected Groups" rewrites all Bakery volume textures (87 here, for 29 volumes), but computes them
from the selected groups only. Terrain, trees and the rest of the scene are absent, so the bounce and sky occlusion
are wrong. The Light Volume atlas built from them inherits the error. Lightmap checks (bindings, timestamps, per-texel
compare of the baked groups) all pass, so nothing flags it.

**Fix / rule.**
- After any scoped group bake, restore every Bakery volume asset and the Light Volume atlas from the last full bake
  (`git checkout <full-bake-commit> -- <volume paths>`).
- md5-verify the restored files against that commit.
- Volume bound changes need a full-scene bake.

**Verify.** Compare each volume's level with the full bake (parse the asset, or sample its texture centre). In play
mode, put an LV-shader sphere inside a volume in sun next to a Standard probe-lit sphere outside all volumes; they
must read alike.

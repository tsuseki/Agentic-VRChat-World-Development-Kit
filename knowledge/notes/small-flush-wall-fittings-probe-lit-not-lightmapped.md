---
title: Small flush wall fittings blotch when lightmapped; make them probe-lit
topic: lighting-baking
tags: [light switches, wall plates, texel density, probe-lit, lightmap repaint, linear color space]
summary: A 9 x 14 cm switch plate gets 3-4 lightmap texels and bakes a half-black smear, so wall plates, outlets and vents are probe-lit; moving one exposes its baked contact shadow, and the probe-lit plate needs a gamma-encoded tint to match the wall.
---

**Symptom:** a player at spawn saw "a weird blotch on the wall that looks like it's supposed to be a light switch". Close up the plate was blank, its left half lit and its right half near black.

**Cause:** the plate was a lightmapped static. At the atlas's density its whole chart was about 4 x 3 texels (Bakery scale-offset 0.013 x 0.006 on a 2048 map), so one or two texels carried the wall-contact shadow and bilinear filtering smeared it over half the plate. A class sweep then found the same plates buried up to 3.5 cm inside wall cladding (invisible) or floating up to 15 mm off the wall.

**Fix / rule:**
- Fittings under about 20 cm (switches, outlets, vents, small brackets) are **probe-lit statics**: ContributeGI off, receive GI from light probes, Bakery storage rows removed (else Bakery re-applies the old index at load). Take them out of any merged mesh that baked their UV2 in.
- Seat each plate on the **visual** wall face, 0.5 mm proud, measured by raycasts against temporary MeshCollider copies of the nearby renderers (exclude the other plates: back-to-back pairs hit each other). Keep at least 6 cm to door casings and jambs.
- Probe-lit plates came out 0.6-2.7x the light of the wall beside them (probes sample the open room; the wall's texels include its own occlusion). Measure probe SH along the plate normal against the wall lightmap a few cm either side and tint the plate material by about 1 / ratio, never below the wall.

**Pitfalls:**
1. **Moving or deleting a flush plate exposes its baked contact shadow**: a near-black rectangle stays on the wall where it was. Without a bake, repaint the footprint texels in the lightmap file with the lerp of the wall texels just above and below it (map world points to texels by raycasting the wall with a temporary MeshCollider and `textureCoord2` x the renderer's lightmapScaleOffset; HDR rows are stored top-down, so y = (1 - v) x height), then reimport. Diff against the original: only the footprint texels may change.
2. **`_Color` is an sRGB colour in a linear-space project.** Writing a linear tint of 0.42 gives 0.147 in the shader and grey, dirty plates. Store `Mathf.LinearToGammaSpace(tint)` (0.42 -> 0.68).
3. Raycasts against MeshColliders miss back faces: from inside a cladding panel a ray never finds its outer face, so cast from the room side toward the wall.

**Verify:** same-camera before/after at spawn eye height plus a 5 degree telephoto on the plate; the old footprint must show no mark, and plate-to-wall rendered brightness should sit near the albedo ratio (a white plate on a cream wall: about 2-3x).

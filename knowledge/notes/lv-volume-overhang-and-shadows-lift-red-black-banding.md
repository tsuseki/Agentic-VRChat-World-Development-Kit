---
title: A higher-weight Light Volume overhanging the next room plus a Shadows lift turns that room red and black
topic: probes-reflection-and-light
tags: [VRC Light Volumes, weight, bounds, Shadows, atlas, CorrectVector, island bitmask]
summary: Crop every Light Volume to its own room's walls and keep its Shadows lift at 0 (bake brightening into the data or use Exposure); a weight-2 bath volume reaching 1.4 m into a bedroom with Shadows 0.7 rendered the bed head saturated red and black.
---
**Symptom:** in play mode a bedroom read dark, blotchy and stepped near the bed head, pillows and bedside lamps;
LV test spheres there showed saturated red-on-black banding, spheres a metre further in were neutral. A second
bathroom in the same world had the same artefact on its towels. Edit mode looked fine (volumes are off there).

**Cause:** two settings stacked.
1. **Bounds overhang:** the bathroom volume (weight 2) extended 1.4 m through the partition into the bedroom; the
   bedroom volume (weight 1) lost that strip, so it was lit by bathroom-side data sampled through a wall.
2. **`Shadows` lift (0.7 and 0.45, added earlier to brighten towels):** at atlas time LV's
   `Texture3DAtlasGenerator.CorrectVector` rescales the L0 vector and each L1 r/g/b vector *separately*, giving
   near-zero vectors a magnitude ≥ ~0.26 in noise directions. L1 then exceeds L0, so lit hemispheres saturate
   red and unlit ones go black. Dark voxels (behind walls, in the overhang) are exactly the ones it breaks.
The baked textures were identical to the previous bake (mean Δ 5e-4): not a bake regression.

**Fix / rule:**
- Crop each volume to its room: compare every volume AABB with the room walls and fix any higher-weight volume
  that crosses into a neighbour (keep voxel pitch; crop whole slices and update position, scale and Resolution so
  the remaining voxels stay where they were; regenerate the atlas). No re-bake needed.
- Keep `Shadows` at 0. To brighten a dim room, raise the volume's Exposure, or apply the lift to the data with one
  rescale per voxel (L0 by `(mag+S/2)/(1+S/2)`, the three L1 vectors by the same per-channel factor, dark voxels
  blended toward the volume's mean colour), then set `Shadows` 0. A future Bakery render overwrites the patched
  textures: re-bake with the corrected bounds.
- When islands get their own Bakery light bitmask bits, add those bits to the `Light Volume Manager`
  `VolumeBitmask` and `ProbeBitmask` too (e.g. 1 → 1|16|32). Only lights whose mask matches bake into volumes and
  probes, so otherwise the next full bake builds the island's volumes without its own lights.

**Verify:** in play mode, place a grid of LV-PBR spheres around each room (corners, centre, by windows, lamps and
the bed, at floor and 1.0–1.3 m) and capture the same poses before and after; the red/black spheres must turn
neutral. Positive control: the overhang strip and the Shadows value reproduce the banding when restored.

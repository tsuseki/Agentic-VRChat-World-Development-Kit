---
title: Flat-based platforms on sloping ground need a plinth skirt
topic: placement-layout-design
tags: [terrain, slope, platform, plinth, floating, contact]
summary: A flat-based platform, slab or pad on sloping ground floats on its downhill side; add a plinth skirt (top 3 mm under the base, inset 2 cm, buried 6 cm below the lowest ground sample) on a shared unit-cube mesh with no collider, and verify each plinth's bottom-vertex gap is negative.
---

**Symptom.** Cabana platforms floated 0.18–0.30 m on their downhill side, dining slabs up to 0.20 m, and pads and parasol bases 4–9 cm. A sweep against the walk collider had passed them.

**Cause.** The pieces are modelled with a flat base at z 0 and seated at one point; on a slope the rest of the base hangs in air. Measuring against the walk collider instead of the visible terrain mesh can also hide the gap.

**Fix / rule.**
- For every piece whose base floats more than 2 cm: take its base rectangle (vertices within 1 cm of local y 0), inset 2 cm per side, and sample the ground on a 7×7 grid.
- Add a box under it: top 3 mm below the base, bottom 6 cm below the lowest ground sample, in a material matching the base (stone, render). Use one shared unit-cube mesh scaled per plinth, no collider. The piece itself is not moved, so its colliders stay.
- Modellers can instead model a footing skirt reaching ~0.35 m below z 0, or flag "needs plinth" in the handoff.

**Verify.** Every plinth's bottom-vertex gap to the visible terrain is negative (buried) and its top is not coplanar with the base; the re-review found the 18 plinths clean.

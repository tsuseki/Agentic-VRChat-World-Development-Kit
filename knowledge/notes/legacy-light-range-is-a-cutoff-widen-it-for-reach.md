---
title: With non-realistic falloff, light range is a hard cutoff — widen range to reach the floor
topic: lighting-baking
tags: [point light, range, falloff, chandelier, Bakery, realisticFalloff]
summary: High fixtures light the ceiling 9× more than the floor; widening range (20→50) lifts unreached zones without blowing the hotspots, unlike raising intensity.
---
**Symptom:** a tall hall's floor mean L = 0.092 vs ceiling 0.304; chandeliers light the ceiling, not the room. Raising intensity blows the ceiling before the floor reads.

**Cause:** fixtures at y 6 under an 8 m ceiling: inverse-square gives the ceiling (6/2)² = 9× the floor. Lights on a 22 × 26 m grid at range 20 meant most of the hall was reached by only 2–3 lights. Legacy (non-realistic) falloff truncates hard at `range`; a light 10 m above a floor with range 14 delivers very little.

**Fix / rule:** widen range (20 → 50, or 14 → 20 with intensity trimmed). It lifts dim zones and barely moves hotspots where the nearest light already dominates. The physically ideal fix is lowering fixtures, if the look allows.

**Pitfalls:**
- Bakery bakes its own light component's values, not `Light.intensity`; check `Light.intensity == BakeryPointLight.intensity` before suspecting a broken rig.
- Cloned Bakery light components keep the **template's** values — sync via `SerializedObject` after cloning. Cloned fixtures may carry no light at all if the original's light was reparented rather than a child.

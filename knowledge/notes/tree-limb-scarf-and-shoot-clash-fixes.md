---
title: Limb "scarf" bands and shoot-through-limb-tip clashes come from the wave and the merge taper, not the angles
topic: blender-modeling
tags: [trees, skeleton, merge, wave, taper, bark clash, whorl, bare_limbs]
summary: Limbs that leave a trunk top and run across it as a level band are pitched level by the limb wave's first step, so fade the wave in (`lead`) before touching the angle; a shoot clipping out through its own limb tip is thicker than the tip after the merge blend and end taper, so cap children at 0.8× the host radius (`kid_cap`).
---
**Symptom:**
- Limbs leaving a broad trunk top ran across it as a level band ("scarf").
- A limb and its own child shoot clashed near the limb tip: 5–6 cm shoots poked 1–3 cm out through 4 cm limb tips.

**Cause:**
- Scarf: the limb `wave` pitched the first step level, so a steeper `ang` alone changed nothing. A `root_out` large enough that tilted base rings stood out of the trunk top got put back on the axis by `base_fix`, level again (0.35 worked, 0.55 did not). Lowering the whorl to 0.93 of the stem gave a 16.5 cm clash.
- Shoot clash: the merge radius blend and the end taper thin the host's tip after the child's radius was drawn from the unthinned host.

**Fix / rule:**
- Fade the wave in over the start of each limb: level `wave=dict(…, lead=0.34)`. Check the wave before the angle; dump the limb skeleton (first-step pitch) when a band shows.
- `kid_cap=dict(k=0.8, depth=2)`: after merge, sag, smooth and taper, a child thicker than k × its host there is scaled down its whole length (hosts first). Avoid `clear` 0.15 did not fix it; limiting shoots to `at` ≤ 0.94 made it worse (3 → 4 clashes). With the cap: 4 → 0 clashes.

**Verify:** `bark_clash.py` `scan` → 0 clashes and 0 pokes on the packed mesh; side and top renders of the trunk top.

**Pitfalls:**
- When `bare_limbs.py` flags pillars under the canopy, count the cards above the flagged point (`cards_above.py`) before adding cards. Raising `fill` to 0.65, adding `fill_under` 0.2 and moving the pillars changed nothing: 11 leaf faces already lay within 0.6 m above. The checker did not accept a stem's merged limb part as a pillar host; fixing the host rule gave PASS.

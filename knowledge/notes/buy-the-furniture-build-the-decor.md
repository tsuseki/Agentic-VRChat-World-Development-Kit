---
title: When an asset pack lacks a category, build that category instead of reusing wrong props
topic: assets-sourcing
tags: [asset pack, decor, procedural, lathe, books, dressing]
summary: Repeatedly substituting the nearest wrong prop for a category a pack lacks shows up as many unrelated-looking review findings; build that category procedurally.
---
**Symptom:** A room review returns many separate findings: "duplicate decor", "not a candle", "books contribute nothing", "reads close to empty". Each looks like a placement mistake. In one review two thirds of 36 findings had this single cause.

**Cause:** The furniture pack has good furniture but **no small decor** in the right style, so the same vase stands in as a vase, a candle and an ornament, appears three times in one room, and the pack's books lie face-down and read as blank card at viewing distance.

**Fix / rule:** Buy the furniture, build the decor.
- A lathed surface of revolution is ~20 lines of code and gives an unlimited family of ceramics from one profile array (ovoid, cylinder, bowl, lidded jar, column).
- An upright book run is a loop of cubes with randomised width, height and depth, the last volume leaning at about 11 degrees.

Both cost a few hundred triangles, read as real objects at viewing distance, and can be tinted per room so rooms do not look like twins.

**Verify / signal:** The same prefab name appears three or more times in one room, or a reviewer keeps describing props as "reads as nothing", "blank" or "a slab". Inventory the pack by category before dressing; when a category comes back empty, build it.

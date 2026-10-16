---
title: A lamp whose emissive faces point into an opaque dish reads switched off — swap the prop
topic: materials-textures-shaders
tags: [lamp, emission, emission map, prop selection, eye height]
summary: If a fixture's emissive texels sit on faces hidden inside a shade or dish, it looks black over a bright pool from every reachable viewpoint; check the emission map first, then swap to a prop proven lit rather than tuning.
---
**Symptom:** The light works, but the fixture looks dead: a black lamp with a strong warm pool pouring out from under it — reads as "unlit prop next to a mystery light".

**Cause:** Either (a) the emission map is genuinely dark (switched-off by design), or (b) the emissive faces face down into an opaque dish / closed shade and are never visible.

**Fix / rule:**
- **Check the atlas before tuning:** sample the emission texture's mean and lit-pixel fraction. A switched-off-by-design fixture measured mean 7.7/255, 3.04% lit pixels, vs 101.6/255 and 47.84% for its lit sibling — no material tweak fixes that; swap the prop.
- If the map is clearly lit and the prop still reads black, the emitters are enclosed or facing away. Raising `_EmissionColor` only brightens the pool.
- **Swap to a prop already proven lit in that room.** Both cases cost several bakes when treated as brightness problems.

**Verify:** render from standing eye height, never from the Inspector or top-down — a downward-facing emitter looks perfect from above and dead from where players stand.

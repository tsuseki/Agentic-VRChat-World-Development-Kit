---
title: ShadowsOnly sun-leak occluders must sit behind the visible wall, never inside the room
topic: lighting-baking
tags: [bakery, occluder, shadows-only, light-leak, single-sided-shell, black-walls]
summary: Reusing blockout boxes as ShadowsOnly occluders bakes walls solid black when the box sits on the room side of the visible face, and shared interior walls cannot carry an occluder at all.
---
**Symptom:** After enabling blockout boxes as ShadowsOnly casters to stop sun leaks through single-sided environment shells, Bakery bakes entire wall faces solid black, in rectangles matching the boxes. On stairs: weird shadows because an occluder slab contained 176 of 180 tread triangles; lights inside occluders leave a room mysteriously dark.

**Cause:** Blockout boxes straddle or sit in front of the visible shell face (e.g. box spans X 22.40-22.82 while the wall face is at 22.86), putting a shadow caster between the lights and the wall. In compact floorplans one room's wall *is* the neighbour's wall, so pushing the box out just moves the black face next door (19 of 26 offset boxes still intruded).

**Fix / rule:**
- Only **exterior** surfaces with no room on the far side may carry an occluder. Classify by sampling ~9 points 0.35 m beyond the outward face; if >= 50% fall inside another room's shell bounds, it's a shared wall -> no occluder. In one case 6 of 30 occluders were enough and zero leaks returned. Don't over-apply.
- Containment check per occluder: thinnest bounds axis = wall normal; `innerFace = center - sign*(thickness/2)`; if innerFace is on the room side of the shell face, it will bake black.
- Automated clearing sweep: take the shell mesh's world triangle centroids and areas; for each enabled ShadowsOnly box, OBB-test centroids (`InverseTransformPoint` vs `sharedMesh.bounds.extents`) and sum the **buried area**. For boxes over ~1 m2, find the smallest of the 6 axis displacements that pushes every contained centroid out, apply it +3 cm, and **disable the box instead if the move exceeds 0.6 m** (shared-wall case). This took 497 m2 of stair surface from ~326 m2 buried to 0.6 m2.
- Report buried **area**, not triangle count - 2 triangles can be an 18 m2 wall quad.
- Run the same OBB test on light positions to find lights buried in occluders.
- Long-term: author thin purpose-built occluder planes just outside each exterior face instead of reusing blockout boxes.

Related: [zero-thickness-walls-leak-sun-use-shadow-only-occluders](zero-thickness-walls-leak-sun-use-shadow-only-occluders.md)

**Pitfalls:** Shared materials do not affect baked shadows (lightmaps are per renderer). Black from an occluder looks like a stale bake - check `lightmapIndex` first; if renderers are lightmapped, suspect geometry occlusion.

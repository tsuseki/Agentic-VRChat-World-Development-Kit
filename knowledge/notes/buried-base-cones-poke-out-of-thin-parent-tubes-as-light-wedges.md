---
title: A limb's buried base cone can poke out of a thin parent tube as a light triangular wedge on the far side
topic: geometry-meshes-uvs
tags: [trees, bark, tube mesh, base cone, fork, lobed trunk, low poly, checker]
summary: Closing each child tube with a cone buried 1.5 radii back leaves the parent's far side on thin lobed or 4/3-sided parents; the exposed cone faces read as light bark wedges, so test the cone and ring against the union of the other tubes and clamp the apex depth.
---
**Symptom:** Players saw light triangular bark wedges (several cm to a hand across) on a tree trunk, on the side opposite a thick limb. Each wedge was flat, lighter than the bark around it and textured in a different direction. A front render of the limb, the fork zone checks and a bark-through-bark check never showed it: the defect sits behind the limb.

**Cause:** A low-poly tube builder closes every child's base ring with a cone whose apex is buried `1.5 x child radius` back along the limb. Thick limbs (0.55-0.75 x the parent radius) on a parent whose cross-section is lobed or only 4 or 3 sided (inradius 0.71 / 0.5 x radius, trough 0.66 x radius with a 0.34 lobe) put the apex, and the ring corners on the far side of the child, outside the parent's surface by 3-65 mm. The cone faces carry the mean UV of their ring and face backwards, so they light differently from the bark. Measured on a 121-mesh tree pack: 82 meshes had at least one such cone, the worst 65 mm outside; they were invisible from the usual review angles.

**Fix / rule:**
- After meshing, test every child's base cone (apex, ring vertices, ring-to-apex edge samples at 0.5 and 0.8) against the **union of all the other tubes** (nearest-surface distance, inside by ray parity), not just the parent: a point hidden in a sibling or grandparent is fine, and a sibling-only test gives false positives at forks whose limbs have equal radii (exclude equal-radius siblings when picking the parent).
- Repair by moving only vertices: pull ring corners more than 2 mm outside toward the parent axis to 1 mm inside, then slide the apex toward the ring centre (shallower cone) until apex and edge samples are inside. Topology, UVs, vertex colours and loop order stay identical; custom normals must be re-set after the move (they are stored relative to the auto normals, which a vertex move shifts).
- Make it the builder default and print a stat only when it fires, so unaffected trees rebuild geometry-identical (a lightmap UV that is projected from the geometry changes for the ones that fire).
- Build the test surface from **explicit triangles in the mesh's own corner order**, and test the worse of both quad diagonals. Generic polygon-to-BVH helpers may split each quad along the other diagonal than the renderer draws; a cone point inside under one split can stand 30 mm outside under the other, and a first checker built that way reported 0 for meshes that still showed wedges.
- A child with no wider tube near its base (a node on a thin twig, a fork of equal radii, a limb on an unconnected trunk) has nowhere to hide the cone: do not skip it, close it flush (apex onto the ring plane). Repeat the repair until a pass moves nothing, because one cone's move can uncover another.
- The checker works on the packed mesh alone: tubes are the connected components that contain triangles, the two apexes (all faces triangles) end the ring chain, the apex with the wider first ring is the base. Ground stems (apex below ground) have no parent.

**Verify:** flag count 0 on every shipped mesh at a 3 mm tolerance; positive control: the same checker on the pre-fix meshes flagged 82 of 121, and on the first repair's output it must still flag the forks a reviewer rendered with the drawn diagonal (8 olive forks, 176 cones on 49 trees) before the second repair brings it to 0 and the red-highlighted cone faces were visible from outside; same-camera renders with the real material before/after (the wedge present before, gone after); UV0, UV2 and vertex colours compare equal between the old and the repaired export.

**Pitfalls:** a width-only metric (apex depth against parent radius) misses lobed and 4/3-sided parents; a hidden-from-front defect needs a camera that looks at the apex from outside the parent along (apex - parent axis point), checked for occlusion.

**Related:** [zero-defect-result-needs-positive-control](zero-defect-result-needs-positive-control.md).

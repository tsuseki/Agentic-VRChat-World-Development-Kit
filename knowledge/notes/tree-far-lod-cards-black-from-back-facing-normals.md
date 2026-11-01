---
title: Far-LOD leaf cards render black in Cycles when their custom normals point out of the back face
topic: geometry-meshes-uvs
tags: [trees, far LOD, leaf cards, custom normals, winding, Cycles, listing renders]
summary: Grown or simplified far-LOD cards can carry crown-proxy normals that point out of their back face (4–61 faces per level); Unity with Cull Off and mesh normals on both sides draws them lit, but Blender Cycles shades by the side facing the camera and draws them black, so wind every leaf face to agree with its own corner normals.
---
**Symptom:** Store-page renders of far LOD levels showed black cards in the crown; the same meshes looked fine in Unity.

**Cause:** Far cards are grown about their attach point and span more of the crown-normal field than their LOD0 twins, so some end up with corner normals pointing out of their back face. A two-sided Unity shader with mesh normals on both sides (and double-sided GI) never sees the winding; Cycles shades by the side facing the camera.

**Fix / rule:** Reverse the winding of every leaf face whose mean corner normal · face normal < 0, keeping each corner's normal, UVs and colours (a pack-step `orient` option). Make it the default for every non-rosette card tree before rendering any far level offline.

**Verify:** count near-black tree pixels (max channel < 40) in a render of each level: 4152 → 163 on one ancient tree; the pack log counts the flipped faces per level.

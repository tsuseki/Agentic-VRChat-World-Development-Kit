---
title: Alpha-cutout leaf cards need crown-proxy normals, and the shader must not flip them
topic: geometry-meshes-uvs
tags: [trees, foliage, leaf cards, custom normals, Blender, Data Transfer, FBX, VFACE]
summary: Give leaf-card vertices the normals of a smooth ellipsoid/hull fitted to the crown, import FBX normals (not Calculate), and disable the shader's back-face normal flip, or the canopy reads flat, speckled or black.
---
**Symptom:** A low-poly tree made of alpha-cutout leaf cards looks like a pile of cards: each card lit on its own, bright/dark speckle, cards flashing as the viewer moves; or after fixing that, half the crown goes near-black or patchy.

**Cause:** Each card's own face normal points in a random direction. Two-sided foliage shaders that flip the normal on back faces (VFACE) then invert half of any smoothed normals too.

**Fix:**
1. In Blender, fit a proxy to the leaf-vertex bounding box (×1.05): ellipsoid for round, capsule for columnar, the same fit squashed for umbrella crowns, shrink-wrapped + smoothed convex hull for clumpy crowns. Give each leaf loop the proxy normal: analytic `normalize((p−c)/r²)` per axis, or a Data Transfer modifier (custom normals, nearest face interpolated, leaf vertex group only), applied. Faces smooth; bark keeps its own normals.
2. Flip any card whose front faces into the crown (nearest point on the proxy) so the geometric front agrees with the new normal.
3. Export FBX with modifiers applied; in Unity set **Normals: Import**.
4. On the leaf material, turn off the back-face normal flip (a "mesh normals on both sides" toggle).

**Verify:** mean |dot(loop normal, face normal)| over leaf loops drops from 1.0 to ~0.45–0.6; the crown shows one soft lit side and shadow side from every angle.

Full pipeline and scripts: [lowpoly-tree-generation](../../skills/lowpoly-tree-generation/SKILL.md).

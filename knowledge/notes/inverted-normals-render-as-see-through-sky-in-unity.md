---
title: Inconsistent normals look fine in Blender but render as see-through sky in Unity
topic: blender-modeling
tags: [normals, backface culling, Blender, FBX, recalc_face_normals, blue faces]
summary: Blender previews double-sided, so faces flipped by operations like inset with negative depth render as holes showing the skybox in Unity; recalc normals on the joined mesh right before export.
---
**Symptom:** parts of a Blender-built prop render as see-through **blue** in Unity — the skybox showing through back-face-culled faces. Visible only where sky is behind (open areas); hidden in enclosed rooms, so it can pass review indoors.

**Cause:** Blender viewport/renders are double-sided; inverted or inconsistent faces (e.g. from `bmesh.ops.inset_individual` with negative depth) look correct there. Unity's lit shaders are single-sided.

**Fix / rule:** run a global `bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])` on the joined mesh right before FBX export. (Don't use this on intentionally two-sided open sheets — build those as closed prisms; see [blender-fbx-export-and-modeling-recipes](blender-fbx-export-and-modeling-recipes.md).)

**Verify:** screenshot against open sky in Unity, or count per-triangle facing vs outward direction.

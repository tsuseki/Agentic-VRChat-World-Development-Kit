---
title: Converting a box blockout into single-face interior meshes via Blender
topic: blender-modeling
tags: [blockout, single-face, Blender, FBX, UV, tiling, axis, headless]
summary: Keep only the visible face of each blockout box, rebuild as one quad per face in headless Blender, and watch for the FBX 180°-Y flip, transposed wall UVs and per-box rotation bugs.
---
**When:** An interior blocked out with primitive boxes wastes ~5 invisible faces per box and can't take per-surface floor/wall/ceiling materials.

**How (pipeline):**
1. In Unity, scan each box face with physics: sample points offset 0.35 m along the face normal; keep the face if any sample is un-buried and enclosed-interior rays hit within ~35 m. Write the kept faces to JSON.
2. Headless Blender builds one quad per kept face, material slots named by zone/role (e.g. `Env_{zone}_{role}`), UV = world metres / 2.
3. Unity instantiates the FBX, remaps materials by slot name, adds MeshColliders. Keep the source boxes disabled in the scene as reference (they are also useful as shadow occluders, see [zero-thickness-walls-leak-sun-use-shadow-only-occluders](zero-thickness-walls-leak-sun-use-shadow-only-occluders.md)).

**Pitfalls:**
- **FBX 180°-Y flip:** Unity (x,y,z) → Blender (x,z,y) plus `bake_space_transform` imported meshes rotated 180° about Y (x→−x, z→−z). Either compensate with root `localRotation = Euler(0,180,0)` or bake the flip into the export.
- **Wall-UV transpose:** with quad UV = (p·A/2, p·B/2), wall families where A is vertical rotate the texture 90° — invisible on noisy textures, glaring on coursed brick/stone. Swap U/V when |A.z| > 0.7 (Blender coords).
- **Tiling:** one repeat per 2 m read too busy; `mainTextureScale = 0.5` (one repeat per 4 m) suited 2K ambientCG brick/flagstone sets (~30 cm courses). Reject sets with grass/moss in the joints for clean interiors.
- **Per-box 90°-Y transpose:** one stair export came out with every box rotated 90° about its own centre (steps became a wall). Flat-shaded FBX gives per-face islands, so union-find can't recover boxes — assign each quad to its known blockout box (containment in the transposed AABB **and** face-plane-on-boundary test; containment alone is ambiguous for overlapping steps), rotate verts/normals/tangents per box, save as a mesh asset and point the scene at it. Re-check orientation whenever the FBX is regenerated.

**Verify:** check enclosure with raycast probes from interior points, not screenshots — unlit interiors are too dark to eyeball.

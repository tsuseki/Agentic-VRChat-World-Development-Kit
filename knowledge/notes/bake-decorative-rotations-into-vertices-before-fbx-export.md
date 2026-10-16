---
title: Split a posed Blender kit into per-object FBXs by baking rotation into vertex data
topic: blender-modeling
tags: [Blender, FBX export, transform_apply, rotation, asset kit, headless]
summary: Kit scenes pose buildings with yaw split between object rotation and mesh data; zero it, sweep for the min-area yaw, apply transforms into vertices, then export — renderer bounds will not reveal a leftover slant.
---
**Symptom:** buildings exported from a decorative kit scene render slanted in Unity once you set your own root rotation, while Blender `o.dimensions`, Unity `mesh.bounds` and `renderer.bounds` all look correct.

**Cause:** the source blend carries ±20–40° yaw partly in object rotation, partly in mesh data. Fixing it with `rotation_euler` alone puts the correction on the FBX node, which Unity instances discard when you assign a root rotation.

**How (per object, headless):**
1. Select, `parent_clear` keep-transform, zero world rotation (`matrix_world = Matrix.LocRotScale(loc, Quaternion(), scale)`).
2. Min-area yaw sweep on sampled vertices; **apply only if it shrinks footprint area > 8 %** (roof clutter fakes small minima — a "13°" fix on a gatehouse was a false positive).
3. `transform_apply(rotation=True, scale=True)` so the fix lives in **vertex data**; verify via world AABB.
4. Origin to bounds bottom-centre (via cursor), move to world origin.
5. Export with `apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True`. Result: true metre scale, floor-level pivot, square to the axes.

**Verify:** only two checks are trustworthy — a min-area vertex sweep on the CPU mesh, and rendered screenshots. Record which local axis each building's door faces (it varied within one kit).

**Pitfalls:** the Blender MCP CLI-execution tool can hard-time-out (~120 s); for anything non-trivial run `blender --background --python script.py` directly. See [blender-fbx-export-and-modeling-recipes](blender-fbx-export-and-modeling-recipes.md).

---
title: A prop that renders as a blank slab is facing away — measure the submesh normal
topic: geometry-meshes-uvs
tags: [orientation, normals, picture frame, submesh, placement script]
summary: When a prop renders featureless but materials, textures and bounds all check out, measure the content submesh's mean local normal; it is probably presenting its back.
---
**Symptom:** Script-placed picture frames (or similar) render as blank slabs. Materials bound, textures correct, aspect correct, wall behind each one — and a material diff against a known-good instance is identical.
**Cause:** The FBX's picture submesh has mean local normal (0,-1,0); the placer assumed +Y, so every frame faced the wall. Hand-placed diagnostic cameras were also on the wrong side, making good frames look blank too.
**Fix / rule:** Suspect orientation before material. Average the per-triangle geometric normals over the content submesh's index range (`mesh.GetSubMesh(i)`, `mesh.vertices`, `mesh.triangles`) in LOCAL space and orient from that.
**Verify (per instance):** the room side is clear for ≥0.55 m along the measured outward normal, and some other renderer contains a point 0.12 m along `-normal` (there is a wall behind it).

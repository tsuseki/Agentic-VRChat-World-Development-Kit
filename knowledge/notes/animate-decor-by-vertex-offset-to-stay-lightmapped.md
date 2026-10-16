---
title: Animate decor by vertex offset so it stays lightmapped
topic: lighting-baking
tags: [vertex animation, shader, lightmap, static batching, ambient motion, curtains]
summary: Transform/Animator motion forces a prop non-static and probe-lit, so it reads off next to baked neighbours; keep it static and move vertices in the shader instead.
sources: [https://note.com/laynts_/n/nbd10954de90d, https://note.com/arfox/n/n66cea5e16e0b]
---
**When:** Small ambient motion on otherwise static decor (floating stones, swaying curtains, hanging lanterns, leaves).
**Rule:** Keep the renderer static (ContributeGI + lightmapped); add a small vertex offset in the material's shader (sine with per-object or per-vertex phase). Never animate its Transform. The bake captures the rest pose, so the prop keeps its neighbours' baked shading.
**Pitfalls:**
- Static batching bakes meshes into world space: take the phase from vertex colour or a spare UV channel (not UV2, the lightmap), not object-space position.
- Pad the shader/renderer bounds by the max displacement or the prop pops at screen edges.
- Keep displacement small (cm, not dm): the lightmap shows the rest pose.
- A custom vertex shader is a shader change: on lilToon/Standard-default worlds, use it only when the user asks for the motion.
**Verify:** the moving prop matches its neighbours' brightness in a same-camera render; no edge popping at 110° FOV.

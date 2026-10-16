---
title: A black featureless door or picture is often hidden inside its own frame
topic: geometry-meshes-uvs
tags: [door, frame, picture frame, occlusion, black slab, bounds]
summary: When a door, lift, panel or picture renders as one black slab, check whether the leaf/canvas sits inside or behind its frame before touching lighting.
---
**Symptom:** A door, lift, hatch or framed panel renders as a single featureless black slab even with lights aimed at it. Luminance metrics say "dark object" and point at lighting.

**Cause:** Geometry occlusion. Observed cases: lift leaves spanning x 4.180-4.240 entirely inside a surround spanning 4.150-4.260; a door frame's front face 2 cm in front of its own leaf (only the handle poked through); picture frames that are solid 5 cm plates re-mounted onto a new wall band, pushing each frame's front face in front of its canvas (four pictures went black in one sweep). A canvas must be positioned from **its frame's front face**, never from the wall plane, because the frame's depth sits between the two.

**Fix / rule:** For every frame/leaf (or frame/canvas) pair, compute the front-face coordinate along the viewing axis (`bounds.center ± size/2`) and make the leaf **proud of the frame by 2-3 cm**. Determine the viewing axis by raycasting both ways from the assembly centre and taking the side with clearance; do not assume. Moving an assembly whose parts are separate objects is not one operation.

**Verify:** Assert `canvas.front > frame.front` (along the viewing axis) after any re-mount, and sweep the whole class (every door, lift, hatch, framed panel), not just the one reported.

Related: [metrics-that-cannot-see-their-defect](metrics-that-cannot-see-their-defect.md), [wall-hung-art-needs-a-wall-behind-it](wall-hung-art-needs-a-wall-behind-it.md)

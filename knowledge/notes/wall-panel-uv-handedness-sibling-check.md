---
title: Check wall-panel UV handedness against siblings and a text panel
topic: geometry-meshes-uvs
tags: [uv, mirrored, wall panel, handedness, raycast, artwork]
summary: Deciding a panel's outward face by raycast fails silently on collider-less walls, mirroring some panels; assert sibling panels on the same wall share handedness and validate with a panel showing text.
---
**Symptom:** After re-UVing wall-mounted panels, some images are mirrored (e.g. 2 of 4 canvases in a hallway).
**Cause:** `u` must increase to the viewer's right: `viewerRight = -Cross(Vector3.up, outward)`. Choosing `outward` by raycasting both faces ties when the decorative wall has no collider; the tie-break is arbitrary.
**Fix / rule:**
1. **Sibling agreement:** panels sharing a wall plane and rotation must share handedness. Correlate `u` against local +X per panel and assert all match; one disagreeing sibling is the bug.
2. **Validate on a panel with text:** abstract art looks fine mirrored; render a text panel head-on and read it — that proves the rule for all panels with the same configuration.

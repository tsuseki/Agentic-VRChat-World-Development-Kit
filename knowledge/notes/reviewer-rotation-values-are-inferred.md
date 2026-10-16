---
title: Recompute a reviewer's prescribed rotation from measured facing
topic: agent-workflow-verification
tags: [reviewer, rotation, facing, furniture, eulerAngles, measurement]
summary: A reviewer's suggested rotation.y is inferred from the transform, not the model's forward axis; take the direction of the finding but recompute the magnitude from measured facing.
---
**Symptom:** A scene reviewer reports stools facing the wrong way and prescribes "set `rotation.y = 90`". Applying it leaves them nearly as wrong, but looks fixed in a diff.

**Cause:** The reviewer sees the render and the Euler value; it cannot see that the FBX's seat points +X. Example: stools at `rotY = 180` measured facing 94 degrees; the counter is at 180, so the correct value was `180 + (180 - 94) = 266`. The suggested 90 would have been 176 degrees off.

**Fix / rule:** Measure facing from vertices: backrest centroid (verts above 0.68 of object height) minus seat centroid (0.30-0.60), `atan2(d.x, d.z)`; the sitter faces `+180`. Apply as a delta to the existing `eulerAngles.y`. Treat inferred reviewer numbers as the default suspect. This works for seating with a backrest; for symmetric case furniture, judge facing by render (see [vertex-density-cannot-tell-which-way-furniture-faces](vertex-density-cannot-tell-which-way-furniture-faces.md)).

**Verify:** Re-measure and quote the new measured facing as proof, never the transform value.

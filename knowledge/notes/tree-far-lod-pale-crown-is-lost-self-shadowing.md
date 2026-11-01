---
title: A far-LOD crown that reads paler than LOD0 has lost self-shadowing, not normals or AO
topic: geometry-meshes-uvs
tags: [trees, far LOD, card cull, crown normals, shading, luminance, LOD pop]
summary: The coverage cull keeps the outer and upper cards, so a far crown loses the inner self-shadowed cards and reads paler; sampling LOD0's normal field at the far level's corners and comparing area-weighted sun lambert proves the normals are right, and the levers are crown density and switch distance.
---
**Symptom:** Far LOD levels read a little brighter or paler than LOD0 at the switch.

**Cause:** The visible-coverage card cull keeps the outer and upper cards; the dark inner cards that shaded the crown go first.

**Fix / rule:**
- Don't patch normals or AO. Change crown density (cards kept, grow) or the switch distance.
- Vertex colours that carry wind data are not AO; don't read them as occlusion.
- For wide flat crowns weight the views from above and below down in the cull, so the eye-height side view stays closed.

**Verify:** sample LOD0's normal field at the far level's corner positions and compare the area-weighted sun lambert with the far level's own. Equal values mean the shading is right and the difference is self-shadowing. The Unity LOD gate: coverage ≥ 0.92 and luminance 0.95–1.05 against the previous level (the bright side fails too: 1.095).

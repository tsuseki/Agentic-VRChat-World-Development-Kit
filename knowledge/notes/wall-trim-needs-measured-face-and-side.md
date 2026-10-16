---
title: Mounting trim proud of a wall needs the measured face coordinate and the room side
topic: placement-layout-design
tags: [wall trim, wall art, bounds, raycast, clash test, z-fighting]
summary: Assume either the wall face position or which side the room is on and the whole assembly builds inside the wall with no error; measure both, print proud distances, and include walls in clash tests.
---
**Symptom:** A timber band, cap, glow reveal, fins and end stop — twelve objects — are invisible. All were placed at `zWall + 0.025` using a remembered wall plane.

**Cause:** Two wrong assumptions: the face was at 15.85, not the remembered 15.90 (that number came from another leg of the corridor), and the room was at lower z, so proud was `-z`. Each leg of an L-shaped corridor faces the opposite way. The clash test passed because walls were excluded as "obviously fine".

**Fix / rule:**
1. Take the face coordinate from the wall renderer's `bounds.min` / `bounds.max`, never a remembered plane or a name.
2. Determine the occupied side by raycasting both ways from the wall centre, or from walk-surface extents.
3. After placing, print `face - piece.min` (or equivalent) per object and assert it's positive. A per-object `proud=0.050 m` column is the proof; "placed 12 pieces" isn't.
4. Run the clash test **with walls included**.

**Pitfalls:** a depth change to a wall plane invalidates every depth relationship on it — flattening art onto a new band left canvases coplanar with their frames (z-fight) and made others interpenetrate. Re-audit canvas-vs-frame and canvas-vs-canvas after the pass.

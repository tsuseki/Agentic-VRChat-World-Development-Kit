---
title: Raycast behind wall-mounted art — no hit within 0.5 m means it is floating
topic: placement-layout-design
tags: [wall art, canvas, screen, raycast, placement, wash light]
summary: Wall-mounted objects get placed on a coordinate line rather than a real wall; cast a short ray along the back normal and relocate floaters onto measured continuous wall runs.
---
**Symptom:** Two of four hall canvases on the same line read as black rectangles. Casting backwards: two hit a wall at 0.24 m, two hit **nothing for ~13 m**.

**Cause:** They were placed on a coordinate line, not on geometry. A picture with no wall behind gets no bounce and is lit from the wrong side. The "picture wall" was mostly void — only two real wall runs existed.

**Fix / rule:**
- For every wall-mounted object, cast a short ray along its back normal; no hit within ~0.5 m = not on a wall.
- Before relocating, sweep the candidate wall line in 0.5 m steps and print continuous runs, so you place on real geometry clear of doors/openings.
- Move the object's wash light with it, or it reads black in the new spot too.

**Pitfalls:** judge from the side the room is on. Canvases/screens are often 3 cm boxes that render from both sides, so a shot from behind looks "buried in a wall" — a review flagged exactly that false blocker.

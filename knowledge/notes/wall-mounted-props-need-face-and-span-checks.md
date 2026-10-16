---
title: Assert wall-mounted props are on the occupied face and inside a solid wall span
topic: placement-layout-design
tags: [wall mount, sconce, artwork, wall thickness, openings, placement audit]
summary: A wall has thickness and gaps; check each mounted prop is on the occupiable side and within a solid segment, or whole schemes face the wrong room or float in doorways.
---
**Symptom:** A 39 m corridor has bare walls (face-on luminance flat, no variation in frame), while sconce glow and artwork bleed into the rooms on the other side "from nowhere". The reported bug is a light leak, which sends you hunting for a hole in the wall.

**Cause:** All 20 corridor fixtures were authored at z 12.80-12.94 against a slab spanning z 12.85-13.15 with the corridor beyond 13.15: they were on (or inside) the wrong face. "At the wall" is ambiguous by the slab's depth. Every object looks right in isolation, and the symptom appears in a different room from the mistake.

**Fix / rule:** Assert two things per mounted object:
1. **Face:** it is on the occupiable side (`bounds.min.z >= wallFaceZ` for a +z-facing corridor) and rotated to face into that room.
2. **Span:** its footprint lies inside a solid segment. Enumerate the wall's segments, treat gaps as openings, and test each object's `bounds.min/max` against them. This check found artworks sitting inside or straddling door openings that the reviewer had not seen.

Generalisation: whenever a pass places things relative to architecture, intersect the two sets and print the hits.

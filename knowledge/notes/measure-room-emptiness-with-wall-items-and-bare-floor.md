---
title: Props per square metre cannot see an empty-looking room
topic: placement-layout-design
tags: [room dressing, emptiness, metrics, wall-mounted, bare floor, review]
summary: A room can score high on props per 100 m² and still read as a bare box; track wall-mounted item count per wall run, largest bare floor square, furniture coverage, and counts with clusters collapsed.
---
**Symptom:** Rooms are reported as "kinda empty", yet every room passes a props-per-100 m² metric (one scored 122 props/100 m², among the highest; ~1% of walkable cells were > 4 m from a prop). A reviewer at standing eye height ranks the same room the emptiest in the world.

**Cause:** What the counter cannot see:
- 30 "surface objects" were 27 back-bar bottles. A count treats a bottle and a sofa as one prop each; cluster-heavy dressing inflates the number without filling space.
- A 13 x 4.5 m wall had zero wall-mounted items (nothing hung, no console, no shelving). A whole room with 0 wall items read as unfinished before anything else.
- 5.5 m of continuous empty floor reads as a hole even when mean distance-to-prop is low because the perimeter is dressed.

**Fix / rule:** Measure what tracks the complaint:
1. wall-mounted item count per wall run (0 is always wrong on a wall over ~4 m);
2. largest inscribed bare square on the floor plate;
3. furniture coverage % of floor area;
4. object count **after** collapsing tabletop clusters to one item.

Before writing placement code, ask the scene reviewer which rooms read empty and where to spend the work; it returns a ranked list naming the specific wall and bare square.

---
title: Blockout rules: reference-avatar capsules, areas 200 m+ apart near the origin, world before scripts
topic: placement-layout-design
tags: [blockout, scale, avatar height, float precision, teleport, layout]
summary: Scale to the group's reference avatar (default 1.3 m eye), keep separate areas ≥200 m apart but clustered near the origin, and wire scripts only after the layout settles.
---
**Rules:**
- Scale to the **reference eye height in WORLD.md** (default **1.3 m eye**, avatar about 1.4 m; full-size groups 1.6 m eye, 1.75 m avatar), not to your own avatar. Reference capsule: Unity capsule scale (0.4, 0.7, 0.4) for the 1.4 m default, (0.45, 0.875, 0.45) for 1.75 m. Tag it `EditorOnly`. Shell (and outdoor features: trees, shrubs, rocks, landmarks) and collision rules: spatial-design §5.9.
- Multi-area worlds connected by teleport doors: keep areas **≥ 200 m apart** (main area to each island and between islands) but packed near the origin for float precision: island slots at ±200 m on X and Z, each with |centre| + half-extent < 256 m per axis (clip-planes skill §4). An earlier layout used ≥100 m with areas at ±170 m; that spacing is superseded.
- **World geometry before scripts**: wiring (doors → spawn, references, ambient audio) waits until the layout settles; premature wiring and placeholder props get deleted when layout iterates.
- Keep teleport arrival Transforms as **children of the structures they belong to**, so wiring survives moves.
- Screenshot-verify each geometry change.

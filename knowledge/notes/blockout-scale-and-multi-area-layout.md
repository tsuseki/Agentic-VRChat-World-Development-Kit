---
title: Blockout rules: reference-avatar capsules, areas 100 m+ apart near the origin, world before scripts
topic: placement-layout-design
tags: [blockout, scale, avatar height, float precision, teleport, layout]
summary: Scale to the group's reference avatar (default 1.2 m eye), keep separate areas ≥100 m apart but clustered near the origin, and wire scripts only after the layout settles.
---
**Rules:**
- Scale to the **reference eye height in WORLD.md** (default **1.2 m eye**, avatar about 1.3 m; full-size groups 1.6 m eye, 1.75 m avatar), not to your own avatar. Reference capsule: Unity capsule scale (0.4, 0.65, 0.4) for the 1.3 m default, (0.45, 0.875, 0.45) for 1.75 m. Tag it `EditorOnly`. Shell and collision rules: spatial-design §5.9.
- Multi-area worlds connected by teleport doors: keep areas **≥ 100 m apart edge-to-edge** but packed near the origin for float precision (e.g. one at origin, others at ±170 m on X and Z).
- **World geometry before scripts**: wiring (doors → spawn, references, ambient audio) waits until the layout settles; premature wiring and placeholder props get deleted when layout iterates.
- Keep teleport arrival Transforms as **children of the structures they belong to**, so wiring survives moves.
- Screenshot-verify each geometry change.

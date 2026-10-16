---
title: Keep hand-placed dressing outside roots that a generator script rebuilds
topic: unity-editor-scripting-mcp
tags: [procedural, generator, scene hierarchy, builder script, dressing]
summary: A "Place Props" script that destroys and rebuilds its root erases anything hand-placed under it; give hand dressing its own scene root.
---
**Rule:**
- If a builder destroys and rebuilds a root (`Props`, `Generated`), everything hand-placed under it is erased on the next run. Put hand dressing under a separate root (e.g. `Dressing/BarDrinks`, `Dressing/GarageProps`).
- Treat the generator script as the source of truth (e.g. a Blender script generating terrain/road/pads from a spline), not the saved `.blend`/scene. Rebuild and re-export in one headless run; keep `.blend`/`.fbx` sources in a folder outside `Assets/`.
- Constants that couple generator output to hand-placed scene objects (e.g. a building pinned at an absolute offset from the hub origin) must be re-derived when the generator's origin moves; document them as pinned.
- Merging all dressing props into one mesh per material via an accumulator keeps renderer counts low (~1M tris in 272 renderers).

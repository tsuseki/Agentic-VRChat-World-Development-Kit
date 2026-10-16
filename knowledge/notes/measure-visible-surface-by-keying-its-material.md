---
title: Measure how much of a surface is visible by keying its material and counting pixels
topic: agent-workflow-verification
tags: [render-metrics, occlusion, coverage, unlit, positive-control, attribution]
summary: AABB occlusion tests treat plants and props as solid and can be off by 30x; force the judged surface to unlit magenta, render from eye height, and divide by a render with occluders hidden.
---
**When:** A reviewer keeps saying something (e.g. "the beds read as bare soil at eye height") while your geometric metrics say it's fine.

**Example:** canopy coverage by AABB footprint said 71-82% covered; segment-vs-AABB occlusion said 3.0% bare; the render said **87.3% bare**. A plant's bounding box is mostly air.

**How:**
1. Snapshot the material; set `shader = Unlit/Color`, `color = magenta`. Unlit means the pixel is exactly (255,0,255) or it isn't the surface.
2. Render pass A: the scene as it ships, from real player cameras.
3. Render pass B (**positive control**): hide the occluders. This is the "all visible" denominator and proves the key is live.
4. `visible% = magenta(A) / magenta(B)`, summed over cameras.
5. Restore the material from version control (`git checkout -- the.mat`), never by re-typing values.

Because it's a render, it respects alpha cutout, `clip()`, draw order and perspective - every reason the geometric test lied.

**Attribute before you fix:** raycast a coarse grid from the camera against candidate bounds and tally the **nearest** hit per ray. In the example, 83% of visible soil belonged to 37 objects that didn't match the name pattern being iterated (a pot's soil, not the bed). **Select by material, not by name.**

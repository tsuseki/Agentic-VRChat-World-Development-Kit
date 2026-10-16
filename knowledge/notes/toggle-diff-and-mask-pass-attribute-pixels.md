---
title: Attribute rendered pixels to objects with a toggle-diff or magenta mask pass
topic: agent-workflow-verification
tags: [render diff, mask pass, pixel attribution, occlusion, hemisphere rays, verification]
summary: To know which renderer a pixel belongs to and what it contributes, render twice: with the suspect toggled off, or with a magenta Unlit material swapped on.
---
**When:** You need to measure what an object actually contributes to a frame, or which renderer a problem pixel belongs to, without guessing pixel windows.

**How:**
- **Toggle-diff:** render the same camera with the suspect renderers enabled and disabled, and diff. It locates the object and measures its contribution. Bucket changed pixels by delta (>0.01 / >0.15 / >0.30 / >0.50); an average over all changed pixels is dominated by the feathered rim and hides the core. Solving `a*decal + (1-a)*ground` across two channels from these numbers pinned one "colour bug" as an alpha bug (core alpha 0.53).
- **Magenta mask pass:** render normally, then again with an `Unlit/Color` magenta material swapped onto the suspect (restore `sharedMaterials` after); classify pixels by the mask and measure the normal frame there. Use ray-vs-triangle instead when you need a single pixel's owner or hit distance, keeping the nearest hit across all geometry (see [pixel-attribution-needs-nearest-hit](pixel-attribution-needs-nearest-hit.md)); it once proved a black ceiling line was the roof mesh, not the trim everyone had blamed.
- **Can light reach it at all?** For a surface rendering near zero, cast ~256 hemisphere rays from the point and count escapes. Zero escapes means no material or intensity change will help; the fix is geometry. A hard edge on a dark region means occlusion or unwritten texels; a gradient means shading.

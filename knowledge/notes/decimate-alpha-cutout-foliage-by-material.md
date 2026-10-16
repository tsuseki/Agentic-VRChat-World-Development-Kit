---
title: Decimate alpha-cutout foliage with stock Collapse, split by material, gated by UV coverage
topic: blender-modeling
tags: [blender, decimate, foliage, alpha cutout, lod, uv coverage]
summary: Stock Decimate>Collapse at a gentler ratio on leaf cards and a harder one on stems cuts plant tris ~60% with zero lost leaf coverage; do not hand-roll a decimator.
---
**When:** Archviz-style plants built from subdivided leaf-card quads whose shape comes from texture alpha are too heavy for a world.
**How:**
- Split leaf vs stem by material and run Blender's stock `Decimate > Collapse` on each at a different ratio. Measured working ratios: leaves ~0.38–0.53, stems ~0.24–0.38. Result on six species: 67,588 → 25,524 tris (−62%) with visually identical silhouettes. One global ratio has to be gentle enough for the cards, so stems never get squeezed.
- Do not write your own collapse decimator: a QEM/boundary-pinned/alpha-gated custom one measured worse (3.99% leaf coverage lost vs 0.0000% for the modifier). `bmesh.ops.weld_verts` does not carry UVs — a welded corner keeps its old UV, silently stretching the texture.
**Verify:**
- **UV coverage metric:** rasterise every face's UV footprint into a boolean canvas (pad UV to [-0.25, 1.25] for wrapped islands), AND with a 2 px-dilated `alpha >= 0.40` mask of the leaf texture, report % of opaque texels no longer covered.
- Always run a harsh positive control (ratio 0.05 gave 24–44% loss) so a 0.00% result is meaningful.
- Loose-part count of the leaf subset should not move much; a jump means thin connections pinched apart (over-decimation tell).
- Render orig vs LOD from identical cameras in headless EEVEE (alpha via `Math GREATER_THAN 0.45` → Alpha, backface culling off, `surface_render_method = 'DITHERED'`), including a crown close-up — a full-body shot is too small to show a clipped tip.

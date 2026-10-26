---
title: Soft and organic props bake torn, faceted dark triangles when their UV2 is fragmented into sub-texel charts
topic: lighting-baking
tags: [UV2, lightmap, charts, texel density, pillows, cushions, sculptures, receiveGI, Light Volumes, audit]
summary: Pillows, cushions, throws, bedding and sculptures with auto-unwrapped UV2 split into hundreds of charts under a few texels each and bake jagged dark facets; measure fragmentation per renderer before the bake, move small soft decor to probes or Light Volumes, and re-unwrap large furniture.
---
**Symptom:** In a finished interior bake, pillows, cushions, throws, bedding and small sculptures show torn shading: jagged, faceted dark triangles and broken chart seams at near reach. The room mean looks fine; wide review shots miss it.

**Cause:** The UV2 is fragmented, not the bake settings. A scene-wide measurement found about 800 of 2,379 small lightmapped renderers with the same signature:
- a pillow with 104 UV2 charts, 94 of them under 4 texels;
- sofa pillows with 4,600 of 4,660 triangles under 0.01 texel², so the whole pillow sat in about 7 texels;
- a bed mesh with 7,600 of 8,254 UV2 triangles degenerate;
- sculptures with 77 of 87 charts tiny, at about 19 texels/m.

Automatic unwraps cut noisy, curved surfaces into many tiny charts; each chart then holds one or two irradiance samples and a gutter, so neighbouring triangles land on unrelated samples. An A/B with the post-bake mesh merge on and off showed identical faceting: the merge was not the cause.

**Fix / rule:**
- Small soft and organic decor (about ≤ 0.4 m, plus loose soft pieces such as pillows, cushions and throws): keep `ContributeGI` and set `receiveGI = LightProbes` (a Light Volume aware material in worlds with VRC Light Volumes). It still casts its shadow into the bake.
- Large furniture: regenerate or author the UV2 (importer margin method Manual, or a flat-chart unwrap in Blender with few large charts), set Scale In Lightmap so the main face gets at least 8 texels across its short side, and re-bake.
- Never raise Scale In Lightmap to rescue a fragmented UV2: the chart count stays, the atlas cost grows with the square of the scale.

**Verify:** per lightmapped renderer, measure triangle texel areas and chart sizes from UV2 and `lightmapScaleOffset`. Flag more than 30 % of triangles under 0.01 texel² or more than 50 % of charts under 4 texels (chart size = √(chart UV2 area) in texels). After the fix, near-reach shots (≤ 0.6 m) plus a lightmap-only render of each flagged piece; positive control: the same rig on an unfixed flagged piece shows the facets.

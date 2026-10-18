---
title: A custom cutout foliage shader tagged RenderType Opaque bakes leaf cards as solid rectangles
topic: lighting-baking
tags: [Progressive lightmapper, RenderType, TransparentCutout, foliage, leaf cards, baked shadows, shader]
summary: The Progressive lightmapper treats a shader tagged RenderType=Opaque as opaque, so every leaf card casts a rectangular baked shadow; tag the SubShader RenderType=TransparentCutout to get leaf-shaped dappled shadows.
---
**Symptom:** After a bake, trees using a custom alpha-cutout leaf shader cast solid rectangular shadows, one per leaf card, instead of dappled leaf shadows.

**Cause:** Unity's lightmapper decides whether to alpha-test a material for shadow casting from the shader's `RenderType` tag (plus `_MainTex`/`_Cutoff`/`_Color`). The SubShader was tagged `"RenderType"="Opaque"`, so the cards were baked as opaque quads, even though `clip()` cut them correctly on screen.

**Fix / rule:** Tag the SubShader `"RenderType"="TransparentCutout"` (keep `_MainTex` and `_Cutoff` as the alpha source). Tested in one bake with one tree under four materials: only the Opaque-tagged one produced rectangles; the TransparentCutout-tagged custom shader gave leaf-shaped dappled shadows.

**Verify:** bake a small test (one tree on a plane) and look at the ground shadow from above: it must show the leaf pattern, not card outlines.

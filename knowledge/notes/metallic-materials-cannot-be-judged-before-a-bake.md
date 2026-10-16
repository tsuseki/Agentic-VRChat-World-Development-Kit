---
title: Author metals low-metallic until the bake exists, and judge them by render
topic: materials-textures-shaders
tags: [metallic, pbr, unbaked, reflection-probe, smoothness]
summary: In an unbaked scene a high-metallic material has nothing to reflect and renders as one flat slab, so inspector values predict nothing about how a metal reads.
---
**Symptom:** A multi-part stainless appliance authored at metallic 0.85 / smoothness 0.58 rendered in the unbaked scene as one featureless white monolith - seams, knobs and vents vanished. In dark scenes the same root cause makes metals read black.

**Cause:** A metallic surface has almost no diffuse response; its look is the reflection probe / lighting it samples. With no bake and only flat skybox ambient, every facet returns the same constant and normals stop reading. Higher metallic = flatter.

**Fix / rule** (scope: unbaked scenes only; these are interim values, and once the bake and probes exist the probe-dependent rule in the related note replaces them):
- Until the bake exists, author metals as dark albedo + moderate metallic (about albedo 0.40, metallic 0.55, smoothness 0.45), or split the object into contrasting parts so silhouette does the work. Revisit after the bake.
- Never sign off a metal from inspector numbers - render it in context.

Related: [metallic-depends-on-what-the-reflection-probe-sees](metallic-depends-on-what-the-reflection-probe-sees.md) (the mirror-image symptom in dark scenes), [unbaked-props-read-blue](unbaked-props-read-blue.md)

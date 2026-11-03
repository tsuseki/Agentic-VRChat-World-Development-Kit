---
title: Concept art must bind what is in each area, or every area comes out the same
topic: agent-workflow-verification
tags: [concept art, area references, reviewers, generators, distinctness]
summary: A kit rule that images bind only mood/palette/materials/density let a structure pass ignore per-area concept art and extrude one generic block kit on every floor; images must bind content (structure and object types, signature pieces), areas must be built from a picked image, and reviewers must check content match and distinctness.
---

**Symptom.** A multi-floor megastructure had per-floor concept art (waterworks with tanks and
sluices, a reactor floor, a foundry with furnaces, cranes and a hull in scaffolding, labs, command).
A structure pass filled every hall floor with the same polygon-extruded "inner buildings", finished
with the same window-bay kit, so seven floors read as identical residential districts. The layout
review passed it at 8/10. The user had to restate content that was already in the concept art.

**Cause.** A chain of kit rules, each reasonable alone:
1. "Images are feel references, never blueprints" bound only mood, palette, materials, lighting
   character and density. *What is there* (furnaces, tanks, cranes) is none of those, so by rule
   the concept art could not set the floors' content; it appeared in 12 kit files.
2. Per-area images were logged as "density/feel references for the later furniture passes", so
   the structure pass between greybox and furniture had no image input at all.
3. The pass brief and plan were text (pillars, platforms, tall streets) and the generator had one
   archetype ("inner building" = extruded polygon), placed by a greedy pass that targeted a metric
   (largest open circle < 80 m). A metric-driven fill with one kit converges to uniform filler.
4. The layout reviewer was forbidden to compare geometry with images and never judges styling, and
   the dressing reviewer only runs on furniture passes: inner structures sat in a gap no reviewer
   owned, and no check compared floors with each other.

**Fix / rule.**
- Images are *content and feel* references: they bind structure and object types, silhouettes and
  each area's signature pieces (plus feel); they still never set exact positions, proportions or
  layout.
- One "Area references" table in the world brief: per area its picked image, signature pieces and
  the user's words; every area brief copies its row; read it before asking the user.
- Build from concept art, never from memory: standalone blockout of each structure → captures from
  several angles → concept art painted over them, one folder per area → user picks → build with the
  image open.
- Reviewers (layout reviewer on any structure pass, dressing reviewer on build-out) list the
  image's signature pieces and treat each missing one as a blocker, and make a distinctness sheet
  (one shot per area); areas with different images that read the same is a blocker.
- Generators: one generic kit on many areas, or filler placed to satisfy a space metric, is a red
  flag; each programme gets its own archetypes shaped from its image.

**Verify.** The next structure pass's report shows each area's blockout next to its source image
and a per-area distinctness sheet; the reviewer's report lists signature pieces per area as
present/missing.

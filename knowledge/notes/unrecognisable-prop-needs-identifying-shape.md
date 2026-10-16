---
title: A prop that reads as a featureless primitive needs identifying geometry, not better materials
topic: placement-layout-design
tags: [prop design, silhouette, identification, emissive cue, review feedback, dark room]
summary: When review says a prop reads as a plain box, add the 2–3 shape features people use to identify it (a speaker's drivers) plus a small emissive cue in dark rooms; material tuning only makes a nicer box.
---
**Symptom:** A hand-built floor-standing speaker fails review twice as "a slim black cabinet or a bin". Round 1 separated cabinet and grille by albedo (0.075 vs 0.045 — invisible in a dark room); round 2 by smoothness (0.65 vs 0.03 — no fixture threw a highlight on that vertical face).

**Cause:** The verdict is about **semantics** ("what is this?"), not surface quality. Cheapest-first triage is right for defects but wrong for "unrecognisable" — the cheap fixes are all dead ends.

**Fix / rule:** list the 2–3 features a person uses to identify the object and model those first. Here: four cylinders on the front baffle (three cone drivers + a tweeter) and a 12 mm emissive standby dot — 608 tris, ~30 minutes, passed in one round. In a dark room add one small **emissive** cue (standby LED, display, pilot light): emission reads at any distance and in silhouette, independent of the bake.

---
title: Set Terrain.drawInstanced on every terrain tile
topic: performance
tags: [terrain, drawInstanced, draw calls]
summary: Terrain.drawInstanced = true cut ~1,400 draws at spawn over 9 terrain tiles with identical terrain pixels; make it a standard D.2 step.
---
**Symptom:** a world of 9 terrain tiles spent ~1,400 draws at spawn on terrain patches.

**Fix / rule:** set `Terrain.drawInstanced = true` on every tile (edit mode, save). Three worlds did it; terrain
pixels were identical in same-camera diffs.

**Verify:** draws at the same pose before/after and a same-camera diff of terrain-heavy views.

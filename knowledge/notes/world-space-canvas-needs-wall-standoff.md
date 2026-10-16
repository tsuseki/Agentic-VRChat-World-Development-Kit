---
title: World-space UI canvases a few cm in front of a wall may not render — keep ≥20 cm
topic: audio-video-ui
tags: [ugui, world space canvas, wall, standoff, text]
summary: A world-space UGUI canvas ~3 cm proud of a cube wall drew nothing (not even its background image) in edit or play mode; ≥20 cm off the wall rendered fine.
---
**Symptom:** A world-space canvas generates vertices (`Text.cachedTextGenerator.vertexCount > 0`) yet nothing draws, including its solid background Image.
**Fix / rule:** Keep scripted wall boards at ≥20 cm standoff from the wall. `isStatic` was also cleared during the same debug; static on canvases remains suspect and is cheap to avoid.
**Verify:** Isolation test — move the canvas 1 m into open space; if it appears, it is wall proximity, not the canvas.

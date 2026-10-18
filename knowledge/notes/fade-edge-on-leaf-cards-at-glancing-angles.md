---
title: Edge-on leaf cards smear into streaks up close; fade cards at glancing angles
topic: materials-textures-shaders
tags: [foliage, leaf cards, Crispy Foliage, edge fade, glancing angle, VR, shader]
summary: Cards seen edge-on smear into streaks within ~1 m; Crispy Foliage's 'Fade at Glancing Angles' (_EdgeFade 1) removes them with only 1–2 % pixel change at distance; 0.5 is a middle setting if edge-on cards turn into dots.
sources: [https://gitlab.com/s-ilent/crispy-foliage]
---
**Symptom:** Walking past a low-poly tree in VR, leaf cards viewed nearly edge-on smear into thin streaks within ~1 m of the eye.

**Cause:** A card almost parallel to the view ray compresses its whole texture into a few pixel columns; mips and alpha test turn it into a streak.

**Fix / rule:** Use a foliage shader that fades cards by view angle. On Silent's Crispy Foliage, enable "Fade at Glancing Angles" (`_EdgeFade` 1). Same-camera lineup: the streaks were gone up close, and at distance the frame changed by only 1–2 % of pixels.

**Pitfall:** at full strength, edge-on cards can show as dots within ~3 m. `_EdgeFade` 0.5 is a middle setting.

**Verify:** same-camera captures at ~0.5–1 m and at normal viewing distance, before and after; count changed pixels at distance and inspect the near shot for streaks and dots.

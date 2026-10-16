---
title: Audit asset-pack prop appearance by rendering, not by querying materials
topic: materials-textures-shaders
tags: [asset pack, atlas, material audit, colour sweep, render]
summary: Pack materials are often white-tinted over a shared atlas, so colour/metallic/name sweeps find nothing; sweep a class of props by rendering it.
---
**Symptom:** A scripted sweep for gold/brass props (warm `_Color`, metallic > 0.3, names containing gold/brass) returns zero hits while gold props are visibly still in the room.
**Cause:** Pack materials use `color = (1,1,1,1)` over a shared atlas that carries the actual colour; several unrelated props share one material, so even the material name does not identify the look.
**Fix / rule:** You cannot audit a pack's appearance from material properties. Render the whole class (every prop on the same atlas) and judge by eye. A reviewer naming four offending props does not mean there are only four — find every user of the same atlas and render them.

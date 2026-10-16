---
title: World-space TextMesh on the default font material draws through all geometry
topic: materials-textures-shaders
tags: [TextMesh, font material, ZTest, GUI/Text Shader, labels, depth]
summary: The built-in text shader uses ZTest Always, so TextMesh labels show through walls and floors; use a copy with ZTest LEqual.
---
**Symptom:** A world-space `TextMesh` panel in one room appears in many unrelated rooms, through floors and partitions, mirrored from behind. In blockout plan views, lower-floor room labels bleed through upper-floor slabs and look like misplaced labels.

**Cause:** `TextMesh` on the default `Font Material` uses the built-in `GUI/Text Shader`, which has `ZTest Always`: it draws on top of geometry regardless of depth.

**Fix / rule:** Copy `GUI/Text Shader`, change to `ZTest LEqual`, bind `_MainTex` to the live font atlas via `tm.font.material.mainTexture` (the same `Texture2D` survives atlas rebuilds), assign the material to the TextMesh's `MeshRenderer`, and clear the label's static editor flags so it is neither lightmapped nor probe-static.

For plan-view renders with default-shader blockout labels, toggle labels by local Y per floor (keep exterior/garden labels on via a footprint test) instead of hiding groups.

Orientation: identity rotation on a `TextMesh` reads from -Z; rotating 180 degrees on Y mirrors it; `(90, 0, 0)` lays it flat and readable from a top-down camera.

**Verify:** One face-on screenshot: if the panel reads perfectly there and wrongly from everywhere else, only the depth state is wrong.

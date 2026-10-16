---
title: Surface-shader alphatest pragma can make cutout foliage blend with the framebuffer
topic: materials-textures-shaders
tags: [cutout, foliage, surface shader, alphatest, clip, HDR skybox, white leaves]
summary: A `alphatest:_Cutoff` surface-shader pragma left cutout leaves blending with whatever was behind them, so leaves in front of a bright HDR sky burned to white; use an explicit clip() instead.
---
**Symptom:** Every cutout-foliage renderer (hundreds) rendered as a flat white silhouette wherever it sat in front of bright glazing or an HDR skybox. The same material on the same mesh read correctly green in front of a plaster wall.

**Cause:** The surface-shader pragma

```
#pragma surface surf Standard fullforwardshadows addshadow alphatest:_Cutoff
```

did not produce a plainly opaque pass. The leaf blended against the framebuffer, so a bright HDR background saturated it to white. Because it is brightness-dependent it looks exactly like a lighting or material bug.

**Fix / rule:** Drop the pragma, clip explicitly, and declare the property yourself:

```
Tags { "RenderType"="Opaque" "Queue"="Geometry+50" }
#pragma surface surf Standard fullforwardshadows addshadow
...
half _Cutoff;                      // the pragma used to declare this
fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
clip(c.a - _Cutoff);
o.Alpha = 1;
```

Things that were ruled out (each costing renders) and did *not* fix it: material binding, the texture on disk, `_Color` tint (black had no effect), compile errors, render queue, texture streaming, static batching, `AlphaToMask Off`. A `VFACE` normal flip for `Cull Off` leaves was a real improvement worth keeping, but not this bug.

**Verify:** Put quads with the *same* material flat against an opaque interior wall and in front of the sky. If only the background changes the result, it is a framebuffer blend: test the pass setup, not the material. No material property, texture inspection or albedo probe can see this defect.

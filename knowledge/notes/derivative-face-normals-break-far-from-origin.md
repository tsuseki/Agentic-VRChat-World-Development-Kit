---
title: Screen-derivative face normals from worldPos turn to noise far from the world origin
topic: materials-textures-shaders
tags: [shader, ddx, ddy, float precision, worldPos, edge fade, leaf cards, supersampling, 4K, stipple, built-in RP]
summary: A fragment-shader face normal built from cross(ddy(worldPos), ddx(worldPos)) is quantised noise when the scene sits a kilometre or more from the origin and the pixel footprint is about a millimetre (near leaves at 4K or in supersampled captures); interpolate a camera-relative position from the vertex shader and take the derivatives of that instead.
---
**Symptom:** Near leaf cards show scattered single-pixel dark holes (a stipple), densest toward the card edges. It appears at 4K and in 2× supersampled captures, but not at 1080p. MSAA 8, 4 and 1 all look the same, so it is not alpha to coverage or the MSAA resolve. The same plants near the origin are clean, and the atlas alpha is clean.

**Cause:** A view-angle edge fade took its card normal from `normalize(cross(ddy(IN.worldPos), ddx(IN.worldPos)))`. At 1.3–1.9 km from the origin, a float `worldPos` steps in about 0.1 mm. A near-leaf pixel at 4K is about 1 mm across, so neighbouring pixels differ by only a few float steps. The derivative normal is then noise, `|cos|` randomly drops under the fade angle, the fade multiplies alpha down, and `clip()` punches holes.

**Fix / rule:**
- **Interpolate a small number.** In the vertex function, write `camRel = mul((float3x3)unity_ObjectToWorld, v.vertex.xyz) + (objectOrigin - _WorldSpaceCameraPos)`. Subtracting the object origin from the camera first means the large-number subtraction happens once per object. In the fragment, take `cross(ddy(camRel), ddx(camRel))` and view direction `normalize(-camRel)`.
- **Guard degenerate slivers.** When the squared length of the cross product is below about 1e-24, use no fade.
- **Watch the interpolator budget.** A surface shader shares `worldPos` with its lighting, but a custom `float3` costs one more interpolator. At `target 3.0` the ForwardBase pass can then exceed 10; pack it with other custom data into a `float4`.
- **Don't name a custom Input member with a `uv` prefix.** The generator treats it as a texture coordinate and fails with "cannot implicitly convert from float2 to float4".

**Verify:**
- **Positive control:** render the failing pose at 3840×2160 with no supersampling, before and after the fix. The hole pixels (and a shredded edge-on leaf) fill in, with the same image on a repeat render.
- **Regression:** render same-camera lineups near the origin. The mean absolute difference should equal the render-to-render noise floor; measured 0.24–0.48 against a noise floor of 0.24–0.53 on 0–255.

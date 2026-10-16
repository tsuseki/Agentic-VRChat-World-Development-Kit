---
title: Lighting wall art: spot geometry traps and the self-lit canvas alternative
topic: lighting-baking
tags: [picture light, spot light, wall art, cone, emission, _EmissionMap, gallery]
summary: A spot aimed at a painting's centre still puts its hot spot above the art and two overlapping cones never blend; move the light out from the wall, use one cone per work, or in a dark room make the canvas self-emissive.
---
**Trap 1: aiming at the canvas centre puts the hot spot above it.** For a light `h` above the canvas centre and `d` out from the wall, a ray at angle θ from vertical hits the wall at `y = y_light - d·cot(θ)` after travelling `L = d/sin(θ)`; irradiance ∝ `sin(θ)/L²`. Larger θ hits higher at a shorter distance, so the top of the pool is far brighter. Measured: `d` = 0.83, canvas centre 2.65 m below, 62° cone: pool peaked well above the frame, canvas centre ~6x dimmer, bottom ~31x dimmer.
- **Move the light out, don't re-aim:** axis ~30° off vertical, `d = h·tan(30°) ≈ 0.577·h`, `rotation.x = 60°`. At `d` = 1.53 the top-to-bottom ratio fell from 6x to ~3.5x.
- **Check `range`:** the painting's bottom is the farthest point; set range well past the bottom corner (measure it) or range falloff crushes the lower half.

**Trap 2: two overlapping circular cones never blend.** They make a notched double lobe with a bright lens; pulling them closer gives a heart/butterfly shape. Use **one cone per artwork**, `half-angle = atan(halfWidth / L)`, and accept the single arc above the frame. If one cone cannot cover the width, light the whole wall evenly from further back instead. A fill light with no visible fixture reads as an unmotivated blob wherever it lands; delete it.

**In a dark, moody room, use no picture light: make the canvas self-lit.** A circular pool cannot frame a rectangular canvas on a steeply raked wall (pools came out 1.42 x 1.9 m on 0.92 x 1.20 m frames, with bare wall above brighter than the art).

```csharp
m.SetTexture("_EmissionMap", m.GetTexture("_MainTex"));   // emit the IMAGE
m.SetColor("_EmissionColor", new Color(0.38f, 0.38f, 0.38f));
m.EnableKeyword("_EMISSION");
m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.BakedEmissive;
```

Setting `_EmissionColor` without `_EmissionMap` emits a flat colour and the picture disappears into a glowing rectangle. Level 0.38 reads as a lit canvas with plausible wall bounce; 0.55 reads as a lightbox. Each artwork stops costing a baked light.

**Pitfalls:** Only in genuinely dark rooms; in a daylit room a self-lit canvas reads as a TV screen.

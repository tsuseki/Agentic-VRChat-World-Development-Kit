---
title: Metallic materials render black in sealed dark rooms but are the only thing that reads against a bright probe
topic: materials-textures-shaders
tags: [metallic, Standard shader, reflection probe, night scene, albedo, energy conservation]
summary: Standard metals have no diffuse term, so whether high metallic rescues or kills a dark prop depends entirely on what the reflection probe captures.
---
**Symptom:** A brass/gold prop in a baked night interior reads near-black; raising metallic ("it's brass!") makes it worse. Conversely, a dark non-metal speaker in a glazed room facing a lit city renders darker than the floor, a pure black cutout.

**Cause:** Metals in Unity Standard get all brightness from reflected environment. In a sealed dim room the probe is nearly black → `_Metallic 1.0` is black regardless of albedo. In a room whose probe sees a bright environment (curtain wall onto a lit city, big window, fire), metallic is what catches an edge highlight; at metallic 0.0 the same 0.075 albedo reads ~0.01–0.02 sRGB, while metallic 0.85 / smoothness 0.62 reads correctly as anodised metal.

**Fix / rule** (scope: scenes already baked with probes captured; before the bake use the interim values in [metallic-materials-cannot-be-judged-before-a-bake](metallic-materials-cannot-be-judged-before-a-bake.md)):
- Sealed dark room: readable brass/gold ≈ **metallic ~0.3 + saturated warm albedo + smoothness ~0.6** — fake the metal with diffuse colour. Treat advice to raise metallic in a dim room as suspect, even from a reviewer.
- Bright probe: metallic is the fix. Ask what the probe captures first; anchor to a known-good material already reading correctly in that room.
- Energy conservation: diffuse ≈ `albedo * (1 - metallic)`. Raising metallic to 0.5 halves diffuse and can cancel an albedo lift made in the same edit. Change one at a time; decide whether the surface is carried by diffuse (bounce-lit) or reflection (facing the bright source).
- If a lighting fix "does nothing", check metallic before adding more lights.

**Verify — audit sweep:** flag materials with `metallic > 0.6` and low albedo luminance:
```csharp
float mt = m.GetFloat("_Metallic");
Color c = m.GetColor("_Color");
float albedoLum = 0.2126f*c.r + 0.7152f*c.g + 0.0722f*c.b;
```
Judge each hit — mirrors, glass and exterior mullions *should* be metallic and dark against sky. In one sweep 1 of 7 hits was a defect (gym equipment at 0.85 → fixed with ~0.28 metallic, ~0.46 smoothness, real albedo). Diagnose from a render, never the inspector.

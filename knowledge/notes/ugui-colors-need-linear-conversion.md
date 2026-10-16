---
title: Convert sRGB hex palettes with .linear for UGUI in Linear colour space
topic: audio-video-ui
tags: [ugui, linear-color-space, srgb, palette, canvas, Graphic]
summary: VRChat world projects render in Linear colour space, so UGUI colours set from sRGB hex values render lighter and less saturated unless converted with .linear at declaration.
---
**Symptom:** A UI palette lifted from a mockup, Figma or a colour picker renders noticeably lighter and less saturated - a dark parchment palette came out olive and cream.

**Cause:** The project is in Linear colour space; `Graphic.color` set from `new Color32(...)` hex values is treated as linear.

**Fix / rule:** convert once where the palette is declared:
```csharp
static Color Hex(byte r, byte g, byte b) { return ((Color)new Color32(r, g, b, 255)).linear; }
static readonly Color CPanel = Hex(0x22, 0x1a, 0x11);
```
Applies to every `Graphic` colour: `Image.color`, `Text.color`, and any colours a script assigns at runtime (enable/disable tints, state fills). Miss one and that element pops brighter than the rest.

**Pitfalls:**
- Dark colours get darker after conversion, which looks wrong at first. Don't judge against a screenshot with anything overlaying the frame (a modal tint made the fix look like the bug); close overlays, then compare.
- A runtime sweep (`foreach (var g in canvas.GetComponentsInChildren<Graphic>(true)) g.color = g.color.linear;`) is fine for an A/B in play mode but is lost on exit - put the conversion in whatever builds the canvas.

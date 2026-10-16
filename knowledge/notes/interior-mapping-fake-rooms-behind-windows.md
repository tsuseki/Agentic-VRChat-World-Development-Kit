---
title: Interior mapping fakes rooms behind windows with a shader, no geometry
topic: materials-textures-shaders
tags: [interior mapping, parallax interior, fake interiors, windows, city backdrop, shader, performance]
summary: For lit windows on distant or unreachable buildings, use an interior-mapping shader (per-pixel ray vs. regularly spaced wall/floor/ceiling planes) instead of modelling rooms; it gives perspective-correct depth for one flat quad.
sources: [https://polycount.com/discussion/204601/interior-mapping-in-spider-man-ps4, https://www.gamedeveloper.com/programming/interior-mapping-rendering-real-rooms-without-geometry, https://www.proun-game.com/Oogst3D/CODING/InteriorMapping/InteriorMapping.pdf, https://www.alanzucconi.com/2018/09/10/shader-showcase-9/, https://www.youtube.com/watch?v=L2wr7vebb6Y]
---

**Symptom / need.** A skyline, street or courtyard backdrop has buildings whose windows look flat
and dead, but modelling interiors behind every window costs geometry, materials and draw calls the
world can't afford (or the rooms are unreachable anyway).

**Technique.** Interior mapping (Joost van Dongen, 2007 thesis; CGI 2008 paper), the effect seen
behind windows in Marvel's Spider-Man (PS4), discussed on Polycount, SimCity (2013), and Unreal's
`InteriorCubeMap` material function. The building facade stays a flat mesh; the shader does it all:

- Take the view ray from the camera through the pixel; use only the part beyond the facade surface.
- Walls, floors and ceilings are infinite planes at **regular spacing** (room size), so which room
  the pixel is in and where its planes lie is a cheap `floor()` calculation.
- Of the 6 room planes, test only 3: the ceiling or the floor (by ray y-sign) and the 2 walls the ray
  faces. The closest hit wins; its hit position becomes the UV for that surface's texture
  (ceiling hit at (x,y,z) → sample (x,z)).
- Cheap: three ray–plane intersections per pixel.

Common variants: one cubemap per room type (the Unreal / "parallax interior cubemap" form);
an atlas with a per-room random index to break repetition; varying room depth; a per-room random
"lights on/off" or tint for night skylines; an extra parallax layer for a furniture/curtain card.

**Limits.** Furniture is painted onto the walls (flat up close). Rooms are boxes on a grid, so a
corner of the building can show a different room from each face, or a wall past the corner. Fine
for backdrop at distance; wrong for any room players can get close to or enter.

**From the Polycount thread.**
- It is not a baked height map with layered parallax. The shader builds a box and maps parts of a
  texture onto it. Plain UV-offset parallax gives an endless interior and bad perspective
  distortion; the ray–box version stays correct.
- Curved facades are the hard case: an arch-viz studio had to split a curved building into several
  material IDs to re-orient the mapping per segment. Prefer flat facade panels, or give each flat
  segment its own room axes.
- Further reading linked there: Alan Zucconi's Shader Showcase #9 (interior mapping examples) and an
  Insomniac technical talk on the game's tech.

**Fit for VRChat worlds.**
- Built-in Render Pipeline only: use or write a Built-in RP shader (search for "interior mapping" /
  "fake interior" Unity shaders, or port the paper's maths); URP/HDRP or Shader Graph versions
  import magenta.
- Treat as emissive backdrop: windows don't need lightmaps; keep the facade lightmapped and the
  interior term unlit/emissive so night windows glow without realtime lights.
- In VR, check from both eyes: the effect is per-pixel and stereo-correct, which is why it reads as
  real depth where a flat window photo does not.
- Quest/mobile: per-pixel cost on large facades adds up; prefer one cubemap sample and test fill rate.

**Verify.** Same-camera capture of the facade before/after from the player's real viewpoints,
including a grazing angle, then the matching stage reviewer.

**Related.** `.omp/skills/clip-planes/SKILL.md` (distant scenery and backdrops), `.omp/skills/vrchat-world-optimization/SKILL.md`.

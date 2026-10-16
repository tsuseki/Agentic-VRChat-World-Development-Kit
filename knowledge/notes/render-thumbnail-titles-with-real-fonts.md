---
title: Render world-thumbnail titles with real fonts, at one fixed layout
topic: placement-layout-design
tags: [thumbnail, world image, title, typography, Pillow, image generation, legibility]
summary: Image models drift in title size, position and font and can misspell; draw the title with Pillow and a real font, centred, block centre ~45% from top, widest row ~57% of width, light fill with glow and shadow, exported at 1200×900.
---

**Symptom:** asking an image model to "add the title" to a world thumbnail goes round after round. The text comes out edge to edge, then in the wrong corner, then in a font the owner hates, and sometimes a letter is mangled or the scene behind it changes.

**Rule:**
- **Placement:** centred horizontally, with the block's centre about 45% from the top.
- **Size:** widest row about 57% of the image width; long names go on two centred rows.
- **Legibility:** light fill on a dark scene, soft glow plus a slight shadow. It must read at thumbnail size, and the spelling must be exact.
- **Font and colour:** pick them to fit the world's theme.
- **Rendering:** use Pillow with a real font rather than an image model, which drifts in size and position and can misspell.
- **Export:** 1200×900 (4:3).
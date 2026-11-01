---
title: Render world-thumbnail titles with real fonts, at one fixed layout
topic: placement-layout-design
tags: [thumbnail, world image, title, typography, Pillow, image generation, legibility]
summary: Image models drift in title size, position and font and can misspell; draw the title with Pillow and a real font, centred, block centre ~45% from top, widest row ~57% of width, on one calm tone (light fill with glow and shadow on dark scenes, dark fill with a light glow on pale sky), exported at 1200×900.
---

**Symptom:** asking an image model to "add the title" to a world thumbnail goes round after round. The text comes out edge to edge, then in the wrong corner, then in a font the owner hates, and sometimes a letter is mangled or the scene behind it changes.

**Rule:**
- **Placement:** centred horizontally, with the block's centre about 45% from the top.
- **Size:** widest row about 57% of the image width; long names go on two centred rows.
- **Legibility:** the title sits on one calm tone, never across a mix of very dark and very bright areas (dark conifers against sky): there a navy fill vanished on the trees and a light fill's glow vanished on the sky, so move the camera instead. On a dark scene use a light fill with a soft glow plus a slight shadow; on pale sky or haze a dark fill (indigo, dark olive) with a white or ivory glow at 0.85–0.9 and no shadow. It must read at thumbnail size, and the spelling must be exact.
- **Font and colour:** pick them to fit the world's theme.
- **Rendering:** use Pillow with a real font rather than an image model, which drifts in size and position and can misspell.
- **Export:** 1200×900 (4:3).
---
title: Look at images in a contact sheet before assigning them to surfaces
topic: assets-sourcing
tags: [images, artwork, contact sheet, orientation, aspect ratio, PIL]
summary: Resolution and aspect ratio cannot tell you a photo's content is sideways; composite candidates into a labelled contact sheet and look before assigning any image.
---
**Symptom:** A replacement painting chosen because its aspect matched the frame to 0.00% shipped as a review blocker: the photo was a portrait subject captured sideways, so the frame showed a person lying on their side with the horizon running vertically. Width, height, aspect and sharpness metrics were all green.

**Cause:** Aspect ratio is invariant under a 90-degree rotation of *content* inside a correctly sized file, so no aspect test can find this.

**Fix / rule:** When choosing among N images, composite them into one labelled contact sheet (PIL: paste thumbnails on a grid, draw the asset name in each cell) and read that single image. One read replaces N and is the only step that catches orientation, mirroring, subject matter or tone.

Related: [metrics-that-cannot-see-their-defect](metrics-that-cannot-see-their-defect.md)

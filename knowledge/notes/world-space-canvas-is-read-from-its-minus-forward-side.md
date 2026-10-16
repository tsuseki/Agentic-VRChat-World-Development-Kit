---
title: Photograph a world-space Canvas from its -forward side
topic: audio-video-ui
tags: [canvas, world-space, camera, screenshots, RectTransform]
summary: A world-space Canvas is read from its -forward side, so a capture camera placed at +forward photographs its back and the geometry behind it, which looks like "the UI is not rendering".
---
**Symptom:** A screenshot of a world-space UI panel shows a plausible dark render of some other object (e.g. the plate the panel is mounted on), and you start debugging layers, culling masks and near clip.

**Cause:** A RectTransform's local +Z points **away** from the viewer (default Canvas has `forward = +Z` with its camera at -Z looking toward +Z). The intuitive `position + forward * d` lands behind the panel.

**Fix / rule:** put the camera at `panel.position - panel.forward * d`, looking along `panel.forward`. Cheap disambiguation before debugging anything else: shoot both sides in one call.

Related: [unity-quad-primitive-faces-minus-z](unity-quad-primitive-faces-minus-z.md)

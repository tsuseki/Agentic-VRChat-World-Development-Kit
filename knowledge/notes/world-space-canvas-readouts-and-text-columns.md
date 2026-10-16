---
title: World-space canvas readouts: size to the screen, two-label columns, opaque backing
topic: audio-video-ui
tags: [UGUI, world-space canvas, TextMeshPro, UdonSharp, CopyProxyToUdon, mirrored text]
summary: Size a board canvas to the visible screen not the prop bounds, align name/time columns as two labels in one rect with equal line counts, and back every Cull Off canvas with an opaque box.
---
**Rules:**
- **Size the canvas to the dark screen face, not the prop's renderer bounds.** Bounds include posts and the base pad: centre ~0.55 m low and 1.7 m too wide here, which put every row's first character under the frame. Example values: canvas 1240 × 500 units at 0.01 scale, positioned from bounds centre + face normal × 0.30 + up × 0.55.
- **Name/value columns:** two labels sharing one rect (TopLeft + TopRight alignment). Padding one string with spaces doesn't align in a proportional font, and one label per cell explodes object count. Both labels must emit the same number of lines — including blank lines for empty rows — or rows pair with the wrong value.
- If a U# script exposes `TextMeshProUGUI[]` arrays, a second readout is a wiring change; those are UGUI, so it must be a world-space Canvas, not 3D TextMeshPro. After editing proxy arrays from an editor script, call `UdonSharpEditorUtility.CopyProxyToUdon` or values never reach the UdonBehaviour.
- World-space canvases with Cull Off render mirrored from behind: give every one an **opaque backing box**. Check which side reads correctly before "fixing" a rotation — shooting from the wrong side shows mirrored text that looks like a bug.
Related: [world-space-canvas-is-read-from-its-minus-forward-side](world-space-canvas-is-read-from-its-minus-forward-side.md).

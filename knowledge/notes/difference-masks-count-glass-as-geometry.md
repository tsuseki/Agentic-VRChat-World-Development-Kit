---
title: A sky-difference geometry mask counts glass as geometry and collapses contrast metrics
topic: agent-workflow-verification
tags: [render-metrics, masks, glass, percentiles, lighting-qa, canvas]
summary: Isolating interior surfaces by differencing against a sky-only render counts window panes as geometry, so on glazed views percentiles pin to the window value and contrast metrics falsely collapse.
---
**Symptom:** On camera poses framed at windows, `p90/p50` collapses toward 1.0 and the room "has gone completely flat", although it looks fine.

**Cause:** The usual three-render mask:
```
is_geo = |full - skyonly|  > eps   # something solid is here
is_ui  = |full - nocanvas| > eps   # a canvas drew here
mask   = is_geo & ~is_ui
```
Glass tints and reflects, so it passes `is_geo`, and head-on glass renders at 0.15-0.25 linear, far above interior surfaces. The mask fills with window pixels and the upper percentiles pin to the window-sky value. It fires on exactly the poses that matter for a night scene lit through windows, and moves the metric in the same direction as the defect being hunted.

**Fix / rule:**
- Print each pose's glazing fraction and compare `is_geo` share across poses; a jump is suspect.
- Exclude glass explicitly by renderer/submesh rather than trusting the difference mask, or judge glazed poses on low percentiles only.
- UI panels need a separate `Canvas.enabled = false` pass - they are `CanvasRenderer`, not `Renderer`.

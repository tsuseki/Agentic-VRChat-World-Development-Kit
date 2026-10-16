---
title: Model window sky light as one flat emitter per opening, never geometry hugging the walls
topic: lighting-baking
tags: [bakery, area light, light mesh, window, night bake, root cause]
summary: An emitting shell sitting 0.1–0.5 m off interior walls bakes as a row of point-light pools no matter how evenly it is authored; use one flat panel filling each opening.
---
**Symptom:** A "lights off" night bake lit by an even glass-shell emitter reads as clearly point-lit: bright pools at each spot the shell nears a wall, falling off fast, warmer at the hot end. The same smooth 1/d² ramp shows up on unrelated objects (trim, plants, furniture fronts).
**Cause:** Evenness of the emitter is not evenness of the result — distance is. An emitter 0.1–0.5 m from a surface produces a 1/d² hotspot at every near-contact point.
**Fix / rule:**
- Model daylight/moonlight through a window as a distant area source: one flat emitter panel filling each opening, nothing lining the interior.
- When the same defect shape appears on unrelated objects a third time, stop fixing instances and re-examine the source. One emitter here caused six separate defects that had each been patched (objects pulled out of the trace, hand-edited atlas corrections); replacing the emitter retired all of them.
- An analytically exact retune that lands on target and still reviews as wrong means the model is wrong, not the number.

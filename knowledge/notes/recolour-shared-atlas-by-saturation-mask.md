---
title: Recolour one material class in a shared atlas with an HSV saturation mask
topic: materials-textures-shaders
tags: [atlas, recolour, hsv, texture editing, furniture, _Color tint]
summary: To retint wood in a furniture atlas without changing its fabric, mask by saturation and remap the masked mean to the target albedo's mean; a _Color tint multiplies everything.
---
**When:** A stock atlas shared by many renderers (e.g. one 4096² atlas for 38 outdoor furniture pieces) has the wrong wood tone, and `_Color` would also tint the cream cushions.
**How:**
- Classify first: convert to HSV and bin. Here wood = warm hue, s > 0.10 (64% of pixels); cushions v > 0.90, s < 0.10 (21%).
- Feathered mask over s 0.10→0.16, then remap:
```python
mask  = np.clip((s - 0.10) / 0.06, 0, 1)[..., None]
ratio = target_albedo.reshape(-1, 3).mean(0) / atlas[mask > 0.5].mean(0)
out   = atlas * (1 + mask * (ratio - 1))
```
- Masked mean went 0.716/0.607/0.499 → 0.431/0.294/0.202, matching the target teak texture; cushions untouched.
**Pitfalls:**
- Sample the atlas before trusting a colour seen in an unbaked render (the same furniture read navy in unbaked shots; no blue existed in the file).
- Count the material's users before editing — a recolour hits every room using it; clone the material if not all should change.

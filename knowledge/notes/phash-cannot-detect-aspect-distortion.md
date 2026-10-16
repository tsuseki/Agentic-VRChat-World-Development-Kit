---
title: Perceptual hashes cannot tell whether an image is stretched
topic: agent-workflow-verification
tags: [pHash, aspect ratio, texture, canvas, metrics, wall art]
summary: pHash resizes to a fixed square before hashing, so a perfect match proves shared content and nothing about stretch; test aspect by rendering square vs stretched, and size canvases from their texture aspect.
---
**Symptom:** A reviewer reports square images stretched onto 16:9 canvases. A pHash match against the 16:9 source returns Hamming distance 0, so the finding is dismissed as a false positive. The reviewer was right.

**Cause:** `phash` starts with `im.convert("L").resize((s, s))` — aspect is destroyed before any bit is computed. General rule: **a metric that normalises away dimension D can never be evidence about D.** pHash is still right for *identifying* which source a texture came from.

**Fix / rule — the test that settles it:** render the texture at 1:1 and at the frame's aspect side by side; faces/round objects decide instantly.
```python
im = Image.open("g_00.jpg").convert("RGB")   # 1024x1024 on disk
sq   = im.resize((H, H))                     # what a 1:1 quad shows
wide = im.resize((int(H*16/9), H))           # what the 16:9 quad shows
```

**Durable canvas fix:** drive each canvas from its own texture aspect, preserving the diagonal:
```csharp
float a  = (float)tex.width/tex.height;
float D  = Mathf.Sqrt(w*w + h*h);
float nh = D/Mathf.Sqrt(1f+a*a), nw = nh*a;
```
Correct for square, landscape and portrait alike.

**Pitfalls:** ProBuilder canvases' `localScale` is not world size — compute from `renderer.bounds`. Resizing can push a piece into a ceiling band or behind furniture (one grew 1.19 → 1.74 m and pierced the ceiling trim); re-audit vertical fit and obstructions afterwards. Watch NPOT import squashing too: [npot-textures-lose-aspect-and-compression](npot-textures-lose-aspect-and-compression.md).

---
title: Hash dedupe candidates through the same transform the pipeline applies
topic: agent-workflow-verification
tags: [perceptual hash, dedupe, images, pipeline, verification]
summary: Comparing a raw candidate's hash to stored, cropped/resized outputs can never match; transform the candidate exactly as the pipeline will before hashing, then re-hash all outputs.
---
**Symptom:** A perceptual-hash dedupe passes, yet the same source photo ends up stored twice under two names.
**Cause:** Stored files were centre-cropped squares; the candidate was hashed uncropped. Different framing, different hash.
**Fix / rule:** Run the candidate through the pipeline's own transform before hashing:
```python
def sq_small(p, s=64):  # identical crop to what gets written
    im = Image.open(p).convert("RGB"); w, h = im.size; m = min(w, h)
    return im.crop(((w-m)//2, (h-m)//2, (w-m)//2+m, (h-m)//2+m)).resize((s, s))
```
Generalises: whenever a dedupe key is computed on one side of a transform (crop, resample, normalise, minify) and compared against the other side, the comparison is meaningless.
**Verify:** After writing, re-hash every stored file and assert zero pairs under the threshold — that final check is what caught it.

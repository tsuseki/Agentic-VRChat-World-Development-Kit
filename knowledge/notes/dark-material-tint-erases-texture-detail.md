---
title: A very dark _Color tint erases the albedo's own detail
topic: materials-textures-shaders
tags: [_Color, tint, albedo, contrast, detail, Standard shader, OcclusionStrength]
summary: Pushing _Color low to get a dark tone multiplies away the texture's contrast; keep the dominant channel at or above about 0.25 and put real darkness in the albedo.
---
**Symptom:** A "dark timber" or "dark soil" surface renders as a featureless slab: board joints, grain and grit stop reading, and relief geometry standing proud of it (battens) also vanishes. Reviewers call it "smeared" or "low-res mesh", and it can be misdiagnosed as a texel-density problem and "fixed" with a pointless mesh swap.

**Cause:** Standard's `_Color` multiplies the albedo, scaling the texture's **contrast** along with its brightness. At `RGBA(0.150, 0.132, 0.118)` cladding whose albedo had clear board joints rendered as one flat black rectangle. A photoscan through a 0.335 multiply went to a flat wash, while the identical mesh at 0.585 read crisp. `_OcclusionStrength` belongs to the same family; it is not "just brightness".

The opposite error exists too: dark topsoil left at a sandy `0.55/0.475/0.395` read as beach sand under warm night lighting (fixed at `0.255/0.210/0.165`).

**Fix / rule:** For a textured diffuse surface keep `_Color` at or above about 0.25 in the dominant channel. Below that you are erasing, not tinting. Lifting the cladding to `0.265/0.235/0.205`, still clearly charred timber, brought the joints and battens back. If you need near-black, put the darkness into the albedo texture where local contrast survives.

**Verify:** Take a grazing-angle render. The inspector swatch, texture presence, tiling and UV density all look fine, and a head-on light hides relief further.

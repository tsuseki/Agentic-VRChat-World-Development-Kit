---
title: SetColor converts gamma to linear: brightness fits must follow the sRGB curve
topic: materials-textures-shaders
tags: [SetColor, MaterialPropertyBlock, linear color space, sRGB, gamma, luminance, binary search]
summary: In a Linear project SetColor applies the exact sRGB-to-linear curve, so rendered luminance scales as ~k^2.2 above the 0.04045 knee and linearly below it; pick the right regime and raise search ceilings since albedo can exceed 1.
---
**Symptom:** Solving for a colour scale `k` that lands a surface at a target luminance overshoots badly (a linear fit gave k = 1.398 and rendered at 1.08x the window sky, worse than the defect). Later, after dimming, the same fit "stops working" and undershoots (~0.68x when 0.80x was asked).

**Cause:** In Linear colour space `SetColor` (on `MaterialPropertyBlock` and `Material`) applies the exact sRGB transfer: `x <= 0.04045 ? x/12.92 : ((x+0.055)/1.055)^2.4`. Above the knee rendered `L ∝ k^~2.2`; below it the response is **linear**. Dim night emitters live entirely below the knee, so a fixture can switch regimes when retuned down. Inverse: `l2s(x) = x <= 0.0031308 ? 12.92*x : 1.055*x^(1/2.4) - 0.055`.

**Fix / rule:**
- Check which side of 0.04045 the value lands on before choosing the law. A power-law refit gave k = 1.178 -> 0.75x sky, correct first try. Or solve in linear via `Color.linear` and convert back.
- Two probe renders at k = 1.0 and k = 2.0 give the exponent directly: `log(L2/L1)/log 2`.
- Reading a block back with `GetVector` returns the **linear** value ((0.36, 0.372, 0.396) reads back (0.11, 0.11, 0.13)); that is correct, and both editor preview and the Udon runtime behave the same.
- **Raise the binary-search ceiling:** albedo is not capped at 1.0 (2.63, 2.22, 1.77 measured on soft furnishings). A search with `hi = 4` returned exactly 4.000 for several renderers. A solve that returns its own bound has failed; assert `result < hi`.

**Verify:** Render after applying; never trust the fit alone.

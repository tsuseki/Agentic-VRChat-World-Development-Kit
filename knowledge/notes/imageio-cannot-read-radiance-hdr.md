---
title: imageio returns raw RGBE mantissas for Radiance .hdr files
topic: lighting-baking
tags: [HDR, RGBE, Radiance, imageio, lightmap, Python, decoder]
summary: imageio.v3.imread on a Radiance .hdr returns the uint8 mantissa with the exponent dropped, so every radiance statistic is meaningless; use a real RGBE decoder.
---
**Symptom:** Analysing a Bakery lightmap (`.hdr`) in Python gives plausible-looking numbers (shape and dtype right, values 0-255, e.g. "max 255, p95 46.76") that say nothing about radiance.

**Cause:** `imageio.v3.imread("foo.hdr")` on a Radiance/RGBE file returns the raw **uint8 mantissa** with the exponent channel discarded. It is only valid for same-format A/B comparison of two files from the same encoder ("did this rebake change the atlas?"), never for absolute values, thresholds or clamping.

**Fix / rule:** Write a real decoder:
- handle **new-style RLE scanlines** (the `0x02 0x02` header per scanline, with per-channel run/literal spans) as well as flat scanlines;
- reconstruct float radiance with `value = mantissa * 2^(e - 136)`;
- re-encode with the inverse (`frexp` on the max channel).

Bakery lightmaps live in `Assets/BakeryLightmaps/*.hdr` in this format. That folder is often gitignored, so there may be no version-control fallback.

**Verify:** If an `.hdr` read gives a max of exactly 255 or any uint8-shaped distribution, stop: you are looking at mantissas. Check any HDR reader against a texel known from another path (e.g. Unity `Texture2D.GetPixels` on the imported asset).

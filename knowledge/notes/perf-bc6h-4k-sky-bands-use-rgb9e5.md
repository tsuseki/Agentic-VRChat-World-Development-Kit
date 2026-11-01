---
title: A BC6H 4K sky shows banding; give the world an RGB9E5 sky copy
topic: materials-textures-shaders
tags: [skybox, BC6H, RGB9E5, banding, HDR]
summary: BC6H banded a 4096 HDR sky in smooth gradients; a world-owned RGB9E5 copy keeps it clean and bundles only ~2.5 MB bigger, because a sky compresses well in LZ4.
---
**Symptom:** a 4096×2048 BC6H HDR sky showed visible bands in the gradient near the horizon.

**Fix / rule:** a world-owned copy imported as RGB9E5 (shared-exponent HDR, not block-compressed). Bundle cost only
~2.5 MB in the measured world because the sky compresses well in LZ4; RGBA Half (128 MB raw) bundled almost as small.
VRAM is 4 bytes per texel, so count it in the texture budget. This keeps the "visible sky is never lossy-compressed"
rule.

**Verify:** same-camera sky views before/after at native resolution; bundle-size A/B.

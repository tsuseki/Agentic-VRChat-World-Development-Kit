---
title: A bare-twig crown reads bare only when the twig atlas is pruned to the stem, main axes and a fringe at the tips
topic: materials-textures-shaders
tags: [trees, winter, bare twigs, leaf atlas, skeleton, pruning, crown fullness, shimmer]
summary: Dense generated twig fans (0.07–0.09 opaque per cell, crown sky 0.34–0.40) read as brown leaves at 10–25 m; pruning each cell's skeleton tree to the stem, an evenly spaced fraction of main axes per side and a tip fringe (0.013–0.03 opaque, sky ≥ 0.60), rebuilt from the original texels and tinted grey-brown, reads as a bare tree on the same cards.
---
**Symptom:** A winter bare-twig atlas on the summer cards looked "too full, too many branches, like brown leaves" at 10–25 m. Crown sky 0.34–0.40.

**Cause:** Generated bare sprays draw every fine twig; at card scale and distance the fine twigs merge into a brown mass.

**Fix / rule** (`scripts/twig_prune.py`):
1. Skeletonise the alpha ≥ 40 mask; BFS-walk it from the skeleton pixel nearest the cell's bottom-centre (the stem base).
2. Decompose into branches by following the heaviest subtree; side children are one order higher.
3. Keep the stem; keep the order-1 axes as an evenly spaced fraction per side of the stem by error diffusion (0.35 for upright sprays, 0.2 for a weeping-strand cell). Random or length-weighted keeps dropped whole sides of a spray.
4. Keep order-2 twigs with a probability rising toward the axis tip (0 → 0.12). Drop order ≥ 3 and spurs < 14 px (a few spurs on the outer half survive as buds).
5. Rebuild the image from the original texels within each kept skeleton pixel's radius + 1.5 px, so kept twigs are pixel-identical and no stubs remain.
6. Desaturate the twigs about 50 % toward grey-brown, ramped in from 160 px above the stem base so the card base matches the limb bark.

Target: about 0.013–0.03 opaque per cell, crown sky ≥ 0.60 (pruned: 0.62–0.65).

**Verify:** per-cell opaque before / after (the script's JSON), `crown_fullness.py` and `bare_limbs.py` with the pruned atlas on the shipped mesh, Unity crops at 10 / 15 / 25 m and under the crown, next to licensed photos of the bare species.

**Related:** the far-mip twig haze in the VR shimmer note: on a bare tree keep only a trace of it.

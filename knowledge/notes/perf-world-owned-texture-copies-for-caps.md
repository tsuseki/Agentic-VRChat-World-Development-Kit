---
title: Cap textures through world-owned copies, never by editing shared pack or source assets
topic: performance
tags: [texture caps, world-owned copies, TerrainLayer, bundle size, rollback]
summary: Make *_World texture, material and TerrainLayer copies for size caps and swaps, keep a rollback pair, cap normal and mask maps at 1024, and leave crisp-detail materials and the sky on the originals.
---
**Symptom:** size work on a world had to touch textures shared with other scenes and the source pack; one round
changed importer settings on shared assets and was reverted.

**Fix / rule:** world-owned `*_World` copies of each texture, material and TerrainLayer, swapped in with a rollback
pair. Normal and mask maps 1024; albedo stays 2048 where it carries the look; a small lantern went to 512. Keep
crisp-ridge rock materials on the originals (1024 lost the ridges) and the visible sky at its native size and format.
Measured: full-view diff ≤ 0.016 % px; close A/B at 0.75–1 m px > 18 ≤ 0.01 % and px > 6 ≤ 0.41 %; bundle
286.9 → 218.2 MB raw.

**Pitfalls:** a TerrainLayer swap is an asset edit, so a temporary in-scene A/B can't cover it: judge the ground at
the player's feet by eye and in the reviewer's pairs. Hash the shared folders before and after to prove they are
untouched.

**Verify:** same-camera close pairs per changed surface, plus the bundle A/B.

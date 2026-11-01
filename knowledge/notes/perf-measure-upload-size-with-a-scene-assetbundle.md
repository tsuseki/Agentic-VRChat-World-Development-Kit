---
title: Measure upload-size tradeoffs with a real scene AssetBundle, not estimates
topic: performance
tags: [bundle size, upload size, BuildAssetBundles, LZ4, A/B]
summary: Build the saved scene into one ChunkBased (LZ4) AssetBundle (~1 min) for every size A/B; compression estimates missed by several MB, and the SDK .vrcw came out at ~0.85x of the raw bundle.
---
**Symptom:** an agent's compression-ratio estimate for quantized vertex data missed the real bundle by several MB;
the SDK's local build once produced nothing for 22 minutes and took 508 s on another world.

**Fix / rule:** `BuildPipeline.BuildAssetBundles(outDir, [{assetBundleName, assetNames = [scene]}],
ChunkBasedCompression | ForceRebuildAssetBundle, activeBuildTarget)`, queued in one `EditorApplication.delayCall`
from a short MCP call (it blocks the editor 35–90 s), result written to a file and polled. Template:
`.omp/skills/vrchat-world-optimization/scripts/bundle_size.cs.txt`. There is no per-asset report, so change one lever per
run. Raw MB vs SDK `.vrcw`: 197.6 → 168.2 and 164.8 → 142.4 MB (≈ 0.85×); quoting raw against the 200 MB guidance is
conservative.

Measured levers in one world: lightmap atlas 8192² → 4096² with world-owned group copies 224.3 → 177.3 MB; crunched
planting atlases 58 MB (BC7) → ~15 MB; sky as RGB9E5 instead of BC6H only −2.5 MB (it compresses well in LZ4);
1.225 M merged ground-cover vertices 182.5 → 218.0 MB (48 B/vertex) or 205.0 MB (28 B), vertex-pulled 189.1 MB.

**Pitfalls:** per-asset-class bundles (one per texture class) hung for 9+ minutes on a "Moving file failed" modal;
build the whole scene only. A scene copied from another ships the source scene's lightmaps until its own bake.

**Verify:** two consecutive builds of an unchanged scene give the same size; quote each lever as a delta between runs.

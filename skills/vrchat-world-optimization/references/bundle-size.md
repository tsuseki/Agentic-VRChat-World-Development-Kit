# Upload size: measure it, then pull the levers that move it

Upload size and frame cost are separate problems; never quote one as evidence for the other. The PC guidance is
~200 MB compressed (the SDK sets no hard PC cap; mobile is capped). Crunch shrinks the download, not VRAM, and the
upload guidance is a download size, so crunch is a real lever here.

## 1. Measure with a scene AssetBundle

Estimates are not measurements: compression-ratio estimates for quantized vertex data missed by several MB, and the
SDK's own local build is slow (508 s on one world) and once produced nothing for 22 minutes.

1. Save the scene (edit mode, no `__*__` helpers, play mode off).
2. Send `../scripts/bundle_size.cs.txt` through the Unity MCP `execute_code` tool with the scene path, a scratch output
   folder outside the project and a run label. It queues one `EditorApplication.delayCall` that runs
   `BuildPipeline.BuildAssetBundles(outDir, [{assetBundleName, assetNames = [scene]}], ChunkBasedCompression |
   ForceRebuildAssetBundle, activeBuildTarget)` and returns at once. The build blocks the editor 35–90 s.
3. Poll for `<outDir>/result.txt` from the shell (`OK <MB> MB <s>s` or `ERR ...`). Never re-send while it runs.
4. Change one lever per run; there is no per-asset report in this method. For a per-asset list use VRWorld Toolkit's
   Build Report after an SDK build (texture-caps.md "Upload size").

Reading: the result is the raw LZ4 bundle. The SDK `.vrcw` has come out at ~0.85× of it (197.6 → 168.2 and
164.8 → 142.4 MB), so a raw figure under 200 MB is conservative. Say which one you quote.

Don't build one bundle per asset class to attribute size: that hung for 9+ minutes on a "Moving file failed" modal.

## 2. Levers, by measured effect

| Lever | Measured | Notes |
|---|---|---|
| Clear `BatchingStatic` on instanced LODGroup foliage | 394.8 → 168.2 MB; 396.6 → 142.4 MB (with the world's own bake); 1,595.7 → 286.9 MB raw | combined static-batch meshes live in the scene; no rebake; play-mode pixel proof |
| Lightmap atlas sized from the texels needed | 8192² → 4096² trees group: 224.3 → 177.3 MB | lightmap-allocation `reception-and-density.md` §3 |
| The world's own bake instead of a copied scene's lightmaps | copied scenes bundled at 518.8 and 396.6 MB before their own bake (and the batching fix) | the copy ships the source scene's lightmaps, including directional maps a world with empty Bakery storage doesn't even render; bake the world non-directional BC6H |
| World-owned texture copies with caps (normal/mask 1024) | 286.9 → 218.2 MB raw | texture-caps.md "World-owned copies"; keep the sky and crisp-detail materials |
| Crunch big cutout atlases (q95) | planting atlases 58 MB (BC7) → ~15 MB | texture-caps.md "Crunch" |
| Vertex-pulled cells instead of merged vertex data | merged 218.0 / 205.0 MB vs pulled 189.1 MB | merging.md "Probe-lit single-LOD clumps" |
| Clear `Mesh.isReadable` on world meshes no script reads | ~25.5 MB over 13 meshes | runtime memory as well |
| Sky BC6H → RGB9E5 | only +2.5 MB | the sky compresses well; do it for banding, not size |

Usual surprises besides these: unused TMP fonts, an oversize skybox HDRI, and inactive objects that still ship (only
`EditorOnly` strips).

# Texture delivery and residency decisions

An incremental adaptation of sechiro's texture/VRAM guide, not another world-performance or image-downloader implementation guide.

First read `.omp/skills/unity-vrc-world-sdk-3/SKILL.md` and its `references/performance.md` for platform constraints and existing texture recommendations. For download APIs, cleanup, cache lifetimes and crossfades, use `.omp/skills/unity-vrc-udon-sharp/SKILL.md` and its `references/web-loading.md` / `references/image-loading-vram.md`. No lifecycle code is copied here.

## Choose the representation before tuning compression

Determine the actual bottleneck and record the conditions: bundle/download bytes, resident GPU memory, CPU-readable copies, decode/upload spikes and visual quality are different measurements.

1. Decide the needed apparent resolution at the closest supported viewing distance. Reducing unnecessary source dimensions can outperform a format change; do not sacrifice required text readability by applying a blanket size cap.
2. For fixed images, first consider platform-compressed bundled textures. For genuinely changeable content without reupload, evaluate runtime delivery under the existing downloader guidance.
3. Count **simultaneously resident** images, including transition overlap, caches and pending downloads, rather than comparing just the total number of source files.
4. Inspect the actual platform import result. Keep existing project/SDK platform overrides; do not replace a deliberate ASTC setup with upstream's generic `Automatic` recommendation. Where no specific policy exists, inspect Automatic's selected format before adding overrides.
5. Change one factor and measure on the supported client/device. A smaller PNG/JPEG on disk is not evidence of lower VRAM.

## Import decisions that affect the tradeoff

- Keep `Read/Write Enabled` off unless an actual CPU pixel-access requirement needs it. A readable copy adds CPU-side memory; it does not mean a second GPU image. Verify such consumers before switching it off.
- Remove unnecessary alpha only when it is not used by transparency, masks or shader data. Preserve texture semantics, color-space and normal-map handling.
- PC BC7 and DXT5/BC3 are both 8 bits per pixel. BC7 can improve quality, but is not a memory reduction over BC3 at equal dimensions/mips. Opaque BC1/DXT1 is 4 bits per pixel where the quality/alpha needs permit it.
- The World SDK skill owns Android/Quest ASTC recommendations. Evaluate larger blocks on fine text and thin lines at actual viewing distances; do not treat their smaller nominal footprint as a free quality improvement.
- **Crunch targets delivery/disk size, not resident GPU size.** It decompresses to the underlying GPU format. Do not enable it as a VRAM fix or assume its ratio is constant across images. Recheck current VRChat Android guidance and compatibility before adopting it.
- Verify device support: unsupported compressed formats can expand to a larger fallback at runtime. Importer labels and source byte counts alone do not prove the resident format.

These distinctions follow Unity's supported-formats/bpp tables and Texture Import Settings (2022.3).

## Footprint arithmetic, not a profiler replacement

For an uncompressed base image, estimate `width * height * GPU_bits_per_pixel / 8`. For block compression, round each dimension up to whole blocks and multiply the block count by block bytes. Sum separately for each mip; a full chain on a large square texture is approximately 4/3 of base size. Use MiB (`bytes / 1,048,576`), not ambiguous MB.

Examples for a 2048 x 2048 base level, excluding mips and overhead:

| Resident format | Approximate base footprint |
|---|---:|
| RGBA32 | 16 MiB |
| BC1/DXT1 | 2 MiB |
| BC3/DXT5 or BC7 | 4 MiB |
| ASTC 6x6 | 1.785 MiB (342 x 342 blocks, 16 bytes per block) |

**Correction to the source guide:** do not promise RGB24 consumes only 24 GPU bits per pixel. Unity's 2022.3 format table explicitly describes RGB24 as 24 bits on disk but converted to RGBA32 for the GPU. Inspect the actual platform result and memory. The upstream example comparing one 1080p RGB24 image to seven resident BC1 images is therefore not retained as a universal break-even threshold.

A bounded set of uncompressed downloaded images can still use less memory than a much larger fully resident set of bundled compressed images. The reverse can also hold. Include transition peaks, effective GPU format, cleanup behavior, mip residency and redownload cost in that comparison. Do not assume every bundled mip is resident, or that an API call has freed GPU memory without observing it. Follow the authoritative Udon lifecycle reference and verify against the installed SDK when changing cleanup.

## World Space UI is not automatically mip-free UI

Decide from how the image is seen, not from whether it is a Canvas or a mesh:

- Posters, walls, display panels and World Space UI viewed from varying distance/angles generally benefit from mipmaps for reduced shimmer and better texture sampling.
- A strictly near-view interface rendered near its designed pixel density may justify disabling mipmaps, but inspect it in VR, Desktop and at reachable distances first. Do not disable all World Space UI mipmaps by category.
- A full mip chain increases total stored texture data, but streaming can reduce the subset actually resident. Disabling mips to save the nominal one-third can remove that opportunity.
- Sampling a coarser mip and evicting unused mips are separate mechanisms. Mip bias alone does not prove that memory was released.

The VRChat 2024.4.2 release documents mipmap streaming for worlds/avatars, dynamic available-shared-memory budgets on Android/Quest and a PC budget set at load. It also says world texture priorities are retained whereas avatar priorities are treated as zero. These are dated release facts, not a promise of a fixed current memory budget or savings percentage; verify current client behavior for the target.

Unity's Mipmap Streaming documentation explains residency management. Its demo-project percentage savings are not a VRChat-world guarantee. Do not increase every texture's priority to force maximum detail; measure the important image and the rest of the scene together.

### DPID is a quality decision

The pinned sechiro guide reports DPID's SDK 3.7.1 beta/opt-in introduction and a Kaiser-filter association. That is historical upstream research, not current verified setup guidance. The directly reviewed client 2024.4.2 notes document DPID re-enabling and improved sharpness for `AlphaIsTransparency` textures. Do not infer current SDK opt-in/default or beta status from those older notes. Check installed SDK settings and current official documentation before changing them; DPID sharpness improvements are not a direct VRAM-reduction mechanism.

## Evidence for accepting a texture change

At the authorized verification point, compare before/after with the same device, camera/viewing distance, content set and transition path:

- Actual imported platform format/dimensions and readable/mip settings.
- Built/download size separately from steady-state and peak resident memory.
- Readability, transparency edges, compression artifacts and distant shimmer in the actual display surface.
- For downloaded content, repeat switches and revisit prior images using the authoritative cleanup/cache implementation; check that residency stays bounded and network behavior remains acceptable.
- Record what was measured and what remains an estimate. Texture/material visual changes still need the workspace stage-reviewer gate (`dressing-reviewer` before the bake, `final-reviewer` after it); a memory reduction does not waive visual acceptance.

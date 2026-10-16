---
title: Generate 360° skyboxes locally with FLUX: seam fix last, upscale, HDR boost
topic: assets-sourcing
tags: [skybox, FLUX, ComfyUI, equirectangular, panorama, seam, HDR, EXR]
summary: Text-to-image at 2048×1024 with a 360 LoRA, then a rolled-strip inpaint to fix the wrap seam as the very last generative step, upscale, and inverse-tonemap highlights into a half-float EXR.
---
**Setup (ComfyUI):** FLUX.1-dev Q8 GGUF (12.7 GB; full bf16 at 23.8 GB doesn't fit a 24 GB card under WDDM) via the `ComfyUI-GGUF` custom node; an equirectangular-360 LoRA (trigger "equirectangular 360 degree panorama"). Headless server needs `comfyui-frontend-package` installed or it exits.

**Pipeline:**
1. t2i 2048×1024, LoRA strength 1.0, euler/simple 28 steps, FluxGuidance 3.5, cfg 1.0 (~1.5 min).
2. Seam metric: mean abs diff of the two edge columns vs an interior adjacent-column baseline (~4). Raw generations ~25 = visible seam.
3. Seam fix: roll 50 %, `SetLatentNoiseMask` strip (160 px at 2K / 320 px at 4K), denoise 0.55, roll back.
4. Upscale: Lanczos 2× + whole-image img2img at denoise 0.30 → 4096×2048 (re-synthesizes mushy detail into crisp edges rather than sharpening). Optional ESRGAN 2× to 8192 so a 2048 cube face downsamples.
5. **Every img2img pass re-breaks the wrap seam** — the rolled-strip inpaint must be the last generative step (ESRGAN only nudges it).
6. HDR: sRGB → linear, inverse-tonemap boost on highlights (up to 4×), write half-float EXR (Python `OpenEXR`).

**Unity import:** an 8192-wide EXR with `maxTextureSize 2048` gives the sharpest face; the reimport can exceed a 30 s MCP timeout while succeeding — poll, don't retry.

**Pitfalls:**
- FLUX negatives are inert at cfg 1.0; cfg must be > 1 for a negative prompt to do anything.
- Structure-preserving img2img of a watermarked reference keeps the watermark (it is structure); use tags-only text-to-image from a captioned reference instead, or a licensed original.
- Slow sampling (88 s/step vs 4 s) with the GPU at 99 % util but half power and ~7 % memory util = weights paging from host RAM under commit exhaustion (async weight offload). Check free commit (`Win32_OperatingSystem.FreeVirtualMemory`) and close Unity editors before generating; stop the server before baking (it holds > 14 GB VRAM).

See [night-sky-grading-for-generated-panoramas](night-sky-grading-for-generated-panoramas.md).

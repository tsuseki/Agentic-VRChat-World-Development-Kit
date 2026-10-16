---
title: GLIM: a free Vulkan GPU lightmapper that runs on AMD as well as NVIDIA
topic: lighting-baking
tags: [lightmapper, GLIM, Vulkan, AMD, Bakery, OptiX, VRCLightVolumes]
summary: Bakery requires NVIDIA OptiX, but GLIM (github.com/z3y/glim) is a free, open-source drop-in replacement for Unity's built-in lightmapper using Vulkan ray queries, so the NVIDIA lock is not inescapable.
sources: [https://github.com/z3y/glim, https://github.com/z3y/glim/releases, https://github.com/z3y/glim/issues]
---
**When:** Choosing a lightmapper, or a contributor has a non-NVIDIA GPU and Bakery (CUDA/OptiX) isn't an option.

**What it is:** <https://github.com/z3y/glim> by z3y — free, open source, drop-in replacement for Unity's built-in lightmapper.
- Backend is Vulkan `VK_KHR_ray_query`, not CUDA/OptiX, plus a software CWBVH fallback for GPUs without hardware RT.
- README lists Windows and Linux, NVIDIA and AMD GPUs. Intel Arc is unlisted — "probably works, untested" (the software fallback covers missing ray_query).
- Ships realtime preview, denoising, seam stitching, UV packing and VRCLightVolumes support.
- Author's caveat: early stage, may lack features. Treat as promising, not production-proven.

**Pitfalls:** migrating an existing Bakery scene is real work — Bakery light groups, `BakeryLightMesh` emitters and similar config do not port. Evaluate it off the critical path, not mid-deadline.
- As of v0.8.0 (2026-10-11; releases land roughly weekly, install via VCC listing `z3y.github.io/vpm-package-listing`): hand-authored LOD groups lightmap only LOD0 (lower LODs fall back to probes; importer-generated LODs share UVs and work, glim#18); bake crash in the AMD Vulkan driver on RDNA1's software path is open (glim#20); it has broken against VRC Light Volumes 3.x once (glim#13). Pin a version per project.

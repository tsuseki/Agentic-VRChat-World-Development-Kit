---
title: GLIM bounces black off the back of two-sided leaf cards; a two-shader patch fixes it
topic: lighting-baking
tags: [GLIM, double sided GI, foliage, alpha cutout, Progressive, Bakery, backface GI, lightmapper comparison]
summary: GLIM 0.11.0 ignores Double Sided GI in its lightmap bounce pass, so every bounce ray that hits a leaf card from behind returns black and tree crowns bake about 40 % darker than Progressive; patching two Slang shaders to bounce the front-side value fixes part of it and leaves single-sided bakes byte-identical.
sources: [https://github.com/z3y/glim, https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Material-doubleSidedGI.html]
---
**When:** baking foliage (two-sided alpha-cutout cards) with GLIM, or choosing a lightmapper for tree-heavy outdoor scenes.

**Symptom:** test on a 40 × 65 m garden chunk with 372 renderers. All bakers had the same sun and the same SH-matched sky, and Double Sided GI was on in every foliage material.
- Under a weeping cherry, crown-interior luminance was 0.077 with stock GLIM 0.11.0 and 0.131 with Progressive GPU (−42 %).
- Cards facing away from the light came out khaki instead of pink.

**Cause:**
- GLIM passes `Material.doubleSidedGI` to the tracer, and its probe, emission and preview paths honour it.
- In `bake_indirect.slang`, any back-face hit sets the bounce to black. The check is commented out upstream, and the comment says the cached bounce stores only the front side.
- In `adjust_samples.slang`, a back face within one texel is treated as the inside of a solid and the sample is moved onto it.
- Shadow rays and alpha cutout already work on both sides.

**What the other bakers do:**
- Unity documents that Double Sided GI back faces "get treated as valid when seen from other objects" and "bounce light using the same emission and albedo as frontfaces".
- Bakery has no per-material flag, only a global *Backface GI* weight from 0 (black, the default) to 1 (same as the front face).
- Neither lights one texel from both hemispheres.

**Fix / rule:**
- GLIM is open source (Rust plus Slang). Patch, don't decompile. Gated on the material flag:
  - the indirect pass bounces the front texel × albedo on a back-face hit;
  - sample adjustment ignores Double Sided GI back faces.
- Build with `cargo build --release` and Slang `2026.13.1`, the version upstream's release workflow pins.
- A native plugin stays loaded until the editor quits, so swapping `glim.dll` needs an editor restart.
- Keep the fork embedded under the same package name (GLIM hard-codes `Packages/io.github.z3y.glim/...`) and drop it from `vpm-manifest.json`.
- Upstream's `Editor/.gitignore` lists `glim.dll`; remove that line, or the project repo silently commits a package without its binary.

**Verify:**
- Plain-wall control: two stock bakes and one patched bake (denoise off) gave a byte-identical `Lightmap-0_Diffuse.exr`.
- Positive control, the same chunk and settings: crown 0.077 → 0.093 (+22 %), shrubs and bamboo almost unchanged.
- At 4096 with 5 bounces it reached 0.098, still about 25 % under Progressive.
- Unresolved in that scene: a shaded plaster wall baked at about 0.53× Progressive's brightness in every GLIM variant (bounces, directional encoding and density ruled out).

**Pitfalls:**
- GLIM reads only the skybox for ambient and ignores Trilight and Color ambient. Bake every lightmapper with the same sky cubemap when comparing them.
- GLIM leaves out of its scene any renderer that is ContributeGI but receives GI from probes; a Discard group is the workaround.
- GLIM stops on a modal "Remove bakery script" dialog while Bakery's `!ftraceLightmaps` object exists, which happens just from having the Bakery window open. Close the window first.
- GLIM's internal probe pass calls Unity's `SaveCurrentModifiedScenesIfUserWantsTo`. Save the scene before every scripted bake, or a "Scene(s) Have Been Modified" dialog blocks it.

**Related:** [glim-vendor-portable-gpu-lightmapper.md](glim-vendor-portable-gpu-lightmapper.md), [bakery-unwrap-registry-rewrites-shared-models.md](bakery-unwrap-registry-rewrites-shared-models.md).

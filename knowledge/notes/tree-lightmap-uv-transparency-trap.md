---
title: Area-weighted lightmap unwraps starve tree bark because alpha-cut leaf cards count as full quads
topic: geometry-meshes-uvs
tags: [lightmap UV, UV2, Smart UV Project, trees, leaf cards, alpha cutout, bark, texel density, FBX]
summary: An automatic lightmap unwrap sizes charts by 3D surface area and ignores transparency, so thousands of mostly see-through leaf quads take the lightmap and thin bark limbs get about one texel each; ship a hand-built lightmap UV in the FBX that gives bark its own budget.
---

**Symptom.** In a baked scene, a tree's limbs are lit unlike the trunk they grow from: some limbs come out evenly
near-black, others evenly bright, along their whole length. A hard light/dark line shows exactly at each fork.
It is common across species and worse on near-camera trees.

**Cause: the transparency trap.**
- Blender Smart UV Project, Unity "Generate Lightmap UVs" and similar unwraps scale every chart by its
  **3D surface area**. They know nothing about the material's alpha.
- A leaf card is a full quad, transparent corners included, and a crown has thousands of them. The unwrap
  therefore treats the crown as almost all surface: bark measured **~3 % of the area** on an olive-type tree.
- Bark is thin tubes, and Smart UV also cuts every face of a 4-sided tube into its own chart (190 bark
  charts on one tree).
- Result: ~92–96 % of bark charts are under 4 lightmap texels wide (median ~1 texel, 10th percentile
  0.1). A 1-texel limb holds one irradiance sample. Whatever lands there (crown shadow or sun) fills the whole
  limb, unrelated to the trunk beside it. Measured on a baked lightmap, thin-stem vs adjacent-trunk luminance
  ratio p10/p50/p90 ranged from 0.02/0.27/1.4 to 0.11/1.08/5.1.
- The unwrap also leaves the 0–1 square only ~10 % full.
- The fork line is a chart border (limb and parent are separate charts) where the two sides land on
  different samples. It isn't fixable by stitching. It goes away once both sides have enough texels to
  resolve the same light.

**Fix / rule.**
- Ship a **hand-built lightmap UV in the FBX** (channel 1, named `Lightmap`; channel 0 `UVMap` for the
  texture). Never rely on an engine setting: the engine can't store a per-asset lightmap scale in the file,
  and its auto-unwrap reproduces the trap. Keep the importer's "Generate Lightmap UVs" off, and say so in the
  buyer readme.
- Build the UV by allocation, not by area:
  - **one chart per limb chain:** a single ribbon, no seams between the tube's faces;
  - **uniform bark density:** the same texels per m² of bark on every limb, weighted well above the
    leaves (start at 5× linear);
  - **leaf cards** keep their charts and shrink to pay for it. Leaves flicker and scatter light, so they
    tolerate coarse lightmaps;
  - **shelf-pack** into the unit square with one uniform scale found by bisection;
  - **margins** sized for the texel sizes buyers bake at (0.010 here; 0.002 bled neighbour charts into
    every leaf rim).
- Choose the bark weight **per tree** by a rule. Target: the thinnest visible limb gets ≥ 2 texels around
  its circumference and trunks get ≥ 8 at a stated reference resolution, with the asset's lightmap scale left
  at 1. Engines size an instance's lightmap rect from world area vs UV area. Moving share from leaves (~97 %
  of the area) to bark is enough for most trees, with no extra lightmap memory.
- A UV-space "bark ×N" figure is not a texel gain: raising total fill shrinks every texel. Normalise by
  √(fill_after / fill_before). Example: ×8.5 in UV space at fill 0.10 → 0.49 is ≈ ×3.8 in texels, leaves ≈ ×0.76.
- Make this the pack step's default for new trees; an automatic area-weighted unwrap must never ship.

**Verify.**
- Re-read the exported FBX: channel names and order; the lightmap UV present, inside 0–1, zero overlap
  between charts (rasterise at 2048²); only UV1 differs from the previous export (positions, UV0, vertex
  colours, normals, topology unchanged).
- Isolated test bake per tree (ground plane, low-angle baked sun plus sky, 5 and 10 texels/unit) and the
  real scene. Same-camera before/after crops at forks; measure the luminance step across each fork and the
  limb/trunk ratio.
- Positive control: the old area-weighted UV on the same camera and bake must show the dark/bright limbs.

**Pitfalls.**
- The re-pack script edits the source `.blend` in place and is not idempotent. Restore the `.blend` from
  version control before re-running, or the second pass re-weights already re-weighted bark.
- Raising the scene's lightmap scale alone multiplies the leaf share too; it costs memory and still leaves
  bark under-allocated.

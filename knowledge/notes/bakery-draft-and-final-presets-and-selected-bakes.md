---
title: Bakery iteration: DRAFT/FINAL presets, selected-group bakes, and what forces a full render
topic: lighting-baking
tags: [Bakery, draft bake, presets, selectedOnly, GI samples, sampleDivisor, iteration]
summary: A low-texel DRAFT preset baked 6 groups in 95 s vs ~22 min at FINAL; selected-group bakes are refused after any geometry or preset change, and GI sample cost is quadratic.
---
**How:**
- Keep two presets (Bakery `ftSettingsAsset`, usable in its Experimental "Presets" foldout). Example FINAL: GI 96, bounces 4, texels/unit 20, maxAutoRes 4096, AO 0.45 / 0.5 × 32, fixSeams on. DRAFT: same but GI 16, texels/unit 5, maxAutoRes 1024, AO × 8, fixSeams off. **Keep bounces equal** — bounce count changes how bright a sealed room bakes, and brightness is what a test bake is for. Measured: 6-group DRAFT 95 s vs ~22 min FINAL. A large outdoor scene's low-res test (GI 8 / 1 bounce / no denoise / no AO, groups 1024/512) took ~3 min — always run it first.
- Applying a preset by script: copy fields into the scene's `ftLightmapsStorage` (`!ftraceLightmaps`), null `renderSettingsAsset` so the window stays editable, then `LoadRenderSettings()` on every open Bakery window (that pushes `texelsPerUnit` / `maxAutoResolution`).
- GI sample cost is **quadratic**: samples = √rays (32 → 1024 rays, 64 → 4096). Bakery warns above 64; that's a nudge, not an error.
- Lighter inner loop: **Samples Multiplier** (`ftRenderLightmap.sampleDivisor`, UI "1/N") scales GI and light samples only and does not force a rebuild, so per-group bakes keep working. Reset to 1 before the final; it doesn't survive a domain reload.
- Unchecking *Export Geometry and Maps* when geometry is unchanged skips the ~40 s export.

**Selected-group bakes (`selectedOnly`):**
- Selected objects' groups re-render; other groups contribute GI only if their `<group>_final.hdr` exists. **Light probes are skipped** — run a separate probe pass.
- **Refused after any geometry/layout edit** ("Scene geometry/layout changed since last full bake") and after a preset switch that changes atlas resolution. It aborts ~40 s in, cleanly (bindings intact): clear the progress bar, reset `userCanceled`, relaunch as a full render with empty selection. Batch all geometry edits before choosing the bake path.
- Group name = output file name, so a DRAFT bake overwrites the shipped `_final.hdr`; re-bake at FINAL before publishing. Separate output paths are worse (the scene rebinds to whatever baked last).

See [bakery-scripted-bake-recipe](bakery-scripted-bake-recipe.md) for launching from code.

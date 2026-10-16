# bakery-light-baking

A diagnosis and automation skill for Unity + Bakery lightmap baking in VRChat worlds. It covers the full workflow for the most common baked-lighting artifacts — red/green chroma blobs on dim interiors (GI samples too low, smeared by the denoiser), blue sheen from stale/NULL reflection probes, silently-failing light probe bakes, and washed-out bakes caused by leftover realtime helper lights — plus verified reflection-based recipes for firing Bakery bakes, selective rebakes, and probe renders entirely from editor scripts (usable via Unity MCP or any editor scripting context).

## Installation

This copy ships with the kit in `<workspace>/.omp/skills/`. To use it elsewhere, copy the folder
into your agent host's skills folder for that project or for all projects.

## When to use

- A Bakery bake looks blotchy, noisy, or discolored (especially red/green blobs in dim rooms)
- Glossy surfaces show an unexplained blue sheen after a rebake
- Dynamic objects render near-black despite baked light probes
- The whole scene looks flat/washed out after baking
- You want to automate full or selective Bakery bakes and probe renders from script
- Iterating on lighting is too slow and you want a fast draft-quality test bake before the full-res one

## Contents

- `SKILL.md` — quick-reference table, diagnostic order, scripted-bake recipe, two-stage draft/final workflow, non-obvious manual behaviour, trade-offs, edge cases
- `reference/examples.md` — complete copy-pasteable C# editor snippets and debug sequences

## Credits / source

See [SOURCES.md](SOURCES.md).

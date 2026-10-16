---
title: SetPropertyBlock replaces the whole block and covers every submesh
topic: materials-textures-shaders
tags: [materialpropertyblock, SetPropertyBlock, submesh, lighting-states, runtime-tint]
summary: A MaterialPropertyBlock replaces the renderer block rather than merging, so a renderer in two passes keeps only the last, and one per-renderer block hits every submesh, so solving against sharedMaterial moves the wrong element.
---
**Symptom:** (1) In a lights-off switch, soft furnishings in two lists got their emission back. (2) A darkening solve made a two-material bed **brighter** (0.0563 -> 0.0633).

**Cause:**
1. `SetPropertyBlock` **replaces**. Two passes each applying a block to the same renderer: only the last survives. The emission-off pass ran first, the albedo pass second, so emission came back.
2. **One block covers all submeshes.** A per-renderer block overrides `_Color` on every material, while a solve against `sharedMaterial` (= submesh 0) tunes only one of them. The tell is a wrong-direction result.

**Fix / rule:**
- Make the shared block carry every property all passes need:
```csharp
_albBlock.SetColor("_Color", albedoNightColor);
_albBlock.SetColor("_EmissionColor", Color.black);   // because this pass runs last
```
- To target one submesh: `renderer.SetPropertyBlock(block, submeshIndex)`; clear with `SetPropertyBlock(null, submeshIndex)`. If one block must cover a multi-material renderer, the value is a weighted compromise - record it as such.
- Before wiring a renderer into any block-driven pass, check (a) is it already in another list, (b) how many materials it has, (c) `HasPropertyBlock()` in the base state.

Related: [dont-clobber-existing-material-property-blocks](dont-clobber-existing-material-property-blocks.md), [removing-a-renderer-from-a-toggle-list-leaks-state](removing-a-renderer-from-a-toggle-list-leaks-state.md)

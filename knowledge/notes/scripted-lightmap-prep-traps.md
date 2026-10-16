---
title: Scripted lightmap prep: read flags back after rebuild, stable selector roots, and the right UV2 source
topic: lighting-baking
tags: [lightmap, static flags, contributeGI, uv2, bakery selector, procedural geometry, probuilder]
summary: Builder scripts silently undo static flags or destroy Bakery selectors; read every flag back after a full rebuild, and choose UV2 from the generator before reaching for the unwrapper.
---
**Symptom:** A long bake produces no lightmap for generated geometry, with no error.
**Cause / rules:**
1. **A late site-wide pass undoes the flags.** A builder's finalize step that forces objects dynamic reverts prep run earlier; `scaleInLightmap` survives while `ContributeGI` reads 0, so it looks done. Run prep after any finalize pass and read every flag back off the renderers after a full rebuild — never report success because the write executed.
2. **Bakery selectors must sit on a rebuild-stable root.** Builders that `DestroyImmediate` and recreate their root destroy the selector, silently dropping geometry from the bake. Use a find-or-create parent and prove stability by instance ID across a rebuild.
3. `scaleInLightmap` / `receiveGI` / `staticShadowCaster` are on `MeshRenderer`, not `Renderer` (CS1061 off a base-class reference). `m_StaticShadowCaster` may still need `SerializedObject`.
4. ProBuilder `ToMesh()` invalidates UV2 — rebake after mesh edits.
5. **Pre-bake sweep: no Contribute GI on mirrors or video screens.** Clear `StaticEditorFlags.ContributeGI` on every renderer that has a `VRCMirrorReflection` or a video-screen material. With Progressive GPU such a mirror made the bake loop 0 → 99 % → 0 forever (Unity 2022.3.22f1, <https://ask.vrchat.com/t/help-lightmap-bake-is-not-working-correctly/27527>, 2024); with Bakery the screen bakes as a coloured area light (see bakery-chroma-patches-atlas-starvation-recipe).
**UV2 choice:**
- If a procedural generator computes chart coordinates directly (uv0 bijective in local space), `uv2 = uv0` is correct and `Unwrapping.GenerateSecondaryUVSet` is worse (adds seams along curvature).
- Use the unwrapper when uv0 is invalid as a layout: tiling triplanar/world-space projections, spherical atan2 wraps, photoscan atlases outside [0,1]. World-space uv0 is the subtle case — bijective but in the thousands and shared across instances; author a planar chart over LOCAL bounds instead.
- Two-sided generated shells: pack front and back into separate V ranges, never mirrored, or lit top and shaded underside average together.
- A shell sharing another mesh's vertex array should inherit its finished uv2.
**Verify density:** effective area = `worldArea × scaleInLightmap²` per site as a fraction of the atlas. LOD1/LOD2 renderers each need their own chart (16% of one site's budget for distance-only geometry) — discount (~0.35/0.2) or exclude them.

---
title: Traps when validating lighting by sweeping rendered pixels
topic: agent-workflow-verification
tags: [render-metrics, pixel-sweep, lighting-qa, attribution, canvas, luminance]
summary: Judging whether surfaces read as lit from rendered pixels works only if you gate on two conditions, compute stats over whole objects, ignore max on soft furnishings, hide canvases explicitly, frame the flagged area, and attribute by renderer toggle.
---
**When:** Validating a lighting state (e.g. "nothing should still read as lit in lights-off mode") from captured frames.

**Pitfalls:**
1. **Gate on two conditions, never one.** E.g. `luminance > skyReference (0.035 linear) && r/b > 0.75`. Brightness alone flags the windows (glazing reads 5-7x the sky p95); hue alone flags every dark brown prop.
2. **A hue-masked mean is selection bias.** Masking to `r/b > 0.8` then averaging r/b returns "warm" for every object with any warm pixel (a beanbag read 1.19 that way; over all its pixels it was 0.32, cool). Mask to attribute if you like; compute object statistics over all its pixels.
3. **Per-pixel max is not a defect signal on creased soft furnishings** - specular on bedding peaks 3-6x the sky reference on accepted surfaces. Judge mean and hue; max only means something on flat surfaces.
4. **UI is `Canvas`/`CanvasRenderer`, not `Renderer`.** Hiding renderers leaves a lit screen contributing thousands of hot pixels; disable the `Canvas` components.
5. **The residual is bounded by where you pointed the camera.** A sweep reported 111 px while a 4,557 px blowout sat in a corner no pose looked at. When a reviewer flags an area, add a pose that frames it before quoting a number.
6. **Attribute by renderer-ownership toggle, then ray-triangle for the submesh.** `Physics.Raycast` returns collider proxies, not visible meshes; scoring by authored albedo misses renderers re-tinted by property blocks; a multi-submesh renderer's `sharedMaterial` is only submesh 0. Disable one renderer at a time, count flagged pixels that change, then Moller-Trumbore the flagged rays against that renderer's mesh for submesh + world position.
7. **Passing the absolute gate is necessary, not sufficient - compare to the surface it abuts.** Cove trim under every threshold was still called "a concealed strip light": it was 1.6-2.0x the luminance of the ceiling it touched (r/b 0.62 vs 0.37). For long thin members, add the ratio to the bordering surface (~1.2x reads as trim, ~2x reads as a fixture).

**Never** attribute hot pixels by toggling `enabled` over every renderer in the scene: ~900 renderers x 3 poses x (render + `GetPixels`) locked the editor for 10+ minutes and every tool call timed out. Subtract canvases first, then scope the loop to one room.

Related: [toggle-diff-and-mask-pass-attribute-pixels](toggle-diff-and-mask-pass-attribute-pixels.md), [difference-masks-count-glass-as-geometry](difference-masks-count-glass-as-geometry.md)

**Report:** "pixels above both thresholds, excluding the deliberate exceptions, over N poses" - a number a later session can reproduce.

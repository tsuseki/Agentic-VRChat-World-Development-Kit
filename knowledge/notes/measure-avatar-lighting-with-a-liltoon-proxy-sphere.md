---
title: Measure avatar lighting with a lilToon proxy sphere — light volumes only respond in play mode
topic: probes-reflection-and-light
tags: [avatar lighting, lilToon, VRC Light Volumes, proxy, play mode, measurement]
summary: Frame-diff a ~0.35 m lilToon sphere at each player pose; a Standard sphere has no light-volume path, and even lilToon reads no volumes in edit mode.
---
**How:** place a ~0.35 m sphere at each canonical player pose, 1.2 m along the look direction. Render with the sphere enabled, then disabled, and diff the frames to isolate exactly its pixels. Report mean linear luminance and `r/b`.

**Rules:**
- **Use lilToon, not Standard.** lilToon has real avatar behaviour (`lightMinLimit`, default 0.05, the floor that stops avatars going black) and the VRC Light Volumes path. A Standard ball has **no** light-volume path and silently reports probe lighting.
- **Light volumes read nothing in edit mode.** `LightVolumeManager` is an UdonSharpBehaviour, so the `_UdonLightVolume*` shader globals are pushed only by the Udon VM in **play mode**. In edit mode shaders fall back to probes, and a day/night sweep returns identical values — which looks like "the toggle does nothing".
- Edit-mode readings are still valid for probe-lit states. A volume at `Intensity 0` is excluded by `UpdateVolumes()`, so that state falls back to probes by design.

**Verify:** before quoting day-vs-night avatar numbers, confirm the two states differ; matching to 3 decimals means the measurement path isn't seeing the volume. See [vrc-light-volumes-traps](vrc-light-volumes-traps.md).

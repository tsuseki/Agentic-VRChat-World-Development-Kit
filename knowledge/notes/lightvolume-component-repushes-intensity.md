---
title: The LightVolume authoring component keeps re-pushing its Intensity to the instance
topic: probes-reflection-and-light
tags: [vrc-light-volumes, ExecuteAlways, intensity, lighting-states, udonsharp]
summary: VRC Light Volumes LightVolume is ExecuteAlways and re-copies its Intensity into the LightVolumeInstance on update, so setting the instance alone silently reverts; set both and treat the authoring component as source of truth.
---
**Symptom:** You set `Intensity = 0` on a `LightVolumeInstance` to park a volume, read it back as 0, and moments later it is back at 1 and the volume ships enabled. (LV 2.x only — the authoring component no longer exists after the 3.0 migration; see the version scope in vrc-light-volumes-traps.)

**Cause:** In `red.sim.lightvolumes`, `LightVolume.cs` is `[ExecuteAlways]`; its `SyncUdonScript()` copies the authoring fields (Intensity included) into the `LightVolumeInstance` (the UdonBehaviour in play mode, the proxy in edit mode). It fires from `Update()` on any transform change or when validated. The revert happens on the next editor update, so the write looks successful.

**Fix / rule:**
- Set **both** the authoring `LightVolume.Intensity` and the instance; the authoring value is the source of truth.
- `LightVolumeManager.UpdateVolumes()` skips any volume unless `activeInHierarchy && Intensity != 0 && Color != Color.black`, so Intensity 0 excludes the volume entirely and LV-aware shaders fall back to light probes - a clean on/off for an alternate lighting state.
- If `AutoUpdateVolumes` is false, call `SendCustomEvent("RequestUpdateVolumes")` on the manager after changing Intensity.
- A runtime switch that must assert a default state at startup should not early-out on an unchanged flag (`if (_state == on) return;`), or an editor-side Intensity survives into play mode.

**Verify:** Enter play mode and read the volume Intensity at startup.

Related: [vrc-light-volumes-traps](vrc-light-volumes-traps.md)

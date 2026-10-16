---
title: Bakery light-probe bakes can die silently and leave flat probes
topic: probes-reflection-and-light
tags: [Bakery, light probes, RenderLightProbesButton, VRChat SDK Control Panel, userCanceled, flat SH]
summary: A Bakery probe pass can abort without an error and leave a full-looking but flat probe set; verify probe variance after every probe bake, and close the VRChat SDK panel first.
---
**Symptom:** After a probe bake every probe-lit object (non-static props, vehicles, anything with `receiveGI = LightProbes`) renders roughly 20x too dark and uniformly unlit. The probe set has the right count and every probe is non-zero, but all probes evaluate to the same ambient-only SH (e.g. L0.r = 0.0348 on every one of ~7000 probes, min == max, against a healthy mean of ~0.72 / max ~6.6).

**Cause (two observed):**
1. **Geometry changed since the last full bake.** `RenderLightProbesButton` aborts instantly with the console line "Scene geometry/layout changed since last full bake. Use Render button instead", leaving `bakeInProgress = false` and `progressBarText` stuck at "Exporting scene - preparing...", which looks identical to "already finished".
2. **The VRChat SDK Control Panel is open.** Bakery's probe pass calls `Lightmapping.BakeMultipleScenes()` on a temp scene (`Assets/Bakery/_tempScene.unity`). Opening it fires `activeSceneChanged`; the SDK panel re-validates a scene with no `VRCSceneDescriptor` and throws `IndexOutOfRangeException` in `VRCSdkControlPanelWorldBuilder.CreateValidationsGUI`. That unwinds out of Bakery's coroutine, so the scene setup is never restored. The flags then read `inProgress = False`, `userCanceled = True` (looks like a user cancel; nobody cancelled). Proof line in the log: `Enlighten scene contents: … 0 probe groups`.

**Fix / rule:**
- Run the probe pass immediately after a full Render bake whenever scene geometry or layout changed since that bake. Scope: editing only `LightProbeGroup.probePositions` does not trip the abort, so a standalone probe-only render is fine for probe-placement edits (see light-probe-placement-raycast-grid); still apply the SDK-panel step and the variance check below.
- Before the probe pass, close every `EditorWindow` whose type name contains `VRCSdkControlPanel` (`Resources.FindObjectsOfTypeAll<EditorWindow>()`). Reset `userCanceled = false` (a dead run leaves it latched and the next launch inherits it), then relaunch.

**Verify:** Never trust completion flags. Read back `LightmapSettings.lightProbes.bakedProbes` and check variance (min ≈ max means the pass died), and sample `LightProbes.GetInterpolatedProbe` at 2-3 spots in different rooms; the values must differ.

Related: [bakery-scripted-bake-recipe](bakery-scripted-bake-recipe.md)

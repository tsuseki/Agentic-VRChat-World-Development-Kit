---
title: Edit-mode preview state that writes serialized fields gets uploaded with the world
topic: vrchat-sdk-upload-components
tags: [Build & Publish, preview, serialized fields, lightmapIndex, scene save, git diff]
summary: The VRChat SDK saves the open scene during Build & Publish, so any edit-mode preview that mutates serialized fields ships as the world default if left applied.
---
**Symptom:** A world uploads in its "night preview" state: renderers left on `lightProbeUsage = CustomProvided` (black in daylight), a recoloured settings menu.

**Cause:** Edit-mode preview tools that mutate **serialized** fields (`lightmapIndex`, `lightProbeUsage`, `ReflectionProbe.enabled`, light-volume `Intensity`, `Graphic.color`) persist; the SDK saves the open scene as part of Build & Publish. Runtime-only state (MaterialPropertyBlock) evaporates, which makes leaving a preview applied feel safe.

**Fix / rule:** restore the shipped state the moment a preview pass is done — not "after the review finishes" — and make "apply the shipped state" the first line of any scripted save path (with `MarkSceneDirty` before `SaveScene`; see [unity-scripted-edits-do-not-dirty-the-scene](unity-scripted-edits-do-not-dirty-the-scene.md)). Audit the default state against a pre-feature snapshot of **every** field the toggle writes, not just the one reported.

**Triage rule:** when a metallic or glossy surface reads as lit by the wrong state ("night lightmap on day"), check the **reflection probe** enabled state before touching lightmaps. In one case every lightmap index matched the pre-feature snapshot; the surface was metallic 0.60 / smoothness 0.68, cubemap-dominated, and the night probe had been saved on with the day probe off.

**Verify:** without trusting the editor:
```bash
git diff -U0 -- <scene>.unity | grep -E "m_LightmapIndex|m_LightProbeUsage|m_ReflectionProbeUsage|m_IsActive|m_Enabled:"
```
No output means lighting state matches the last commit.
Alternatively, reopen the scene from disk and query it, rather than re-querying in-memory state.

**Pitfalls:** grep markers must come from the serialized value, not an inspector dump — Unity writes `g: 0.27936998`, so `0.2794` from `ToString("F4")` matches nothing. Better discriminator: a colour stored in both a palette array and a live component appears exactly twice as often as its unapplied counterpart.

---
title: Grey stipple on trees right after a capture camera jumps is the LOD cross-fade
topic: agent-workflow-verification
tags: [LODGroup, cross-fade, dither, capture, review renders, A/B diff]
summary: With animated LOD cross-fade, the first render after a camera jump catches LODGroups mid-fade (dithered or mixed levels); set LODGroup.crossFadeAnimationDuration to ~0.001, render each pose twice and keep the second, then restore the project value.
---

**Symptom.** Review captures showed grey dither on tree crowns in some frames and not in others from the same pose; A/B diffs flagged changes on trees nobody touched. Freshly re-registered LODGroups showed it most.

**Cause.** With animated cross-fade, LODGroups fade over `LODGroup.crossFadeAnimationDuration` (default 0.5 s) after the camera moves. A capture rendered right after the jump catches the fade: dithered levels, or a mix of levels. A capture camera's fade state can also follow the editor camera's. `WorldCapture` doesn't settle it.

**Fix / rule.**
- In the capture call: save the old value, set `LODGroup.crossFadeAnimationDuration = 0.001f`, render each pose twice (or 2–3 throwaway `_warm` shots) and keep the last, restore the old value in the same call.
- For hide-and-diff passes over many views, freeze fades the same way before diffing.
- In-memory only; the review state report confirms the duration was restored.

**Verify.** Two settled captures of the same pose differ by 0 px; re-shoots of the flagged views were clean.

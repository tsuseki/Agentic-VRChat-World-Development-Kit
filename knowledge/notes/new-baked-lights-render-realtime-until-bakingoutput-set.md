---
title: New or cloned Baked lights render as realtime until their bakingOutput says baked
topic: lighting-baking
tags: [bakingOutput, isBaked, realtime lights, placement-only edits, Bakery]
summary: A Light set to Baked but created or duplicated after the last bake has bakingOutput.isBaked = false, so Unity draws it as a realtime light in the editor and in builds; copy a baked sibling's bakingOutput (or bake) before saving.
---

**Symptom:** after adding a picture light (four Baked spot lights cloned from an existing fixture) without re-baking, editor renders showed bright spot scallops on the wall above the new frame. No realtime light existed by `lightmapBakeType`.

**Cause:** Unity decides whether to light a mesh in real time from `Light.bakingOutput`, not from `lightmapBakeType`. A light that has not been through a bake has `bakingOutput.isBaked = false`, so it renders as a realtime light (editor, Play mode and the uploaded world) even though its mode reads Baked. Cloning a baked light with `Instantiate` does not reliably carry the baked state, and Bakery only writes it during a bake.

**Fix / rule:** on placement-only passes that add or clone lights, copy `bakingOutput` from a baked sibling of the same type (`isBaked = true`, `lightmapBakeType = Baked`, `mixedLightingMode` as the sibling) onto every new light, or run the bake. The light then contributes nothing until the next bake, which is the honest state for an unbaked fixture.

**Verify:** count active lights where `!bakingOutput.isBaked || bakingOutput.lightmapBakeType != Baked`; it must be 0 before saving. Re-render the same camera: the scallops are gone (before/after pair).

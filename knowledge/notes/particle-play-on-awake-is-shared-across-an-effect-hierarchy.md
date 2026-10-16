---
title: ParticleSystem playOnAwake is shared across an effect hierarchy — set it on the root last
topic: audio-video-ui
tags: [ParticleSystem, playOnAwake, sub-emitter, toggle, animation, effects]
summary: Setting playOnAwake=false on a collision sub-emitter disabled the parent effect too; an object activated by toggle then emitted nothing.
---
**Symptom:** an effect toggled on via animation/GameObject activation becomes active but emits nothing; manual `Play()` works.

**Cause:** `ParticleSystem.MainModule.playOnAwake` behaves as shared across a particle effect hierarchy. Turning it off on a child (a collision sub-emitter) also disabled the parent.

**Fix / rule:** configure the hierarchy first, then set the **root** `main.playOnAwake = true` last; don't set the sub-emitter false afterwards. Registered collision sub-emitters still don't burst at launch.

**Verify:** test the real activation path (toggle/button) and record `particleCount` across editor frames **without** calling `Play()` or `Simulate()`; a standalone `Simulate` test bypasses activation bugs. Repeated-trigger effects need a short inactive "restart" state between presses so each press re-arms.

**Other pitfalls:** mesh particles use a normalized mesh, so `startSize` is the world size; Particles/Standard Unlit gives a flat silhouette — use Particles/Standard Surface with Normal/Color/UV vertex streams for lit mesh particles; world-space simulation freezes launch position independent of the emitter moving.

---
title: Local underwater effect in Udon — switch on at the surface, keep the fog mode, set only _Udon globals
topic: udonsharp-networking
tags: [underwater, water, fog, fog stripping, FogMode, VRCShader, _Udon globals, GrabPass, depth texture, ClientSim, hysteresis]
summary: A head-in-water screen effect needs an asymmetric switch (on at depth > 0, off ~3 cm above), the world's own fog mode with per-mode density (Exp 5.54/d, ExpSq 2.355/d), _Udon-prefixed shader globals, no depth texture, and play-mode proof renders.
---
Context: a local UdonSharp effect (head position against axis-aligned water boxes) that turns on a
full-screen GrabPass overlay, swaps the scene fog, shows an underside quad of the water surface and
muffles world AudioSources. The kit version is `.omp/templates/underwater/` (README has the full proof list).

**Symptom 1, dry band:** with the head 0–3 cm under the surface the player saw a "drained pond": a dry,
sunlit bed, clear sky straight up, no water surface, no fog.
**Cause:** the switch used the same 3 cm threshold both ways (on at depth > 3 cm). The world's water quad
is back-face culled, so from below it draws nothing until the effect's underside quad is on.
**Fix:** asymmetric hysteresis: on as soon as depth > 0, off only when the head is 3 cm **above** the
surface. The tinted 0–3 cm above the surface reads as a water film; the dry band under it reads as broken.
**Verify:** lower the head through the surface 2.5 mm per step (eye height, feet on the bed): switch-on at
head = surface (−0.3000 for a −0.30 surface), off 3 cm above, one switch each way, 0 frames with the head
under the surface and the underside off. Bob ±1 / 2 / 2.5 cm at 0.7 Hz: 0 switches after the first dip.

**Symptom 2, fog only in the editor:** the underwater fog showed in the editor and ClientSim, but in builds of
Exponential-fog worlds it would not render (found in review from the stripping setting; not reproduced in a build).
**Cause:** the script forced `RenderSettings.fogMode = ExponentialSquared`. With fog stripping on Automatic
(`GraphicsSettings` `m_FogStripping: 0`) a build keeps only the `FOG_*` variants of the modes its scenes use.
A world with fog **off** has no fog variants at all.
**Fix:** keep the world's mode and change only colour, density and linear start/end. Make the installer warn
when scene fog is off. Restore every stored value on surfacing. Opaque (1/255) at distance d:
Exponential ρ = ln 255 / d = **5.54 / d**; ExpSq ρ = √(ln 255) / d = **2.355 / d**; Linear start 0, end d.
With the same d, Exp is far murkier near the eye (transmittance at 2 m of d = 8 m: 0.25 vs 0.71). Give Exp
worlds about **1.6× d** for a similar mid-range look.
**Verify:** in play mode set each world fog mode, re-run the behaviour's `_start`, dive and surface. Submerged
density = 0.6925 (5.54 / 8) for Exp, 0.294375 (2.355 / 8) for ExpSq, linear 0 / 8; after surfacing the mode,
colour, density and start/end match the stored values bit-exact, in all three modes.

**Symptom 3, globals ignored:** a shader global set from Udon has no effect.
**Cause:** `VRCShader.SetGlobal*` only accepts property names that start with `_Udon`.
**Fix:** name them `_Udon<Effect>_*` (here `_UdonUW_Params`, `_Tint`, `_Murk`, `_Floor`); get the IDs once
in `Start` with `VRCShader.PropertyToID`; zero the amount global on restore.

**Symptom 4, depth-based fog or foam renders wrong or flat:** water shaders that read
`_CameraDepthTexture` show nothing useful.
**Cause:** VRChat worlds have no camera depth texture unless a realtime shadowed light generates one; baked
worlds have none.
**Fix:** take the distance falloff from the scene fog (every Unity-fogged shader follows it); make the overlay
one full-screen GrabPass draw that needs no depth. The vertex shader writes the clip-space quad itself (mesh
bounds ±2000 m so it is never culled), which covers both eyes in single-pass instanced. Derive any screen
wobble from the screen row only, so both eyes get the same offset. The underside is an upward quad 1 mm
under the water with `Cull Front`, so it never shares a camera side with the `Cull Back` water and can't
z-fight.

**Symptom 5, black water in proof frames:** edit-mode renders after a scene reopen drew the water flat black.
**Cause:** the reflection probes don't refresh while the editor is unfocused.
**Fix:** render the proof in play mode (one play-mode toggle also clears it); reject any frame with flat black
water.

**Pitfalls:**
- ClientSim puts the head at feet + 0.92 × eye height. Place a head with `SetAvatarEyeHeightByMeters` plus
  `TeleportTo` the floor under it, and log the measured head, not the request. Bobbing by teleporting the feet
  above ±4 cm lets gravity drop them between frames: those switch counts are harness artefacts.
- Standing players can't submerge in water shallower than their eye height (~1.3 m for a 1.4 m avatar);
  VRChat has no swimming, so shallow ponds show the effect only to crouching or prone players.
- Within ~1 cm under the surface the camera's near plane clips the underside and looking up shows the sky;
  it is inherent and transient.
- Shaders that apply fog from their own uniforms (radial fog for mirrors) ignore a `RenderSettings` swap
  unless the effect drives those uniforms too.

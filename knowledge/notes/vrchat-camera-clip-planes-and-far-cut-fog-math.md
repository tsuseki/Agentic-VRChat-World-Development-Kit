---
title: VRChat camera clip planes and the fog math for hiding a far-plane cut
topic: vrchat-sdk-upload-components
tags: [VRCCameraSettings, near clip, far clip, reversed-Z, float depth, skybox overdraw, fog, ExpSq, fog dome]
summary: VRCCameraSettings clamps runtime near clip to 0.001–0.05; PC depth is float32 reversed-Z so near costs no precision, but the skybox paints over geometry beyond f_eff ≈ n·f/(n + 5.3e-7·(f−n)); ExpSq fog must hide the cut at that effective far.
---
**Near clip:** the Reference Camera's Inspector minimum is 0.01. `VRC.SDK3.Rendering.VRCCameraSettings.ScreenCamera.NearClipPlane` is read-write at runtime and **clamped to 0.001–0.05 m**; far must be ≥ near + 0.1. Set far first, then near, from an UdonSharp `Start()`; read `NearClipPlane` back to detect a user's "Forced Camera Near Distance" (Forced = 0.001 always; worlds can't override it). Keep a local-Camera fallback for editor play mode. Rule: near ≤ (closest surface that must stay intact) / 2; cuddle worlds use 0.001–0.01.

**PC depth is 32-bit float, reversed Z** (measured on Unity 2022.3 D3D11: `D32_SFloat_S8_UInt` even when 24-bit is requested, `usesReversedZBuffer = True`). Minimum depth separation measured identical for near 0.001–0.1 (≈4 µm at 100 m, 32 µm at 1 km), so a small near costs no z-fighting and far/near ratio rules are fixed-point (D24) rules only. Precision is limited by float32 world coordinates instead: keep cuddle zones < 256 m and occupied space < 512 m from the origin.

**Skybox overdraw is the real far limit:** the skybox overwrites pixels whose reversed depth < ε ≈ 5.3×10⁻⁷, so geometry is visible only to **f_eff ≈ n·f / (n + ε·(f − n))** (saturating at n/ε ≈ 1.9 km for n = 0.001). Measured at f = 1000: 684 m at n = 0.001, 950 m at 0.01, 989 m at 0.05; f = 700, n = 0.001 gives 532 m, matching users' 531 m. A solid-colour clear doesn't overpaint. Far needed to show distance D: f = n·D/(n − 6e-7·D).

**Hiding the far-plane cut with ExpSq fog:** `T(d) = exp(-(ρd)²)`. A straight cut is visible whenever contrast ≥ one 8-bit step. Reach T ≤ 1/1020 by the effective far for n = 0.001 users: **ρ ≥ 2.63 / f_eff** (Exp: 6.93/f_eff; Linear: end ≤ f_eff). `ρ = 0.00235` at 1000 m leaves ~1 level, faintly visible. Make the sky's horizon and below-horizon colour equal the fog colour so overpaint and the cut vanish.

**Pitfalls:**
- Unity's built-in fog uses view-space depth, same as the far plane, so a short far plane fogs uniformly — and thereby **masks** radial boundaries the fog can't actually hide. See [fog-must-be-radial-and-shader-driven-for-mirrors](fog-must-be-radial-and-shader-driven-for-mirrors.md).
- A sky-occluder/fog dome with radius beyond the camera far clip is culled and silently never renders (e.g. r=1200 with far 1000). If the skybox below the horizon equals the fog colour, the dome is redundant anyway.

Details and sources: `.omp/skills/clip-planes/SKILL.md`.

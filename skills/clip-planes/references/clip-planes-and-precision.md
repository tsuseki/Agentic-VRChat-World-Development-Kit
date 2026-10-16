# Clip planes, depth precision and world extent: research for intimate VRChat worlds

Research date: 2026-10-10. Scope: VRChat PC worlds built in Unity 2022.3 with the Built-in Render Pipeline (D3D11).
Most of these worlds are cuddle and lie-down interiors, so the near clip should be as small as possible. This file
covers how that choice constrains depth precision, the far clip, how far the world can extend from the origin, and
how distant scenery should be handled.

**Tags.** `[Source]` means the claim comes from that entry in **## Sources**. `[in-house]` means a user report or
a kit knowledge note. `[in-house, measured]` means I measured it on 2026-10-10 in the Unity 2022.3.22f1 editor on
D3D11 with throwaway C# (method in §2.1). `[INFERENCE]` means my own derivation or recommendation, which you can
tune.

---

## 0. Defaults

| World type | Reference Camera near | Runtime near (`VRCCameraSettings`) | Far clip | Fog | Max \|coordinate\| reachable |
|---|---|---|---|---|---|
| Intimate interior (cuddle rooms, views out through windows) | 0.01 | 0.001–0.003, sized by §4 | Smallest that covers the longest sightline (§4), typically 300–1000 | Optional; horizon band of sky = fog colour | **< 256 m** (hard limit 512) |
| Mixed (interior plus garden, beach or rooftop) | 0.01 | 0.003–0.005 | 500–1000 | ExpSq, opaque before the effective far | < 512 m |
| Large outdoor or flying (the known-good case) | 0.01 | none | 1000 [in-house: a shipped flying world]; up to ~2000 if needed | ExpSq, T(far) ≪ 1/255 | < 512 m around the social core; vehicles may range further |

All rows are [INFERENCE] built on the measurements below. The 1000 m far clip on a fogged flying world comes from a
shipped world [in-house].

---

## 1. VRChat camera clip rules

| Fact | Value | Tag |
|---|---|---|
| Where the world sets clip planes | The Scene Descriptor's **Reference Camera**. Its settings "are applied to the player when they join the room. It is most often used for adjusting the clipping planes" | [VRChat First World], [VRChat Scene Descriptor] |
| Default far clip with no override | 1000 m | [VRChat Dev Update 2022-08-03] |
| Default near clip | 5 cm (stated by a user; not in the docs I read) | [WildCat Canny 2025] |
| Inspector minimum for `Camera.nearClipPlane` | 0.01. The Reference Camera can't go lower | [in-house] (clip-planes note) |
| Runtime API | `VRCCameraSettings.ScreenCamera.NearClipPlane` / `FarClipPlane` are read-write and "follow similar restrictions to setting them via the Reference Camera" | [VRChat Camera Settings] |
| Enforced near range | **Clamped to 0.001–0.05 m** | [VRChat Camera Settings] |
| Enforced far range | ≥ near + 0.1 | [VRChat Camera Settings] |
| Desktop vs VR | Same API and clamps. `ScreenCamera` "will be a stereo camera if the user is in VR". The docs list no per-platform difference | [VRChat Camera Settings] |
| Handheld photo, stream and drone camera | `VRCCameraSettings.PhotoCamera` exposes the same near/far properties. It is `null` in ClientSim | [VRChat Camera Settings] |
| Mirrors | The mirror's Clear Flags default to "From Reference Camera" (the skybox is redrawn in the mirror). The Water layer never renders in mirrors | [VRChat Mirror Reflection] |
| Mirror near plane | Oblique, lying on the mirror surface. Fog state is missing in the mirror pass | [in-house] (fog note: replicate with `Camera.CalculateObliqueMatrix`); oblique-plane depth effects are [INFERENCE] |
| Per-layer cull distances | `ScreenCamera.LayerCullDistances` (32 entries; 0 means use far). Reserved layers can't be changed | [VRChat Camera Settings] |
| Occlusion culling toggle | `UseOcclusionCulling` defaults to true and works only if occlusion data is baked | [VRChat Camera Settings] |
| Since 2024.1.1 | "World-specified camera reference clipping distances should no longer affect the VRChat menu" | [VRChat 2024.1.1] |

**User override: "Forced Camera Near Distance".** This is a user setting with three modes. **Off** uses the world's
value. **Dynamic** uses 0.001 m when far ≤ 1000. When far > 1000 it uses the lowest near within a factor of 10⁶ of
far, capped at the world's near. **Forced** always uses 0.001 [VRChat Dev Update 2022-08-03]. The setting now
persists between worlds and sessions [hdorriker Canny 2025]. A world can't override it, but it can detect it by
reading `NearClipPlane` back after setting it [VRChat Camera Settings], [hdorriker Canny 2025]. In Dynamic and
Forced mode, users measured visible distance falling from 693 to 531 m (far 700) and from 1180 to 683–787 m
(far 1200) [WildCat Canny 2025]. §2.5 reproduces and explains this. VRChat states that very small near values with
large far values cause "fog breaking, sprites drawing past FarClip, extreme Z-fighting"
[VRChat Dev Update 2022-08-03], and that cursor jitter improved but "floating point inaccuracies will still occur"
[VRChat 2025.4.2].

**What a too-large near clip looks like.** Anything closer than *n* in view depth is cut away. Surfaces are
back-face culled, so a clipped face or hand shows as a hole you can see through, not a cap. Avatars smaller than
average see their own body clipped [Ericbazinga in hdorriker Canny 2025]. A frequent reporter says "1 cm is close
enough for head pats and cuddles when using typically scaled avatars" and 5 cm "is too relaxed"
[WildCat Canny 2025].

The near plane is flat, so a point at angle θ off-axis is clipped once its *radial* distance falls below n/cos θ.
At 50° off-axis in a wide VR field of view that is 1.56 n. **Rule: n ≤ (closest surface that must stay intact) / 2.**
With n = 0.01 everything beyond about 2 cm survives anywhere in view [INFERENCE].

**Setting it from Udon** (pattern from [in-house] clip-planes note; API from [VRChat Camera Settings]):
```csharp
// UdonSharp. Set far first: Dynamic mode re-derives near when far changes.
var cam = VRC.SDK3.Rendering.VRCCameraSettings.ScreenCamera;
cam.FarClipPlane = farClip;        // from §4
cam.NearClipPlane = nearClip;      // clamped to 0.001..0.05
bool userOverride = Mathf.Abs(cam.NearClipPlane - nearClip) > 1e-6f;  // Forced/Dynamic active
```
Keep a local `Camera` fallback for editor play mode [in-house].

**Tooling note.** The kit's `ZFightRender` defaults to this file's PC model (§2): float32 reversed-Z, tolerance
max(0.05 mm, 2·(2⁻²⁴·C + 2⁻²³·d)) with C the camera's largest |coordinate|, independent of the near clip. Its
older 24-bit fixed-point model at near 0.01 remains available as `DepthFormat = Fixed24` for D24 platforms
[in-house] (`ZFightRender.cs`).

---

## 2. Depth precision

### 2.1 What the depth buffer actually is (PC)

- Unity puts DirectX 11, DirectX 12 and Metal on **reversed Z**: depth is 1.0 at the near plane and 0.0 at the
  far plane. "Other platforms" use the traditional direction. "Reversed direction depth (Z), combined with a
  floating point depth buffer, significantly improves depth buffer precision" [Unity Platform Differences].
- On 2022.3.22f1 with D3D11 [in-house, measured]: `SystemInfo.usesReversedZBuffer = True`. The default
  depth-stencil format is `D32_SFloat_S8_UInt`. A render texture that asks for a **24-bit depth gets
  D32_SFloat_S8_UInt**, and 32-bit does too; only 16-bit gives D16_UNorm. HDR+MSAA4/8 and LDR+MSAA2 targets also
  reported D32_SFloat_S8_UInt.
- So VRChat PC renders into a **32-bit float, reversed-Z** depth buffer. That holds for camera targets and
  intermediate targets on D3D11 [in-house, measured]. The VR eye-texture format inside the shipping client was not
  observable [INFERENCE: it is created through the same 24-bit request, so it is D32F].
- Android/Quest is not covered here. Unity lists only D3D11/12 and Metal as reversed [Unity Platform Differences].
  For worst-case numbers, assume D24 fixed point there [INFERENCE].

**Method.** I drew a front quad, then a back quad at +δ, through `CommandBuffer.SetViewProjectionMatrices`
(Unity applies the GPU projection and reversed Z) into a 24-bit-requested render texture. The result is the
smallest δ at which the back quad never wins any pixel. Pixels are tested head-on with Unlit/Color.

### 2.2 Formulas

Distance from the camera along the view axis = d. Bits of depth = b.

- **Fixed point (D24), either direction:** Δd ≈ d²·(f−n)/(n·f·2^b) ≈ **d² / (n·2²⁴)**. The far clip barely matters.
  The near clip dominates. This is the classic curve [Reed 2015].
- **Float32 with reversed Z** (z_ndc = n(f−d)/(d(f−n)) stored with 23-bit relative precision):
  Δd ≈ 2⁻²³·d·(1 − d/f) ≈ **1.2×10⁻⁷·d**, **independent of n** [INFERENCE: derivation]. In practice
  vertex-transform rounding of float32 positions dominates, so the real floor is about ½ ulp of the larger of the
  distance and the world coordinate (§2.3).
- NVIDIA: reversed Z with a float buffer gave a "zero error rate" in their test. It "erases the distinctions
  between ... finite versus infinite far planes" — **"you can use whichever far plane you like, without affecting
  precision at all"**. Reversed Z with an *integer* buffer is no better than standard [Reed 2015].

### 2.3 Minimum surface separation for a correct depth order

Camera at the origin. The PC rows were measured; the D24 rows come from the formula.

| Buffer, near n | 1 m | 10 m | 100 m | 500 m | 1000 m |
|---|---|---|---|---|---|
| **PC D32F reversed, any n 0.001–0.1, f = 1000** [in-house, measured] | 0.07 µm | 0.5 µm | 4.3 µm | 16 µm | 32 µm (d = 999) |
| PC D32F reversed, f = 5000 [in-house, measured] | 0.07 µm | 0.5 µm | 4.3 µm | 16 µm | 96 µm |
| D24, n = 0.001 (any f ≥ d) | 60 µm | 6 mm | 0.60 m | 14.9 m | 59.6 m |
| D24, n = 0.01 | 6 µm | 0.6 mm | 60 mm | 1.49 m | 5.96 m |
| D24, n = 0.05 | 1.2 µm | 0.12 mm | 12 mm | 0.30 m | 1.19 m |
| D24, n = 0.1 | 0.6 µm | 0.06 mm | 6 mm | 0.15 m | 0.60 m |

How far 500 / 1000 / 2000 / 5000 changes the D24 rows: by less than 0.01 %. For D24, the far clip only decides
whether d is inside the frustum at all [INFERENCE: (f−n)/f ≈ 1].

**Away from the origin** (n = 0.01, f = 1000, camera at (X, 1.5, X), measured [in-house, measured]):

| X (m) | d = 0.3 m | 1 m | 10 m | 100 m |
|---|---|---|---|---|
| 0 | 0.015 µm | 0.07 µm | 0.5 µm | 4.3 µm |
| 100 | 7.5 µm | 4.3 µm | 4.3 µm | 13 µm |
| 500 | 3.6 µm | 16 µm | 19 µm | 39 µm |
| 1000 | 19 µm | 32 µm | 32 µm | 67 µm |
| 5000 | 56 µm | 287 µm | 287 µm | 287 µm |
| 10000 | 344 µm | 495 µm | 495 µm | 495 µm |

The world coordinate, not the near clip, sets the floor: about ½·ulp(max(|P|, d)) (§3.1).

### 2.4 What reversed float-Z changes

1. **Near clip no longer limits depth precision.** Measured separations were identical for n = 0.001, 0.01, 0.05
   and 0.1 [in-house, measured]. On PC, dropping from n = 0.05 to n = 0.001 costs no z-fighting.
2. **Far clip doesn't limit precision either** [Reed 2015]. It still matters for culling, fog and the skybox cut
   (§2.5, §4).
3. The old "far/near ≤ 10³–10⁴" rule [in-house] (clip-planes note) is a fixed-point rule. So is Wikidot's advice
   that "raising [far] past 3000 is not recommended" [VRChat Wikidot Render Distance]. On PC the real
   replacement is the skybox limit in §2.5 [INFERENCE].
4. Exactly coplanar faces (δ = 0) fight on any buffer. Scripted flush joints fight on every instance [in-house]
   (overlap note).

### 2.5 The real far limit on PC: the skybox paints over distant geometry at small near

[in-house, measured] Setup: a green quad at distance d, the camera clearing to a skybox (Panoramic and Procedural
gave identical results), and a binary search for the largest d at which the quad is still visible.

| far f | n = 0.001 | n = 0.01 | n = 0.05 |
|---|---|---|---|
| 700 | **532** (76 %) | 675 (96 %) | 695 (99 %) |
| 1000 | **684** (68 %) | 950 (95 %) | 989 (99 %) |
| 1200 | 745 (62 %) | 1129 (94 %) | 1183 (99 %) |
| 10000 | 1598 (16 %) | 6843 (68 %) | 9061 (91 %) |

- The result was identical for LDR and HDR, with no MSAA and with MSAA 2/4/8. With a **solid-colour clear** there
  is no overpaint: geometry stays visible to ~f. At n = 0.001 it is even drawn **past** the far plane (seen at
  1.05 f) [in-house, measured]. That matches VRChat's "sprites drawing past FarClip" [VRChat Dev Update 2022-08-03].
- The f = 700, n = 0.001 result (532 m) reproduces the user measurement of 531 m [WildCat Canny 2025]. **Cause:**
  the skybox, drawn after opaques, overwrites any pixel whose reversed depth is below ε ≈ 4.5–6.0×10⁻⁷ (median
  5.3×10⁻⁷) [in-house, measured]. The exact internal reason is [INFERENCE].
- **Effective far:** f_eff ≈ n·f / (n + ε·(f − n)), with ε ≈ 5.3×10⁻⁷. As f → ∞ it saturates at **n/ε**:
  ≈ 1.9 km at n = 0.001, 19 km at n = 0.01, 95 km at n = 0.05 [INFERENCE: fit to the table above].
- **Keeping 95 % of f** needs f ≤ ~10⁵·n. **Keeping 99 %** needs f ≤ ~1.9×10⁴·n. VRChat's Dynamic factor of 10⁶
  leaves about 65 % [INFERENCE]. That matches the 787/1200 the user measured [WildCat Canny 2025].

Far clip needed so that geometry out to distance D stays visible (ε taken as 6×10⁻⁷ for margin)
[INFERENCE]: **f_req = n·D / (n − ε·D)**, valid only while D < n/ε.

| n \ D | 100 | 300 | 500 | 1000 | 2000 | 5000 | max D |
|---|---|---|---|---|---|---|---|
| 0.001 | 106 | 366 | 714 | 2500 | — | — | 1.67 km |
| 0.003 | 102 | 319 | 556 | 1250 | 3333 | — | 5 km |
| 0.01 | 101 | 305 | 515 | 1064 | 2273 | 7143 | 16.7 km |
| 0.05 | 100 | 301 | 503 | 1012 | 2049 | 5319 | 83 km |

**Consequence for Forced/Dynamic users (n = 0.001).** These users see real geometry only out to about 0.65 f
(f ≤ 1000), whatever the world sets. Design so that content between 0.65 f and f may vanish into the sky without
anyone noticing: make the sky's horizon band equal the fog colour, and make the fog dense by then (§4)
[INFERENCE].

### 2.6 Z-fighting separation rule (used by the checklist)

- **Never coplanar.** Joints overlap by 1–3 cm, and decals or overlays stand off ≥ 1 mm [in-house] (overlap note)
  + [INFERENCE].
- **PC-only world:** δ ≥ max(1 mm, 2×10⁻⁶·(R + d)). R is the largest |coordinate| in the world, d the viewing
  distance. That is a safety factor of about 30 over the measured floor. The 1 mm floor covers shadow bias, import
  rounding and mesh compression [INFERENCE]. While R + d ≤ 500 m the 1 mm floor governs; beyond that the
  linear term takes over (for example 3 mm at R = 500 m, d = 1000 m).
- **Conservative / cross-platform rule (D24, `ZFightRender`'s `Fixed24` mode):** δ ≥ 2·d²/(n·2²⁴). With n = 0.01
  that is 0.2 mm at 4 m, 5 mm at 20 m, 12 cm at 100 m and 3 m at 500 m [in-house] (ZFightRender) + [INFERENCE].
  Distant layered terrain or road decals need this treatment only if the world also ships to D24 platforms.
- **Detector (`ZFightRender` default, PC):** flags pairs within max(0.05 mm, 2·e), e = 2⁻²⁴·C + 2⁻²³·d. The
  unscaled e already bounds every §2.3 measurement (e.g. e = 71.5 µm at C = 1000, d = 100 vs 67 µm measured;
  e = 0.60 mm at C = 10000, d = 1 vs 0.495 mm). That is below the authoring rule above, so a decal that obeys
  the authoring rule passes the detector [in-house] (ZFightRender) + [INFERENCE].

---

## 3. Floating-point position precision

### 3.1 Float32 spacing (ulp) vs coordinate magnitude

ulp(x) = 2^(⌊log₂ x⌋ − 23). The maximum rounding error is ulp/2 [Dawson 2012] (the table matches his values at
1, 10, 100, 1000 and 10000).

| \|coordinate\| | 100 m | 128–256 m | 256–512 m (incl. 500) | 512–1024 m (incl. 1000) | 4096–8192 m (incl. 5000) | 8192–16384 m (incl. 10000) |
|---|---|---|---|---|---|---|
| ulp | 7.6 µm | 15.3 µm | 30.5 µm | 61 µm | 0.49 mm | 0.98 mm |

Precision is **per axis** and is set by the distance from the **world origin**, not from spawn. "Distance from
spawn" is the right proxy only if spawn sits near (0,0,0) [INFERENCE].

### 3.2 Measured close-up jitter

This is the failure that matters for cuddle worlds. Setup [in-house, measured]: camera and an object at a fixed
true offset s, both moved continuously in double precision and rounded to float independently, as a head and a
nearby face are. I recorded the on-screen edge position over 60 frames at 1024 px across 60° (≈ 17 px/deg).

| \|P\| (m) | s = 2 cm | 5 cm | 20 cm | 1 m |
|---|---|---|---|---|
| 0–100 | 0 px | 0 | 0 | 0 |
| 250 | 1 px | 0 | 0 | 0 |
| 500 | **2 px** | 1 | 0 | 0 |
| 1000 | 3 px | 1 | 0 | 0 |
| 2000 | 6 px | 2 | 1 | 0 |
| 5000 | **26 px** | 10 | 2 | 0 |

Model: angular jitter ≈ ulp(|P|)/s, i.e. px ≈ ulp(|P|)/(s·θ_px) [INFERENCE]. The predictions at 20 px/deg
(0.44 / 0.87 / 1.75 / 3.5 / 7 / 28 px at s = 2 cm) match the measurements. **A smaller near clip lets players
bring s down, so it magnifies the jitter a world must tolerate.** The intimate-world constraint is "how close
times how far from the origin", not depth precision [INFERENCE].

### 3.3 Symptoms and what's verified

| Symptom | Status |
|---|---|
| Polygons and UI "violently shake" far from the origin | Players report it; forum answers attribute it to float precision [VRChat Ask 2024] |
| PhysBones jitter "when you get very far away from the origin. This is due to floating point precision" | VRChat staff statement [Mr. Imagination Canny 2024] |
| Close-range vertex shimmer (faces, hands, the other avatar while cuddling) | [in-house, measured] (§3.2) |
| UI cursor jitter, worse at tiny near | [VRChat 2025.4.2] |
| Distant shadow flicker; Unity's fix is "camera-relative culling" for shadows | [Unity Shadow Distance]. Worlds can't ship that project setting [INFERENCE] |
| IK, skinning, world-space particles, physics contacts and pickups at rest degrade the same way | [INFERENCE] (same float32 world-space math) |
| Network quantization of synced player positions as a cause | No VRChat documentation found. It isn't needed to explain the effect [INFERENCE] |
| Floating-origin workarounds break static batching, occlusion culling, VRCObjectSync and world-space shaders | [KitKat4191 JetSim FO]. Avoid them in social worlds [INFERENCE] |

### 3.4 Why "~500 m from spawn" and the radii to use

- The user reports that problems appear beyond ~500 m [in-house]. **512 m is a float exponent boundary**: ulp
  doubles from 30.5 µm to 61 µm. At 256–512 m a 2 cm close-up already moves ~1.75 px at 20 px/deg; past 512 m it
  moves ~3.5 px. That fits a threshold users notice around 500 m [INFERENCE].
- **Radii** (largest per-axis |coordinate| of anything players occupy, including eye height):
  - **Cuddle zones < 256 m** (≤ ~0.9 px at 2 cm). Below 128 m it is ≤ ~0.45 px.
  - **Any player-occupied space < 512 m.**
  - Viewed-only scenery can sit anywhere inside the far clip. Rendering error there is relative to the
    *camera's* coordinate (§2.3) [INFERENCE].
- Put the main social area and spawn at the origin [in-house] (blockout note: "clustered near the origin").

### 3.5 Teleport islands (private rooms ≥ 200 m away)

The user's practice is private rooms ≥ 200 m from the main area [in-house]. The kit's blockout rule is areas
≥ 100 m apart, packed near the origin, e.g. ±170 m [in-house]. Rules [INFERENCE]:

1. |island centre component| + island half-extent **< 256 m** on every axis for cuddle rooms (512 m absolute).
   Example grid: centres at (±220, 0, 0), (0, 0, ±220) and (±220, 0, ±220), rooms ≤ 30 m wide. Adjacent slots are
   then ≥ 220 m apart. Vertical layers at y = ±200 add more slots.
2. Anything below the main floor must stay above the Scene Descriptor's Respawn Height [VRChat Scene Descriptor].
3. At 200–300 m, islands sit **inside** a 1000 m far clip. Either seal them (they then work as occluders with
   baked occlusion culling), put them below the ground plane, or put them on their own user layer with
   `LayerCullDistances[layer] ≈ 150` m so they're culled from the main area but drawn when you're inside
   [VRChat Camera Settings] + [INFERENCE].

---

## 4. Choosing the far clip

**Procedure** [INFERENCE except where tagged]:

1. **Reach box R.** Encapsulate all enabled, non-trigger colliders (in a prop-collider-free world these are the
   floors, ramps and boundary walls). Add 2.5 m of headroom for eyes and jumps. Add flight or vehicle bounds if
   the world has them. Snippet below.
2. **Content box C.** Bounds of every renderer meant to be seen, including backdrop cards. Exclude the skybox.
3. **Sightline** D = |per-axis max(C.max − R.min, R.max − C.min)|. This is an upper bound. Shorten it with a
   raycast sweep from viewpoints if walls block the corners [in-house] (sightline note).
4. **Near clip:** choose the smallest n with f_req(n, D) defined (§2.5 table). Interior worlds with D ≤ 300 m can
   use n = 0.001 with f ≈ 370. Worlds out to 1 km need n ≥ 0.003.
5. **Far clip** f = max(f_req(n, D), 1.05·D). Built-in fog and the far plane are both view-depth, so a radial bound
   D is safe off-axis [in-house] (fog note).
6. **Fog** must reach T ≤ 1/1020 (a quarter of an 8-bit step) by the effective far. For players with Forced near,
   that point is ~0.65 f. ExpSq: ρ ≥ √(ln 1020)/f_eff = **2.63/f_eff**. Exp: ρ ≥ 6.93/f_eff. Linear: end ≤ f_eff.
   Cut math: [in-house] (clip-planes note). The kit's shipped ρ = 0.00235 at 1000 m gives T = 1.0 levels, which is
   faint but visible [in-house] (fog note). For 950 m use ρ ≥ 0.0028.
7. Make the sky's **horizon and below-horizon colour equal the fog colour**. Overpaint (§2.5), the far-plane cut
   and any gap at the edge of the ground then all disappear [in-house] (moonlit-fog note).
8. Apply fog radially in your own shaders so mirrors fog too [in-house] (fog note).
9. Re-check fog domes and sky occluders: one larger than far is culled silently [in-house] (clip-planes note).

```csharp
// Unity MCP execute_code: reach box, content box and sightline. Compiled and run on 2022.3 [in-house, measured].
Bounds reach = default, vis = default; bool hasR = false, hasV = false;
foreach (var c in UnityEngine.Object.FindObjectsOfType<Collider>()) {
  if (!c.enabled || c.isTrigger) continue;
  if (hasR) reach.Encapsulate(c.bounds); else { reach = c.bounds; hasR = true; } }
if (hasR) reach.Encapsulate(reach.max + Vector3.up * 2.5f);
foreach (var r in UnityEngine.Object.FindObjectsOfType<Renderer>()) {
  if (!r.enabled || r is ParticleSystemRenderer) continue;
  if (hasV) vis.Encapsulate(r.bounds); else { vis = r.bounds; hasV = true; } }
System.Func<Bounds, float> axisMax = b => Mathf.Max(Mathf.Max(-b.min.x, b.max.x, -b.min.y), Mathf.Max(b.max.y, -b.min.z, b.max.z));
var span = new Vector3(
  Mathf.Max(vis.max.x - reach.min.x, reach.max.x - vis.min.x),
  Mathf.Max(vis.max.y - reach.min.y, reach.max.y - vis.min.y),
  Mathf.Max(vis.max.z - reach.min.z, reach.max.z - vis.min.z));
return $"reach {reach.min}..{reach.max} maxAxis={axisMax(reach):F0} m | D_view<={span.magnitude:F0} m";
```
A huge catch plane or ocean collider inflates R. List the five largest collider bounds and remove the ones players
can't actually stand on. NavMesh alternative: `NavMesh.CalculateTriangulation().vertices` [INFERENCE].

**Does a larger far clip cost performance (Built-in RP)?**
- The far plane on its own costs little; content draw distances are what lag. Raising terrain detail distance to
  1000 cost ~3× the frame time of 250–800 [in-house] (terrain-trees note).
- A longer far lets more renderers pass frustum culling, which means more draw calls and triangles. Budget per
  viewpoint with LODGroups, baked occlusion culling and walls [in-house] (triangle-budget note). Cull small-prop
  layers early with `LayerCullDistances` [VRChat Camera Settings].
- Shadow distance is a quality setting. Unity uses the far plane instead only "if the current Camera Far Plane is
  closer than the Shadow Distance" [Unity Shadow Distance]. Raising far past shadow distance adds no shadow cost
  [INFERENCE].
- Occlusion culling works only when baked and is on by default [VRChat Camera Settings]. A larger extent means a
  longer bake and more data [INFERENCE].

---

## 5. Distant scenery without geometry

### 5.1 Options, nearest to farthest

| Distance band | Technique | Why |
|---|---|---|
| Inside reach, out to ~3–5× reach radius | Real geometry with LODs | Needs true parallax and stereo [INFERENCE] |
| Mid band, inside f_eff | Backdrop cards (layered silhouettes) or impostors captured from the real assets | 6-tri cross billboards rendered from the real trees looked identical at ≥ 140–200 m and keep the scene's grading [in-house] (impostor note) |
| Beyond the parallax limit (§5.2) | **Baked into the skybox** (cubemap or equirect) | Zero cost, always visible, never clipped |
| Very large, animated or dynamic | A "3D skybox": a miniature sub-scene drawn behind the playable area by a second camera that moves at a fraction of the player | [Unity 3D Skybox] (a URP camera-stacking demo). In a Built-in-RP world this means a second world camera, which costs an extra render [INFERENCE] |

### 5.2 Parallax limit for skybox-baked content

A viewer moving r metres from the capture point sees content at true distance D shift by θ ≈ r/D, while skybox
content doesn't move at all. Required depicted distance: **D_min = r / θ_max** [INFERENCE].

| reach radius r | θ_max = 0.05° (≈ 1 px VR) | 0.25° | 1° |
|---|---|---|---|
| 5 m (room by a window) | 5.7 km | 1.1 km | 290 m |
| 20 m (penthouse, terrace) | 23 km | 4.6 km | 1.1 km |
| 50 m (garden, beach) | 57 km | 11 km | 2.9 km |
| 200 m (island) | 229 km | 46 km | 11 km |
| 500 m (flying) | 573 km | 115 km | 29 km |

- Use **θ ≤ 0.25°** for baked content that sits next to real geometry, such as a skyline continuing a real street.
  Use **θ ≤ 1°** for isolated silhouettes (mountain ranges, distant city glow) [INFERENCE].
- **Stereo:** IPD 64 mm gives disparity 0.064/D rad, which drops below one VR pixel (≈ 0.05°) beyond **~75 m**.
  Past that, motion parallax and not stereo gives a skybox away [INFERENCE].
- **Horizon gap:** from eye height h, a ground plane that ends at R sits atan(h/R) below the sky's horizon line:
  0.09° at h = 1.6 m, R = 1000 m, but **16.7°** from a flying vehicle at h = 300 m. Fill the gap with fog and with a
  below-horizon sky colour equal to the fog colour [INFERENCE] + [in-house] (moonlit-fog note).
- Unreachability only feels odd if a path seems to lead there. Put a barrier (water, cliff, fog, glazing) between
  the reach box and anything baked [INFERENCE].

### 5.3 Capture procedure (cubemap or equirect from the play-area centre)

1. Build the far content as real geometry at its true distance, with final materials and lighting.
2. Place a capture camera at the reach box's centre, at mean eye height (mid-altitude for flying worlds).
3. Set the capture camera's **near = r + margin**, so the playable foreground is excluded, and far beyond the
   content. Use clear = the final sky, and fog on with the runtime settings. Unity skyboxes aren't fogged at
   runtime, so the fog has to be baked into the capture [INFERENCE].
4. `Camera.RenderToCubemap(cubeRT)`, which uses "the Camera's position, clear flags and clipping plane
   distances", then `cubeRT.ConvertToEquirect(equirectRT, Camera.MonoOrStereoscopicEye.Mono)` if you want
   lat-long. Use an HDR ARGBHalf target [Unity RenderToCubemap].
5. Save it as EXR and import it as a Cubemap at **2048 per face** (BC6H ≈ 64 MB; 1024 is blurry through large
   windows) [in-house] (HDRI-import note).
6. Disable the source geometry or tag it EditorOnly. Keep it as the re-capture source.
7. Point the Bakery sky light's `cubemap` at the new skybox cubemap, rebake, then bake reflection probes
   [in-house] (Bakery sky-light note). Re-bake the probes after every lighting bake.

### 5.4 Matching sun, fog and colour

- Match the skybox sun to the baked directional light in **azimuth and elevation**. Elevation-only matching can
  leave it 180° out. Fix it with the closed-form `_Rotation` [in-house] (skybox-sun notes).
- The horizon band of the sky must equal the fog colour (§4 step 7). Grade real geometry, impostors and the
  capture with the same exposure pass [in-house] (cozy-darker-outside note).
- A softly photographed HDRI skyline needs real emissive tower geometry in front for crispness and parallax
  [in-house] (HDRI note).

### 5.5 Mirrors and the photo camera

- Mirrors set to "From Reference Camera" show the skybox [VRChat Mirror Reflection]. Mirrors render **without
  Unity fog state** [in-house] (fog note). So real distant geometry with Unity fog shows unfogged in mirrors,
  while fog baked into the skybox stays correct. That is an argument for baking [INFERENCE].
- The photo camera has its own near/far through `VRCCameraSettings.PhotoCamera` [VRChat Camera Settings]. The
  skybox overpaint in §2.5 applies to any skybox-clearing camera whose depth is reversed float, which includes
  mirrors and photos [INFERENCE].
- Agents' editor screenshots: the Scene view has its own far clip (one was 100 m), and capture cameras have their
  own clip planes. Check them before calling something "missing" [in-house] (Scene-view note).

---

## 6. Checklist (setup agent runs; reviewer verifies)

| # | Check | Pass condition | How |
|---|---|---|---|
| 1 | Reference Camera assigned | Descriptor's Reference Camera is set; its near is **0.01** | Inspect the descriptor |
| 2 | Runtime near/far | If n < 0.01 is wanted, an Udon `Start()` sets far then near through `VRCCameraSettings`. n meets §1's rule (n ≤ closest intact surface / 2) | Read the script; ClientSim read-back |
| 3 | Reach extent | max per-axis \|coord\| of reach box < **256 m** (cuddle zones) / **512 m** (any occupied space). Spawn and social core near the origin | §4 snippet (`maxAxis`) |
| 4 | Teleport islands | Each island: \|centre\| + half-extent < 256 m per axis; ≥ 200 m from the main area; above Respawn Height; sealed, underground or layer-culled from the main area | Bounds per island root |
| 5 | Sightline vs far | D_view measured; far ≥ f_req(n, D) (§2.5 table) | §4 snippet + table |
| 6 | Fog vs effective far | ExpSq ρ ≥ 2.63/f_eff with f_eff computed for n = 0.001 (Forced users), **or** sky horizon colour = fog colour so overpaint is invisible | Compute; 12-bearing horizon sweep ≤ ~1.5 levels [in-house] (fog note) |
| 7 | Sky domes and occluders | Radius < far (else it is culled) | Bounds vs far |
| 8 | Z-fighting rule | No coplanar pairs; joints overlap 1–3 cm; decals ≥ max(1 mm, 2e-6·(R+d)) off their surface (PC). For D24 platforms, ≥ 2d²/(n·2²⁴) | ZFight scan; ZFight render (PC float model by default, `DepthFormat = Fixed24` for D24 platforms) |
| 9 | Skybox backdrop distance | Every baked feature's depicted distance ≥ r/θ (θ = 0.25° next to real geometry, 1° for isolated silhouettes); barrier between reach and backdrop | §5.2 table |
| 10 | Backdrop cards and impostors | Inside f_eff (n = 0.001) or fogged out before it; same fog formula as the terrain | Bounds vs f_eff |
| 11 | Sky matching | Sun azimuth and elevation match the baked light; Bakery sky light uses the sky cubemap; probes rebaked | [in-house] skybox notes |
| 12 | Close-up jitter spot test | Teleport ClientSim to the farthest cuddle spot; a capture camera 2 cm from a surface shows no visible shimmer while moving | Render 2 frames 1 cm apart and diff the edges |
| 13 | Layer culls | Small-prop and island layers have `LayerCullDistances` where they help; reserved layers untouched | Read the script |

---

## Sources

Source keys in this file resolve in [SOURCES.md](../SOURCES.md).

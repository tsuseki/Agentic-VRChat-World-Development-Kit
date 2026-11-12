# Underwater effect (local, UdonSharp)

A local underwater look for VRChat PC worlds. While the local player's **head** is below the surface of a
water volume, the world shows:

- a full-screen overlay: tint, slight desaturation, murk gathering at the screen edges, a gentle wobble and,
  on Strong only, fake caustic lines on the bed;
- underwater fog: the scene fog's colour and density are swapped and the fog mode is kept;
- the water surface seen from below: a rippled bright underside with an approximated Snell window, mirror-dark
  towards grazing angles;
- a light muffle of the world's own AudioSources (low-pass filter and −2 dB).

When the head surfaces, every value goes back bit-exact. Nothing is synced and other players are not affected.
There is no toggle, so nothing needs to persist. Player voices are never touched.

It is a world default, like jumping: every body of water players can enter gets it (world-pipeline C.2;
`.omp/agents/world-builder.md` "Interactions & playability").

## Files

| Template | Copy to | What it is |
|---|---|---|
| `UnderwaterFX.cs.txt` | `<folder>/UnderwaterFX.cs` | UdonSharp runtime, sync None: head-vs-volume test, fades, fog swap, muffle, exact restore |
| `UnderwaterOverlay.shader.txt` | `<folder>/Shaders/UnderwaterOverlay.shader` | `World/UnderwaterOverlay`: one full-screen draw with a GrabPass, stereo-instanced safe |
| `UnderwaterSurface.shader.txt` | `<folder>/Shaders/UnderwaterSurface.shader` | `World/UnderwaterSurface`: underside quad, `Cull Front`, unlit, alpha-blended, fogged |
| `UnderwaterKit.cs.txt` | `<folder>/Editor/UnderwaterKit.cs` | installer `AWDK.Underwater.UnderwaterKit`, menu `Tools/AWDK/Underwater` |
| `UnderwaterShots.cs.txt` | `<folder>/Editor/UnderwaterShots.cs` | play-mode proof jobs `AWDK.Underwater.UnderwaterShots` (sweep, bob, dive, shots, perf, audio) |

`<folder>` is `Assets/<World>/Underwater/`, or a shared folder such as `Assets/_World/Shared/Underwater/`
when several worlds in one project use it. Copy each template once per project; two copies of
`UnderwaterFX` don't compile. The installer creates everything else itself, the first time it runs:
`Meshes/UnderwaterOverlayQuad.asset`, `Meshes/UnderwaterSurfaceQuad.asset`, `Materials/UnderwaterOverlay.mat`,
`Materials/UnderwaterSurface.mat` and the U# program asset `UnderwaterFX.asset`. They go in the folder of
`UnderwaterFX.cs`, or under `UnderwaterKit.AssetFolder` if you set it.

**Requirements:** Unity 2022.3 with the VRChat Worlds SDK 3.x and its bundled UdonSharp (built and verified on
SDK 3.10.5). The scene fog must be on (any mode). PC only, because the overlay uses a GrabPass. If `<folder>`
sits inside an assembly definition, the `Editor/` scripts need an Editor-only asmdef that references it plus
`UdonSharp.Editor`, `UdonSharp.Runtime`, `VRC.Udon` and `VRC.SDKBase`.

## Install

1. Copy the five files (table above) and let Unity compile. Read the console for `error CS`.
2. Measure each body of water: the surface height (the water renderer's top), its footprint as one or more
   axis-aligned rectangles `(xMin, xMax, zMin, zMax)` in world metres, and a bottom below the deepest bed
   (downward raycasts on a 0.5–1 m grid). Seas: cover the reachable sea plus a margin, not the whole skybox
   ocean.
3. Install, one call per water body, through the Unity MCP `execute_code` tool:

   ```csharp
   // first water body: builds the scene root "UnderwaterFX" (re-running replaces it)
   return AWDK.Underwater.UnderwaterKit.Install(new[] { new Vector4(-12f, 10f, -6f, 8f) }, 0.0f, -1.6f);
   // further bodies at other surface heights: append
   return AWDK.Underwater.UnderwaterKit.Install(new[] { new Vector4(40f, 52f, 3f, 9f) }, 1.20f, 0.0f, true);
   ```

   - The first call on a fresh project creates the assets and the program asset and returns `PREPARED ...`.
     Wait for the UdonSharp compile, then call it again.
   - `OK ...` lists the volumes, the measured bed heights (`bedY`, the caustics' plane), the muffled AudioSources,
     the fog mode and `fogEnd`, and warnings. Save the scene.
   - The optional fifth argument `undersideMargin` (metres per side) grows the underside quads. Use it for seas
     whose surface is visible beyond the volume from inside the water.
   - For flat water planes, `Tools/AWDK/Underwater/Install On Selected Water` (or
     `UnderwaterKit.InstallFromRenderers(gameObjects)`) takes the footprint and surface from the selected
     renderers' bounds. Check its `surfaceY`, and use `Install` with measured values when the water is rotated or
     not flat.
4. **Preset:** `0` Subtle is the default; `UnderwaterKit.SetPreset(1)` ships Strong instead. Both presets sit on
   the component, so a later in-world picker only sets `preset` and sends `_ApplyPreset`.
5. **Per-world tint:** match the world's water colour (tropical turquoise, green-brown lake, blue sea) for each
   preset:

   ```csharp
   AWDK.Underwater.UnderwaterKit.SetLook(0, tint, fogColor, murkColor);            // Subtle; optional 5th arg fogEnd
   AWDK.Underwater.UnderwaterKit.SetLook(1, tint, fogColor, murkColor);            // Strong
   AWDK.Underwater.UnderwaterKit.SetUnderside(color, mirrorColor);                 // per-scene copy of the underside material
   ```

   The values live on the scene's component, so the worlds of one project can differ. `SetUnderside` writes
   `Materials/UnderwaterSurface_<Scene>.mat` and leaves the shared material alone.
6. Save the scene, then run the proof below.

### Defaults

| | Subtle (0, default) | Strong (1) |
|---|---|---|
| Tint (rgb) / desaturation | (0.80, 0.97, 0.97) / 0.10 | (0.55, 0.85, 0.80) / 0.25 |
| Fog colour / opaque at (`fogEnd`) | (0.20, 0.42, 0.42) / 8 m | (0.07, 0.22, 0.21) / 4 m |
| Murk colour / strength | (0.10, 0.28, 0.28) / 0.25 | (0.03, 0.14, 0.14) / 0.55 |
| Wobble amplitude / speed | 0.003 screen heights / 1.0 | 0.0085 / 1.5 |
| Caustics | off | 0.35 |
| Muffle | low-pass 5000 Hz, −2 dB | 4000 Hz, −2 dB |

Timing: on as soon as the head is under the surface, 0.12 s fade in; off only when the head is 3 cm above it
(`exitHeight`, hysteresis against head-tracking jitter), 0.35 s fade out. Strong turns everything past about
2.5 m into a dark band, so it reads as a deep lake. Subtle keeps a clear 1 m pond readable 3–6 m away.

### Fog modes

The script keeps the world's fog mode and changes only the numbers. A build keeps only the fog variants its
scenes use (fog stripping Automatic), so switching the mode at runtime would make the underwater fog silently
disappear in the build while the editor still shows it. All three modes are opaque (1/255) at `fogEnd`:

| World fog | Underwater value |
|---|---|
| Exponential | density = 5.54 / `fogEnd` (ln 255) |
| ExponentialSquared | density = 2.355 / `fogEnd` (√ln 255) |
| Linear | start 0, end `fogEnd` |

With the same `fogEnd`, Exponential fog is much murkier near the eye: at 2 m of an 8 m `fogEnd` the
transmittance is 0.25, against 0.71 for ExpSq. **Exponential worlds need about 1.6× the fog distance** to look
like an ExpSq world. On a fresh install `Install` multiplies both presets' `fogEnd` by `UnderwaterKit.ExpFogScale`
(1.6) and reports it. Judge the look in the frames. If the scene fog is off, `Install` warns: with fog off, a
build has no fog variants at all. Turn fog on first; the clip-planes values work.

## Proof (play mode, ClientSim)

Run every check in **play mode**. Edit-mode renders can draw the water flat black after a scene reopen: the
reflection probes don't refresh while the editor is unfocused, and one play-mode toggle fixes it. Reject any
frame with flat black water. Start each job from dry land (the jobs return the player there), poll
`UnderwaterShots.Status()` until `DONE`, and never start a job while one is running.

```csharp
return AWDK.Underwater.UnderwaterShots.Start("sweep", @"C:\Temp\underwater");   // then Status()
```

| Job | Pass |
|---|---|
| `sweep` (head lowered and raised 2.5 mm per step at the deepest point) | descent: 1 switch, on at head ≤ the surface; rise: 1 switch, off about `exitHeight` (3 cm) above it; `drainedFrames=0` both ways; `restore exact=True` |
| `bob` (head ±1 / 2 / 2.5 / 4 / 5 cm around the surface, 0.7 Hz) | ±2 and ±2.5 cm: 0 switches, 0 drained frames; ±1 cm: at most the first dip; `restore exact=True`. At ±4 cm and more, gravity drops the teleported feet between frames, so those counts are harness artefacts |
| `dive` (walk-in from the nearest shore to the deepest point and back, crouch eye height) | `flipsOn=1 flipsOff=1`, `amountDirectionReversals=1`, `EXACT_RESTORE=True`, `overlayActive=False` |
| `shots` (`Start("shots", dir, 1600, 900)`; optional `posesJson`) | per pose `_0_above` (the camera 1 m above the water, head dry: the water looks as it did before install, overlay and underside inactive), `_1_subtle`, `_2_strong`. Default poses at the deepest point: across, up at the surface (Snell window), toward the shore, down at the bed. Make one contact sheet (rows = poses, columns = above / Subtle / Strong) for the user's strength pick |
| `audio` | submerged: filter on at the preset cutoff, volume ×0.794 (−2 dB); surfaced: filter off, volume exactly as before. A scene without AudioSources reports 0 |
| `perf` | overlay + underside on vs off at the first pose; record both medians |

Also check: console clean (no `error CS`, no Udon exceptions); the `UnderwaterFX` behaviour has sync None; for
Exp or Linear worlds, the submerged density (or start/end) matches the table above. Save the scene with 0
`__*__` objects: the capture camera `__UWCapCam__` lives only in play mode. Then the C.2 dressing-reviewer
review: it judges the frames, the contact sheet and the job logs.

## Cost

While submerged: +2 draws (the overlay quad with one GrabPass copy, and the underside quad). Measured on a
pond scene in the editor (render + GPU sync, 4×MSAA): 5.02 vs 5.13 ms at 1920×1080 (within the ±0.4 ms
noise), and 4.64 vs 4.35 ms with Strong at 2560×1440. On land the effect objects are inactive and `Update`
does one head-vs-box test per volume. No depth texture, no extra camera, no RenderTexture.

## Limits

- **No depth-based fog, foam or edge fade.** VRChat worlds have no camera depth texture unless a realtime
  shadowed light makes one, and baked worlds have none. Distance falloff comes from the scene fog on every
  shader that applies Unity fog. Shaders that fog from their own uniforms (radial fog, see
  `.omp/knowledge/notes/fog-must-be-radial-and-shader-driven-for-mirrors.md`) ignore the swap unless you drive
  those uniforms too. The skybox is not fogged; it shows only through the Snell window, tinted by the overlay.
- **The Snell window is approximated:** a smoothstep on the view angle (window up to ~48° from vertical), with no
  refraction and no reflections. Strong's caustics are projected on one flat plane at the median bed height, so
  over shallow boulders they lie flat and slide as the head moves.
- **Standing players can't submerge in shallow ponds.** VRChat has no swimming: players walk on the bed. A
  1.4 m avatar's head sits about 1.3 m above its feet, so a pond under ~1.3 m deep is entered only by crouching,
  going prone or with a shorter avatar. Say so when you show the frames. Deepen the water only if the user asks.
- **Near-clip band:** within about 1 cm under the surface the camera's near plane clips the underside, and
  looking up shows the sky. It is transient. VRChat may scale the near clip with avatar size.
- **Volumes are axis-aligned boxes with a flat top.** Rotation is ignored. Cover rotated or irregular water with
  several footprints. Wave-displaced water leaves a band of the wave height.
- **Only `_Udon`-prefixed shader globals can be set from Udon** (`VRCShader.SetGlobal*`), hence `_UdonUW_*`.
- **Never switch the fog mode at runtime**, because builds strip unused fog modes (see "Fog modes").
- **Audio:** voices are untouched by design. Only scene AudioSources present at install time are muffled, so
  re-run `Install` after adding ambience or video. Sources that already have their own active or tuned
  low-pass filter are skipped. Not tested with AVPro video speakers.
- **Not verified in a headset.** The shaders use the single-pass-instanced stereo macros, and the wobble depends
  on the screen row only, so both eyes get the same offset. Not tested either: VRChat mirrors and the VRChat
  camera, which render without Unity fog state and may draw the overlay into their own image.
- **Android/Quest:** not supported as built, because of the GrabPass and the transparent full-screen draw.

## Provenance

Written from scratch for the kit. The Mochie "Underwater Visuals" shader was only a behavioural reference for
what an underwater view should show. No code or assets were copied from it or from anywhere else, so nothing
is credited.

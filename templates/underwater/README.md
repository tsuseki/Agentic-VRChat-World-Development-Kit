# Underwater effect (local, UdonSharp)

A local underwater look for VRChat PC worlds. While the local player's **head** is below the surface of a
water volume, the world shows:

- a full-screen overlay: tint, slight desaturation, murk gathering at the screen edges, a gentle wobble, the view
  up through the surface bent by its ripples and, on Strong only, fake caustic lines on the bed;
- underwater fog: the scene fog's colour and density are swapped and the fog mode is kept;
- the water surface seen from below: a rippled bright underside (swell, fine chop and splash rings where players
  enter the water) with an approximated Snell window, mirror-dark towards grazing angles;
- a light muffle of the world's own AudioSources (low-pass filter and −2 dB).

When the head surfaces, every value goes back bit-exact. Nothing is synced and other players are not affected.
There is no toggle, so nothing needs to persist. Player voices are never touched.

It is a world default, like jumping: every body of water players can enter gets it (world-pipeline C.2;
`.omp/agents/world-builder.md` "Interactions & playability").

## Files

| Template | Copy to | What it is |
|---|---|---|
| `UnderwaterFX.cs.txt` | `<folder>/UnderwaterFX.cs` | UdonSharp runtime, sync None: head-vs-volume test, fades, fog swap, muffle, exact restore, splash-ring tracking of all players |
| `UnderwaterOverlay.shader.txt` | `<folder>/Shaders/UnderwaterOverlay.shader` | `World/UnderwaterOverlay`: one full-screen draw with a GrabPass, stereo-instanced safe |
| `UnderwaterDome.shader.txt` | `<folder>/Shaders/UnderwaterDome.shader` | `World/UnderwaterDome`: camera-following cube in the fog colour that fills what no geometry covers (far-clip gap, sky below the horizon) |
| `UnderwaterSurface.shader.txt` | `<folder>/Shaders/UnderwaterSurface.shader` | `World/UnderwaterSurface`: underside quad, `Cull Front`, unlit, alpha-blended, fogged |
| `UnderwaterRipples.cginc.txt` | `<folder>/Shaders/UnderwaterRipples.cginc` | the surface slope (swell, chop, rings) both shaders share; a world's own water shader may include it |
| `UnderwaterKit.cs.txt` | `<folder>/Editor/UnderwaterKit.cs` | installer `AWDK.Underwater.UnderwaterKit`, menu `Tools/AWDK/Underwater` |
| `UnderwaterShots.cs.txt` | `<folder>/Editor/UnderwaterShots.cs` | play-mode proof jobs `AWDK.Underwater.UnderwaterShots` (sweep, bob, dive, splash, shots, perf, audio) |

`<folder>` is `Assets/<World>/Underwater/`, or a shared folder such as `Assets/_World/Shared/Underwater/`
when several worlds in one project use it. Copy each template once per project; two copies of
`UnderwaterFX` don't compile. The installer creates everything else itself, the first time it runs:
`Meshes/UnderwaterOverlayQuad.asset`, `Meshes/UnderwaterSurfaceQuad.asset`, `Meshes/UnderwaterDomeCube.asset`, `Materials/UnderwaterOverlay.mat`,
`Materials/UnderwaterSurface.mat` and the U# program asset `UnderwaterFX.asset`. They go in the folder of
`UnderwaterFX.cs`, or under `UnderwaterKit.AssetFolder` if you set it.

**Requirements:** Unity 2022.3 with the VRChat Worlds SDK 3.x and its bundled UdonSharp (built and verified on
SDK 3.10.5). The scene fog must be on (any mode). PC only, because the overlay uses a GrabPass. If `<folder>`
sits inside an assembly definition, the `Editor/` scripts need an Editor-only asmdef that references it plus
`UdonSharp.Editor`, `UdonSharp.Runtime`, `VRC.Udon` and `VRC.SDKBase`.

## Install

1. Copy the six files (table above) and let Unity compile. Read the console for `error CS`; both shaders must show
   no errors in their inspector (`Prepare` refuses to continue otherwise, and when the `.cginc` is missing).
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
   Ripples per water body: `UnderwaterKit.SetRipple(volume, multiplier)` (the volume index from the `Install`
   report; 0.5 for a sheltered pond, 1.5 for open water, 0 for mirror-calm; default 1).
6. Save the scene, then run the proof below.

   More installer calls (all `UnderwaterKit.*`, all return a text report; save the scene afterwards):

   | Call | Use |
   |---|---|
   | `InstallRect(corners, surfaceY, bottomY, slabs, bedY)` | a rotated rectangular pool: four corners in order (x/z); covered by up to `slabs` inscribed axis-aligned slab volumes (`RectOverhang` 0.1 m), every slab's underside is the exact rotated rectangle. Appends. Axis-aligned pools: `slabs` 1 |
   | `AddDome()` | scenes installed before the far dome existed: creates the dome assets and the `Dome` child, assigns `fx.dome`, fills `ringGain` / `ringGlow` when empty and re-syncs the Udon program (save the scene afterwards). `Install` does this by itself on new installs. Older scenes keep their serialized `ringGain` / `ringGlow`: set the current defaults with `SetRings` |
   | `SetUndersideMargin(volume, margin)` | grows the underside quad of a sea to its volume + margin per side (reach what is visible from inside, up to where the world's water ends) |
   | `SetBedY(volume, y)` | caustics plane of one body (the median bed of beds shallower than `CausticsMaxDepth` 6 m is used by default) |
   | `SetRings(gainSubtle, gainStrong, glowSubtle, glowStrong)` | per-preset splash ring look (defaults 1.5 / 2 and 0.35 / 1): Subtle's ring reads for ~2-3 s of its 3 s life, Strong's bold; re-syncs the Udon program |
   | `ScanTransparents()` | lists renderers whose material queue is above 3050 (they would draw over the underside) and counts the world-space canvases |
   | `RefreshAudio()` | re-collect the scene's AudioSources into the muffle list after ambience/video was added to a scene that already has its `UnderwaterFX` |

   Only the underside quad of the volume the head is in is shown, so bodies at several heights (sea + pools) do not float each other's undersides in the air. `Install` measures beds on a grid of at most ~200 steps per side, so a call on a km-wide sea stays short. For seas set `UnderwaterShots.MaxDepth` (e.g. 2.2) and `UnderwaterShots.TestRegion` (xMin, xMax, zMin, zMax) before `Start(..)`, so the proof's "deepest point" is a wading-depth shelf near a shore and not the deep. Extra proof jobs: `jump` (poses with `dropX`, `dropZ`, `dropH`: hand jump-ins seen from below), `udon` / `udonmove` (Udon cost of `_update`; spawn a crowd first with `VRC.SDK3.ClientSim.ClientSimMain.SpawnRemotePlayer()`; ClientSim remote players are moved by their transforms, not by `TeleportTo`).


### Defaults

| | Subtle (0, default) | Strong (1) |
|---|---|---|
| Tint (rgb) / desaturation | (0.80, 0.97, 0.97) / 0.10 | (0.55, 0.85, 0.80) / 0.25 |
| Fog colour / opaque at (`fogEnd`) | (0.20, 0.42, 0.42) / 8 m | (0.07, 0.22, 0.21) / 4 m |
| Murk colour / strength | (0.10, 0.28, 0.28) / 0.25 | (0.03, 0.14, 0.14) / 0.55 |
| Wobble amplitude / speed | 0.003 screen heights / 1.0 | 0.0085 / 1.5 |
| Caustics | off | 0.35 |
| Muffle | low-pass 5000 Hz, −2 dB | 4000 Hz, −2 dB |
| Ripple tilt (swell + chop) / swell scale / speed | 0.45 / 0.8 per m / 0.6 | 0.7 / 0.8 / 0.8 |
| Refraction looking up (screen shift per unit slope) | 0.03 | 0.05 |
| Extra wobble next to a fresh ring | +1.0× the wobble | +0.5× |

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

### Ripples and splash rings

The surface is never glass-flat. `UnderwaterRipples.cginc` gives one slope field that both shaders read:

- **Swell and chop:** four long crossing sine trains (the swell, `rippleScale`/`rippleSpeed`) plus three short
  ones of 0.3–0.5 m (the chop, faded out where a pixel would alias), tilted by `rippleStrength` × the volume's
  `volumeRipple`. The underside's window edge, mirror band and glints follow it.
- **Refraction:** the overlay finds where each upward eye ray meets the surface plane and shifts its grabbed
  pixel by the slope there (`refraction`), so the Snell window, the underside and the sky behind it wobble
  together. It fades out towards the horizon and beyond 20 m. It reuses the overlay's one GrabPass and needs no
  depth texture. A world point drives it, so both eyes see the same ripple.
- **Splash rings:** `UnderwaterFX` samples every player's feet round-robin (`playersPerFrame` = 8 per frame, a new
  round at most every `sampleInterval` = 0.05 s, so 80 players are each seen about every 0.1 s). Feet crossing a
  volume's surface downward push a ring with amplitude `splashMin + splashPerSpeed × downward speed` (a step in
  from the bank ≈ 0.25, a jump from 1 m ≈ 1). Wading faster than 1 m/s pushes a small wake ring every 0.6 s. Rings
  spread at 1.2 m/s with a 0.35 m wavelength and fade over 3 s; the buffer holds the newest 8. Players beyond
  `ringRange` (40 m) from the local head are ignored, and moves faster than 12 m/s sideways or 40 m/s vertically
  count as teleports. A ring within 4 m of a head near the surface briefly adds `ringWobble` to the overlay
  wobble. Everything is local: each client sees rings from the positions it already receives.

Globals, readable by any shader (only `_Udon*` names can be set from Udon):

| Global | Content |
|---|---|
| `_UdonUW_Wave` | x swell/chop tilt, y swell scale (1/m), z swell speed, w refraction |
| `_UdonUW_RingCfg` | x ring speed (m/s), y life (s), z wavelength (m), w now (Udon `Time.time`, updated while a ring lives) |
| `_UdonUW_Rings[8]` | x, z world position, start time (same clock), amplitude 0..1 (0 = empty; Strong pushes up to `ringGain` x that) |
| `_UdonUW_RingGlow` | ring highlight weight of the active preset (`ringGlow[preset]`): the underside shader adds bright glints on the rings' own slope |

The rings are tracked even while the local head is dry. A world's own top-surface water shader can show them:
`#include "UnderwaterRipples.cginc"` (relative path from that shader) and add `UW_Rings(worldPos.xz)` to its
normal's x and z (the underside reads the same slope with the normal pointing down). Not built into any world
water shader here.

A world sound control that changes the muffled sources' volumes calls `_CaptureBaseVolumes` on `UnderwaterFX`
afterwards, so surfacing restores the player's level and not the one at Start.

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
| `dive` (walk-in from the nearest shore to the deepest point and back, crouch eye height) | `flipsOn=1 flipsOff=1`, `amountDirectionReversals=1`, `EXACT_RESTORE=True`, `overlayActive=False`; `ringsPushed` rises (one step-in ring plus wake rings while wading) |
| `splash` (`Start("splash", dir, 1600, 900)`: the local player drops in from 1.2 m above the deepest point, then its head goes under 2 m away) | `ringsPushed` +1 within ~1 s, `rings global length=8`, newest ring at the drop point with amplitude ≥ 0.9; frames `splash_0.4s` … `splash_2.4s` show a bright ring spreading over the underside and bending the window, `splash_4.5s` is calm again; `ringBoost` > 0 in the first frames and 0 at 4.5 s |
| `shots` (`Start("shots", dir, 1600, 900)`; optional `posesJson`) | per pose `_0_above` (the camera 1 m above the water, head dry: the water looks as it did before install, overlay and underside inactive), `_1_subtle`, `_2_strong`. Default poses at the deepest point: across, up at the surface (Snell window), toward the shore, down at the bed. Make one contact sheet (rows = poses, columns = above / Subtle / Strong) for the user's strength pick |
| `audio` | submerged: filter on at the preset cutoff, volume ×0.794 (−2 dB); surfaced: filter off, volume exactly as before. A scene without AudioSources reports 0 |
| `perf` | overlay + underside on vs off at the first pose; record both medians |

`sweep` and `bob` must log `ringsPushed total=0` (the feet never cross the surface), so the ripple code adds no
switches or flicker there.

Also check: console clean (no `error CS`, no Udon exceptions); the `UnderwaterFX` behaviour has sync None; for
Exp or Linear worlds, the submerged density (or start/end) matches the table above. Save the scene with 0
`__*__` objects: the capture camera `__UWCapCam__` lives only in play mode. Then the C.2 dressing-reviewer
review: it judges the frames, the contact sheet and the job logs.

## Cost

While submerged: +2 draws (the overlay quad with one GrabPass copy, and the underside quad). Measured on a
pond scene in the editor (render + GPU sync, 4×MSAA): 5.02 vs 5.13 ms at 1920×1080 (within the ±0.4 ms
noise), and 4.64 vs 4.35 ms with Strong at 2560×1440. On land the effect objects are inactive and `Update`
does one head-vs-box test per volume. No depth texture, no extra camera, no RenderTexture.

Ripples: the underside and the overlay evaluate the slope field per pixel (7 sine trains plus 8 ring slots); the
overlay only where the eye looks up through the surface. Udon: up to `playersPerFrame` (8) player samples per frame,
one `GetPlayers` per round, one shader array upload per new ring, one vector per frame while a ring lives; the
state arrays are allocated once in `Start`. Not measured yet: measure `perf` and the Udon update time with 1 and
80 ClientSim players before shipping a crowded world.

## Limits

- **No depth-based fog, foam or edge fade.** VRChat worlds have no camera depth texture unless a realtime
  shadowed light makes one, and baked worlds have none. Distance falloff comes from the scene fog on every
  shader that applies Unity fog. Shaders that fog from their own uniforms (radial fog, see
  `.omp/knowledge/notes/fog-must-be-radial-and-shader-driven-for-mirrors.md`) ignore the swap unless you drive
  those uniforms too. The skybox is not fogged; it shows only through the Snell window, tinted by the overlay.
  Everything else it would show is covered by the **far dome** (`UnderwaterDome.shader.txt`, child `Dome` of the
  root, `fx.dome`): a 100 m cube that follows the camera, in the current scene fog colour, drawn before the
  skybox and after the opaque geometry, so only pixels no geometry covers are filled (the underside quad ends at the
  far clip plane and a sea has no bed past its last tile: without the dome the unfogged sky and the far
  headlands show below the horizon "like glass"). The Snell cone (above ~38° elevation) is left open.
- **The Snell window is approximated:** a smoothstep on the view angle (window up to ~48° from vertical), bent by
  a screen-space shift of the grabbed image instead of real refraction, and no reflections. Strong's caustics are
  projected on one flat plane at the median bed height, so over shallow boulders they lie flat and slide as the
  head moves; they fade out between 2 and 4 m from the eye (where the real bed can be far from the plane, e.g. a
  steep coast, the net would otherwise float over open water).
- **Sort order:** the underside quad is queue Transparent+50 (after world transparents, before the overlay at
  Transparent+100). A world-space UI canvas (UI/Default: queue 3000, no fog keywords, e.g. an entry board) is
  therefore covered by the underside like any fogged opaque object. A renderer with a custom queue above 3050
  would still draw crisp over the water view: `Install` ends with `ScanTransparents()` (also callable alone) that
  lists such renderers and the number of world-space canvases.
- **Rings are not physical:** one ring per entry, no spray or foam, no interaction between rings, flat-water
  speed everywhere; with more than 8 entries within 3 s the oldest rings vanish early. Feet crossing the surface
  are sampled every ~0.05–0.1 s, so a player who touches the water for less than that can be missed.
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

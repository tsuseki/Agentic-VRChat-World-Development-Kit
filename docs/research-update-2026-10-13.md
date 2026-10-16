# Kit update from online research, 2026-10-13

We read four kinds of source and compared each tip against the kit:
- the official VRChat creator docs and SDK release notes (3.6–3.10.5);
- about 40 GitHub/GitLab world tools;
- ask.vrchat.com and Canny threads;
- creator guides, including Japanese note.com, CGWORLD and Qiita articles.

A tip was **rejected** if it was outdated (SDK2, Unity 2018/2019, pre-VPM installs, archived tools) or broke a workspace rule (realtime or Mixed lights, prop colliders, stations, pickup settings).

Reddit returned 403 or a login wall, so nothing below comes from Reddit.

Full research reports with sources and verdicts were session artifacts: `research-OfficialDocs.md`, `research-GitHubTools.md`, `research-CommunityThreads.md`, `research-TutorialsGuides.md`. Each source is now cited in the relevant skill's `SOURCES.md` and in `.omp/CREDITS.md`.

## New: Android / iOS skill

- **`skills/vrchat-android-worlds/`** (new).
  - PC stays primary; an Android/iOS version is an optional port of the finished PC world.
  - Covers what to decide at intake, port-friendly choices per stage, a port workflow, mobile budgets and a gotchas table.
  - The port workflow covers mobile shaders, ASTC overrides, setting lightmap and HDR-cubemap encoding to High, EasyQuestSwitch, Build & Test on a device over ADB (and over VTP for iOS), and uploading to the same blueprint ID.
  - The SDK facts were checked read-only in the open editor. One example: the SDK refuses mobile uploads over 100 MiB compressed.
- **Intake.** `intake.md`, `templates/WORLD.template.md` and `.omp/AGENTS.md` no longer say "PC only". Intake now asks Android yes/later/no and whether mobile shaders are allowed. `AGENTS.md` has a routing row for the new skill.
- **Mobile section of `unity-vrc-world-sdk-3`.** Wrong lines in `performance.md` and `SKILL.md` were corrected:
  - "Quest first";
  - Mixed/realtime lights allowed;
  - Unity `Mobile/*` shaders;
  - a "Quest emulator";
  - unsourced draw-call bands, now replaced by Meta's numbers.

## Corrections: the kit was wrong

| Where | Was | Now |
|---|---|---|
| `unity-vrc-world-sdk-3/references/layers.md`, `SKILL.md` | Pickup layer collides with players; PickupNoEnvironment collides with players; IgnoreRaycast ignored by all raycasts | Pickup does not collide with players; PickupNoEnvironment collides only with Pickup; VRChat's own raycasts still hit IgnoreRaycast. Checked against the `DynamicsManager.asset` of three projects |
| `unity-vrc-udon-sharp` image loading (`image-loading-vram.md`, `web-loading.md`, `api.md`, CHEATSHEET) | `Dispose()` does not free the texture, so you must `Destroy()` it | `IVRCImageDownload.Dispose()` frees its texture (official docs). The samples also no longer blank the image during a swap |
| `upload.md`, `components.md` | Friends/Friends+ listed as world release states | A world is only Private or Public; capacity is clamped to 1–80. Community Labs rules added |
| `audio-video.md`, `components.md` | Linear spatial-audio falloff; Near 1–5 m in examples | Roughly inverse-square falloff; Near = 0; world sources get +10 dB |
| `performance.md` | Smallest Occluder 5–10 m | 2–6 m |
| `sdk-migration.md` | Toon Standard is avatar-only | Toon Standard also works in worlds, but has no lightmap support |

## Added tips (by area)

**Lighting**
- `bakery-light-baking`:
  - a zero-light baseline bake to find uncontrolled light;
  - gradient emission on visible lamp faces, plus concealed cove/cornice fill;
  - a "Unity shine" row: specular occlusion needs Filamented, ORL or Graphlit, offered only on request.
- `lighting.md`: give shaders a depth texture with `VRCCameraSettings.ScreenCamera.DepthTextureMode` instead of a "depth light" (soft water edges, depth fog).
- Notes:
  - Light Volumes: 2.x scope, keep Bakery "compress volumes" off, setup limits.
  - GLIM: v0.8 status.
  - A pre-bake sweep that clears ContributeGI on mirrors and video screens (they make Progressive loop 0→99 %).
  - New note: animate decor through a shader vertex offset so it stays lightmapped.

**Performance**
- `merging.md`: occlusion authoring (EditorOnly proxy occluders, Occlusion Areas per island, an OcclusionPortal on real doors, no giant occludees).
- `draw-call-attribution.md`: probe blend-weight and instancing batch traps.
- `texture-caps.md` and `perf-optimizer`: attribute upload size with the VRWorld Toolkit build report.
- `perf-optimizer` and the FBX note: strip Animators from static props.
- `blender-optimizer`: atlas tiling surfaces by cutting the mesh at each repeat and stacking the squares on one cell.
- `performance.md`: in-client debug-view table.

**SDK and upload**
- Stickers and user Items: which layers they use, mirrors, Udon physics masks.
- Settings that exist only on the website (content toggles, World Debugging, Avatar Scaling, Video Player Allowed Domains).
- Video URL trust rules for Public instances.
- A re-upload can kick players out of live instances when synced components change.
- Mirror inspector settings; TMP fallback fonts; UIShape Focus View.
- Tool entries:
  - LTCGI: opt-in, needs a user decision in WORLD.md;
  - VRWorld Toolkit;
  - AudioLink.
- Gotchas: stale `BAKERY_INCLUDED` / PPv2 define symbols; deprecation status of CyanTrigger, CyanPlayerObjectPool, NetworkedEventCaller, z3y/shaders and USharpVideo.
- Thumbnails: crop zones for the platform badge and the circular portal view.

**Udon**
- Multi-client Build & Test black-screen workaround.
- ClientSim known bugs, the PlayerData window, launch flags, and finding `halted` behaviours in the log.
- Persistence breaks for Network IDs above 10,000.
- A FieldChangeCallback setter must not read other synced fields.
- Player triggers can be skipped on teleport.
- Bandwidth: there is a per-behaviour overhead.
- Physics hits need `Utilities.IsValid`.
- `VRCShader` / `VRCGraphics` rules.
- New note: SmartObjectSync is in maintenance mode, and its example prefabs ship pickup proximity 2.

**Design**
- `spatial-design` §5.8 and `world-builder` C.2: a soundscape pass. Each area gets a 3D ambience bed (not 2D) plus placed emitters, and the agent walks the routes listening for problems.
- Walked surfaces must be smooth.
- Functional UI is dressed in the world's own materials.

## Rejected on purpose
- A weak realtime directional light so avatars look right. This is common Japanese practice, but it breaks the fully baked rule; use probes or Light Volumes instead.
- Mixed sun light; volumetric fog that needs a realtime light; auto-on mirrors.
- 2D ambience; MeshCollider on walked surfaces; VRCChair samples; AutoHold Yes.

## Follow-up decisions (same day)
- **Collider rule changed (your call).** Big furniture now gets one always-on `SolidCollider` box
  from the floor to the top surface: dining, kitchen and other big tables, counters, islands, bars,
  cabinets, sideboards, dressers, wardrobes, bookcases and appliance-sized pieces. Small furniture
  (chairs, stools, couches, armchairs, coffee, side and bedside tables) stays walk-through, and beds
  and couches keep only the lie-down collider.
  - Updated: `RULES.md`, `AGENTS.md`, the world-pipeline skill, `world-builder`, `dressing-reviewer`,
    `world-architect` (plan JSON `solid: true`), the WORLD template (Solid column and C.2 row),
    spatial-design, the android skill, `layers.md` and one note.
  - `WorldAudit` (package 0.3.0) now accepts a `SolidCollider` and counts them on a
    `[SOLID_FURNITURE_COLLIDERS]` line.
  - This also answers the old pickup question for big tables: pickups rest on them now. A pickup
    placed on a small table still falls to the floor.
- **SDK versions:** you upgrade the SDK before every upload, so the 3.10.4 / 3.10.5 gap is not an
  issue.

## Open questions for you
1. **`knowledge/notes/runtime-lightmap-swap-in-vrchat.md`** assumes Bakery's `ftLightmapsStorage` runs in-client. VRChat's component allowlist does not list it, so this needs one in-client test before anyone relies on the note.
2. **Shader choices.** LTCGI and other shaders (Filamented/ORL/Graphlit, VRChat/Mobile for ports) stay off until you approve them for a world.

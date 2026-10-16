# Sources: unity-vrc-world-sdk-3

Bibliography and attribution for `.omp/skills/unity-vrc-world-sdk-3/SKILL.md`. Not needed to use the skill; open it only to check
where a claim or tag came from. Sections are grouped by the file that cites them.

## `SKILL.md`

Source: adapted from [niaka3dayo/agent-skills-vrc-udon](https://github.com/niaka3dayo/agent-skills-vrc-udon) (MIT, see [LICENSE.txt](LICENSE.txt)).

## `references/components.md` — WorldQualitySettings

Sources: [official quality settings reference](https://creators.vrchat.com/worlds/udon/vrc-graphics/vrc-quality-settings/),
[SDK 3.10.5 release notes](https://creators.vrchat.com/releases/release-3-10-5/),
final SDK `Samples/VRCQualitySettings/Scripts/WorldQualitySettings.cs` and its
`Editor/WorldQualitySettingsEditor.cs`.

## `references/audio-video.md` — video players

Source: [official VRChat video documentation](https://creators.vrchat.com/worlds/udon/video-players/) ([GitHub source](https://github.com/vrchat-community/creator-docs/blob/main/Docs/docs/worlds/udon/video-players/index.md)), reviewed 2026-09-12.

URL trust rules (allowlist, Video Player Allowed Domains, HTTPS on Android, faststart, AVPro channel cap, sample sync
player ownership): [www-whitelist](https://creators.vrchat.com/worlds/udon/video-players/www-whitelist) (updated
2026-07-14), read 2026-10-13.

## `references/audio-video.md` and `references/components.md` — VRC_SpatialAudioSource falloff

Source: [vrc_spatialaudiosource](https://creators.vrchat.com/worlds/components/vrc_spatialaudiosource) (updated
2024-12-10): roughly inverse-square default falloff, Near = 0 recommendation, +10 dB world gain, init-only values.
ClientSim left-channel caveat: RavenWorks, [Canny "Stereo audio missing a channel in ClientSim"](https://feedback.vrchat.com/sdk-bug-reports/p/stereo-audio-missing-a-channel-in-clientsim)
(2026-10-12, no status yet).

## `references/layers.md` — collision corrections, stickers and items

Sources: [worlds/layers](https://creators.vrchat.com/worlds/layers) (updated 2026-08-17),
[worlds/items](https://creators.vrchat.com/worlds/items) (2025-06-12),
[Developer Update 13 March 2025](https://ask.vrchat.com/t/developer-update-13-march-2025/42053) (per-instance
sticker/print toggles). Collision matrix verified 2026-10-13 against `m_LayerCollisionMatrix` in Airship, Penthouse and
treehouse `ProjectSettings/DynamicsManager.asset`.

## `references/components.md` — mirror inspector, VRC_UIShape, TextMeshPro, capacity

Sources: [vrc_mirrorreflection](https://creators.vrchat.com/worlds/components/vrc_mirrorreflection) (2024-07-31),
[release 3.10.2](https://creators.vrchat.com/releases/release-3-10-2/) and
[release 3.10.3](https://creators.vrchat.com/releases/release-3-10-3/) (mirror material instance, onPreCull);
[vrc_uishape](https://creators.vrchat.com/worlds/components/vrc_uishape) (2025-05-06);
[textmeshpro](https://creators.vrchat.com/worlds/components/textmeshpro/) (2024-05-21);
capacity clamp from local SDK source `com.vrchat.worlds/Editor/VRCSDK/SDK3/VRCSdkControlPanelWorldBuilder.cs` (3.10.4,
`WORLD_MAX_CAPAITY = 80`).

## `references/upload.md` — release status, Community Labs, network compatibility, website-only settings

Sources: [creating-your-first-world](https://creators.vrchat.com/worlds/creating-your-first-world) (2026-04-16),
[submitting-a-world-to-be-made-public](https://creators.vrchat.com/worlds/submitting-a-world-to-be-made-public)
(2024-02-13; performance tips only),
[VRChat Community Labs](https://docs.vrchat.com/docs/vrchat-community-labs) (updated 2025-11-13),
[networking/compatibility](https://creators.vrchat.com/worlds/udon/networking/compatibility) (2025-11-13),
[networking/events "Mismatched World Versions"](https://creators.vrchat.com/worlds/udon/networking/events) (2026-06-17),
[world-debug-views](https://creators.vrchat.com/worlds/udon/world-debug-views) (2026-01-29),
[player-avatar-scaling](https://creators.vrchat.com/worlds/udon/players/player-avatar-scaling) (2026-04-28),
[Canny #1602](https://feedback.vrchat.com/feature-requests/p/1602-some-of-default-instance-settings-set-by-a-world-creator-must-be-respected)
(world defaults vs instance settings, open). Capacity clamp: local SDK source as above.

## `references/community-world-tooling.md` — Choose by problem

Sources: [README](https://github.com/Sacchan-VRC/MS-VRCSA-Billiards), [release 1.14](https://github.com/Sacchan-VRC/MS-VRCSA-Billiards/releases/tag/1.14), [root inventory](https://api.github.com/repos/Sacchan-VRC/MS-VRCSA-Billiards/contents/), [repository metadata](https://api.github.com/repos/Sacchan-VRC/MS-VRCSA-Billiards).

## `references/community-world-tooling.md` — VizVid (repository VVMW)

Sources: [README](https://github.com/JLChnToZ/VVMW), [manual for v1.8.0+](https://xtlcdn.github.io/VizVid/docs/), [package manifest](https://github.com/JLChnToZ/VVMW/blob/master/Packages/idv.jlchntoz.vvmw/package.json), [1.8.0 release](https://github.com/JLChnToZ/VVMW/releases/tag/1.8.0), [MIT license](https://github.com/JLChnToZ/VVMW/blob/master/Packages/idv.jlchntoz.vvmw/LICENSE).

## `references/community-world-tooling.md` — GI Tweaks

Sources: [README](https://github.com/pema99/GITweaks), [manifest](https://github.com/pema99/GITweaks/blob/master/package.json), [0.1.3 release](https://github.com/pema99/GITweaks/releases/tag/0.1.3), [license](https://github.com/pema99/GITweaks/blob/master/LICENSE), [bundled Harmony license](https://github.com/pema99/GITweaks/blob/master/Editor/Dependencies/Harmony/LICENSE.txt).

## `references/community-world-tooling.md` — XatlasLightmap: chart packing, not “install xatlas for Bakery”

Sources: [README](https://github.com/z3y/XatlasLightmap), [manifest](https://github.com/z3y/XatlasLightmap/blob/main/package.json), [editor provenance](https://github.com/z3y/XatlasLightmap/blob/main/Scripts/Editor/README.md), [v0.1.6 release](https://github.com/z3y/XatlasLightmap/releases/tag/v0.1.6), [MIT license](https://github.com/z3y/XatlasLightmap/blob/main/LICENSE), [bundled xatlas MIT license](https://github.com/z3y/XatlasLightmap/blob/main/Scripts/Editor/XatlasSource~/xatlas/LICENSE).

## `references/community-world-tooling.md` — LTCGI

Sources: [PiMaker/ltcgi README](https://github.com/PiMaker/ltcgi), [ltcgi.dev](https://ltcgi.dev/) (Controller,
Shadowmaps, FAQ; v1.7.x docs), [v1.7.3 release](https://github.com/PiMaker/ltcgi/releases/tag/v1.7.3) (2026-08-02),
VRCLibrary, [The VRChat Creation Compendium: Lighting](https://vrclibrary.com/wiki/books/the-vrchat-creation-compendium/page/lighting)
(opt-in/"use sparingly" framing), lilToon CHANGELOG (local package copy) for LTCGI support. Read 2026-10-13.

## `references/community-world-tooling.md` — VRWorld Toolkit, AudioLink

Sources: [oneVR/VRWorldToolkit README](https://github.com/oneVR/VRWorldToolkit),
[V3.5.0/V3.5.1 releases](https://github.com/oneVR/VRWorldToolkit/releases) (2026-10-02/08),
[llealloo/audiolink README](https://github.com/llealloo/audiolink) (3.1.2),
[VCC curated listing](https://packages.vrchat.com/curated). Read 2026-10-13.

## `references/performance.md` — Quest/Android sections

Tags used inline (full list and the Android workflow: `.omp/skills/vrchat-android-worlds/SOURCES.md`):

- **[VRChat Cross-Platform]** [Cross-Platform Setup](https://creators.vrchat.com/platforms/android/cross-platform-setup/) (updated 2026-09-15): "alpha cutout counts as transparency".
- **[VRChat Android Optimization]** [Android Content Optimization](https://creators.vrchat.com/platforms/android/quest-content-optimization/) (updated 2025-06-25): 100 MB limit, ~250k tris, keep lightmap resolution low.
- **[VRChat Video Allowlist]** [www-whitelist](https://creators.vrchat.com/worlds/udon/video-players/www-whitelist) (2026-07-14): Android plays HTTPS only; URL resolver available on Android per [video-players](https://creators.vrchat.com/worlds/udon/video-players/).
- **[Meta Device Comparison]** [Device-specific optimization](https://developers.meta.com/vr/resources/device-optimization-comparison/) (updated 2026-05-11): whole-frame draw calls < 100 (Quest 2) / < 200 (Quest 3).
- Mobile shader list (Standard Lite, Lightmapped, Particles Additive/Multiply; Toon Standard without lightmaps): [Android Content Limitations](https://creators.vrchat.com/platforms/android/quest-content-limitations/) (updated 2025-10-08).

## `references/audio-video.md` — Steam Audio

Steam Audio ship date and server-side tuning: VRChat client release notes
[2025.4.2](https://docs.vrchat.com/docs/vrchat-202542) (2025-12-03, Build 1768) and
[2025.4.2p1](https://docs.vrchat.com/docs/vrchat-202542p1); conversion caveats and "report these as bugs" list:
[Developer Update, December 4, 2025](https://ask.vrchat.com/t/developer-update-4-december-2025/47243).

## `references/layers.md` — user layer names overridden

Runtime evidence: [niaka3dayo/agent-skills-vrc-udon Issue #286](https://github.com/niaka3dayo/agent-skills-vrc-udon/issues/286)
(layer-dump script and output), [independent report](https://ask.vrchat.com/t/user-defined-unity-layers-raycasts-ignored-by-vrchat/47933);
upstream report [vrchat-community/creator-docs#303](https://github.com/vrchat-community/creator-docs/issues/303).

## `references/lighting.md` — VRCCameraSettings

[VRC Camera Settings](https://creators.vrchat.com/worlds/udon/vrc-graphics/vrc-camera-settings).

## `references/build-validation.md` — pipeline manager check

Local SDK source `VRCWorldPostBuildValidator.cs:17-45`.

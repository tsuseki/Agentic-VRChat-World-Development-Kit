# Sources: vrchat-android-worlds

Bibliography and attribution for `.omp/skills/vrchat-android-worlds/SKILL.md`. Not needed to use the skill; open it
only to check where a claim or tag came from. Sections are grouped by the file that cites them; a
source cited by several files is listed in full once, under the first file. All pages were read on
2026-10-13. creators.vrchat.com returns 403 to plain fetchers, so its pages were read with a browser
user agent (dates are the page's "Last updated") and cross-checked against the raw Markdown in
https://github.com/vrchat-community/creator-docs.

## `SKILL.md`

- **[VRChat Platforms]** VRChat, "Platforms", VRChat Creator Docs, updated 2025-10-08. https://creators.vrchat.com/platforms/ — device list per platform (Quest 2+, PICO 4+, Vive XR Elite, Android 10+, iOS 17+).
- **[VRChat Cross-Platform]** VRChat, "Cross-Platform Setup", VRChat Creator Docs, updated 2026-09-15. https://creators.vrchat.com/platforms/android/cross-platform-setup/ — platform switch, "switching again is much faster", EasyQuestSwitch recommendation, same blueprint ID, multi-platform publish, iOS → Android fallback, matching colliders tip, "alpha cutout counts as transparency".
- **[VRChat iOS]** VRChat, "iOS" (updated 2025-12-05) and "Setting up Unity for Creating iOS Content", VRChat Creator Docs. https://creators.vrchat.com/platforms/iOS/ — Android/Quest guidance and limits apply to iOS.
- **[VRChat Android Optimization]** VRChat, "Android Content Optimization", VRChat Creator Docs, updated 2025-06-25. https://creators.vrchat.com/platforms/android/quest-content-optimization/ — 100 MB world limit after compression, ~250k world triangles, 1k textures, Crunch vs memory, materials vs occlusion, baked lighting with low lightmap resolution, `Lightmapped` world shader, transparency.
- **[VRChat Android Limitations]** VRChat, "Android Content Limitations", VRChat Creator Docs, updated 2025-10-08. https://creators.vrchat.com/platforms/android/quest-content-limitations/ — `VRChat/Mobile` shader list and descriptions (Toon Standard, Standard Lite, Lightmapped, Supersampled UI), GPU Instancing, post-processing disabled, world-permitted components.
- **[VRChat Public Submission]** VRChat, "Submitting a World to be Made Public", VRChat Creator Docs, updated 2024-02-13. https://creators.vrchat.com/worlds/submitting-a-world-to-be-made-public/ — 45 FPS at spawn, "use mobile shaders on Android", ≤ 2 video players, mirrors off by default.
- **[VRChat Video Allowlist]** VRChat, "Video Player Allowlist", VRChat Creator Docs, updated 2026-07-14. https://creators.vrchat.com/worlds/udon/video-players/www-whitelist/ — Android plays HTTPS only.
- **[VRChat Video Players]** VRChat, "Video Players", VRChat Creator Docs, updated 2024-08-06. https://creators.vrchat.com/worlds/udon/video-players/ — URL resolver available on Android.
- **[VRChat Mirror]** VRChat, "VRC Mirror Reflection", VRChat Creator Docs, updated 2024-07-31. https://creators.vrchat.com/worlds/components/vrc_mirrorreflection/ — mirrors off by default, fewer reflect layers, lower resolution.
- **[VRChat Mobile Best Practices]** VRChat, "Mobile Best Practices", VRChat Creator Docs, updated 2024-08-02. https://creators.vrchat.com/platforms/android/android-best-practices/ — `OnInputMethodChanged` / `GetLastUsedInputMethod` / `VRCInputMethod.Touch`, `OnScreenUpdate`, touch UI advice.
- **[VRChat Android B&T]** VRChat, "Build and Test for Android Mobile", VRChat Creator Docs, updated 2026-09-15. https://creators.vrchat.com/platforms/android/build-test-mobile/ — ADB setup, Quest developer mode via Meta Quest Developer Hub, first-launch rules, Wi-Fi ADB, troubleshooting, scrcpy.
- **[VRChat iOS B&T]** VRChat, "Build and Test for iOS", VRChat Creator Docs, updated 2026-09-15. https://creators.vrchat.com/platforms/iOS/build-test-mobile/ — VRChat Test Protocol on port 9002, SDK IP Address, local-network permissions, Windows firewall rule, no VPN.
- **[VRChat Network Compatibility]** VRChat, "Network Compatibility", VRChat Creator Docs, updated 2025-11-13. https://creators.vrchat.com/worlds/udon/networking/compatibility/ — matching component and synced-variable types, count and order.
- **[VRChat Network ID Utility]** VRChat, "Network ID Utility", VRChat Creator Docs (creator-docs commit 2025-10-06). https://creators.vrchat.com/worlds/udon/networking/network-id-utility/ — network IDs link the platform versions; Import/Export utility for separate scenes or projects.
- **[SDK 3.8.1]** VRChat, "Release 3.8.1", 2025-05-22. https://creators.vrchat.com/releases/release-3-8-1/ — Toon Standard added (PC, Android, iOS; outline variant PC-only), iOS Build & Test added.
- **[SDK 3.9.0]** VRChat, "Release 3.9.0", 2025-10-06. https://creators.vrchat.com/releases/release-3-9-0/ — "UdonSharp scripts are now recompiled when you switch platforms"; "Using Standard Lite shaders in worlds no longer breaks lightmapping".
- **[SDK 3.10.5]** VRChat, "Release 3.10.5", 2026-09-04. https://creators.vrchat.com/releases/release-3-10-5/ — AudioLink support for Toon Standard including mobile; realtime reflection probes toggle on all platforms.
- **[Canny LV Toon Standard]** "[SDK 3.8.1-beta.4] Support VRC Light Volumes in Toon Standard", VRChat Feedback (Canny), opened 2025-05-19, still open with comments to 2026-08-30. https://feedback.vrchat.com/sdk-bug-reports/p/sdk-381-beta4-support-vrc-light-volumes-in-toon-standard
- **[EasyQuestSwitch]** Jordo (JordoVR), "EasyQuestSwitch", GitHub (now in the vrchat-community org), release 1.4.0 (2024-03-25). https://github.com/vrchat-community/EasyQuestSwitch — README and the `EQS_Types` list; VCC Curated listing (`vrchat.jordo.easyquestswitch` 1.4.0, read from https://vrchat-community.github.io/vpm-listing-curated/index.json).
- **[Bakery Troubleshooting]** Mr F (geom.io), "Troubleshooting: I have an Android project, and lightmaps don't look good", Bakery GPU Lightmapper wiki. https://geom.io/bakery/wiki/index.php?title=Troubleshooting — Lightmap Encoding High Quality, ASTC on, compression quality High or None.
- **[Unity Lightmap Data Format]** Unity Technologies, "Lightmaps: Technical information", Unity Manual 2022.3. https://docs.unity3d.com/2022.3/Documentation/Manual/Lightmaps-TechnicalInformation.html — Lightmap Encoding per platform group, dLDR clamps above 2, Android ASTC: dLDR/RGBM ASTC 3.56 bpp, HDR = ASTC HDR 3.56 bpp.
- **[Meta Device Comparison]** Meta, "Device-specific optimization (Quest 3 vs Quest 2)", Meta Horizon OS Developers, updated 2026-05-11. https://developers.meta.com/vr/resources/device-optimization-comparison/ — 72 Hz / 13.8 ms, draw calls < 100 (Quest 2) / < 200 (Quest 3), triangles < 750k / < 1.5M per frame.
- **[Meta Unity Perf]** Meta, "Testing and performance analysis", Meta Horizon OS Developers. https://developers.meta.com/horizon/documentation/unity/unity-perf — draw-call ranges by simulation load (busy: Quest 2 80–200, Quest 3 200–300).
- **[Meta Perf Checklist]** Meta, `skills/hz-unity-code-review/references/performance-checklist.md`, meta-quest/agentic-tools, GitHub, commit 2026-09-24. https://github.com/meta-quest/agentic-tools/blob/main/skills/hz-unity-code-review/references/performance-checklist.md — ASTC 6×6 default, 4×4 for UI/text, lightmaps 1024.
- **[Fujito 2026]** Fujito (一級建築士), "VRChatワールドはどのようにつくるのか？", note, 2026-01-24. https://note.com/fujito88/n/n19204b6ae044 — iOS upload path checked at the greybox stage; special shaders and post-processing avoided from the start so platforms look alike.
- **[in-house, SDK source]** (shortened to **[SDK source]** in `references/`) VRChat SDK 3.10.5 package source in the workspace (`com.vrchat.base`, `com.vrchat.worlds`): `WorldValidation.ShaderWhiteList` and `FindIllegalShaders` (yellow "unsupported shader" warning under `UNITY_ANDROID || UNITY_IOS`), `VRCSdkControlPanelBuilder.cs` (ASTC red error and Auto Fix; iOS-permission red error), `VRChat-Mobile-StandardLite.shader`, `ToonStandard.shader` (`skip_variants LIGHTMAP_ON`), `VRChat-Mobile-Lightmapped.shader`.
- **[in-house, measured]** Read-only `execute_code` reflection in the open workspace project (Unity 2022.3.22f1, 2026-10-13): `VRC.ValidationHelpers.GetAssetBundleSizeLimit(World, mobile)` = 104,857,600 compressed, −1 (none) uncompressed and on PC; `PlayerSettings` lightmap encoding Android = Low, iOS = Low, Standalone = High; HDR cubemap encoding Android = Low.

## `references/materials-and-textures.md`

Cites [VRChat iOS], [VRChat Android Limitations], [VRChat Public Submission], [SDK 3.9.0],
[SDK 3.10.5], [SDK 3.8.1], [VRChat Android Optimization], [VRChat Cross-Platform],
[Meta Perf Checklist], [Unity Lightmap Data Format], [Bakery Troubleshooting],
[Canny LV Toon Standard], [in-house, SDK source] and [in-house, measured] (all above).

## `references/port-workflow.md`

- **[VRCreators Mobile]** VRCreators, "Build and Test VRChat Worlds for Android and Quest" and "VRChat Quest and Mobile Compatibility Checklist", vrcreators.net, reviewed 2026-07-31. https://vrcreators.net/docs/vrchat/android-mobile-worlds-guide and https://vrcreators.net/docs/vrchat/quest-compatibility-checklist — Play Mode does not reproduce device performance; world vs avatar limits restated from the official docs.

Also cites [VRChat Cross-Platform], [EasyQuestSwitch], [SDK 3.9.0], [VRChat Mirror],
[VRChat Network Compatibility], [VRChat Network ID Utility], [VRChat Mobile Best Practices],
[VRChat Android Optimization], [VRChat Android B&T], [VRChat iOS B&T], [VRChat Public Submission]
and [in-house, SDK source] (all above).

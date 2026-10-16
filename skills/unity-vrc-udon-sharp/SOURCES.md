# Sources: unity-vrc-udon-sharp

Bibliography and attribution for `.omp/skills/unity-vrc-udon-sharp/SKILL.md`. Not needed to use the skill; open it only to check
where a claim or tag came from. Sections are grouped by the file that cites them.

## `SKILL.md`

Source: adapted from [niaka3dayo/agent-skills-vrc-udon](https://github.com/niaka3dayo/agent-skills-vrc-udon) (MIT, see [LICENSE.txt](LICENSE.txt)).

## `references/api.md` — VRCQualitySettings

Sources: [official quality settings reference](https://creators.vrchat.com/worlds/udon/vrc-graphics/vrc-quality-settings/),
[SDK 3.10.5 release notes](https://creators.vrchat.com/releases/release-3-10-5/).

## `references/assembly-definitions.md` — SDK 3.10.5 script creation

Sources: [SDK 3.10.5 release notes](https://creators.vrchat.com/releases/release-3-10-5/),
[Unity Version Defines](https://docs.unity3d.com/2022.3/Documentation/Manual/ScriptCompilationAssemblyDefinitionFiles.html#version-defines),
SDK `Integrations/UdonSharp/Editor/Compiler/CompilationContext.cs` and
`Integrations/UdonSharp/Editor/UdonSharpUtils.cs`.

## `references/image-loading-vram.md`, `references/web-loading.md`, `references/api.md`, `CHEATSHEET.md` — image `Dispose()` semantics

Source: [official image-loading docs](https://creators.vrchat.com/worlds/udon/image-loading) (2026-06-17):
`IVRCImageDownload.Dispose()` frees the texture; `VRCImageDownloader.Dispose()` frees all downloads and textures.
Replaces an earlier unsourced claim that `Dispose()` leaves the texture in VRAM.

## `references/api.md` — VRCShader / VRCGraphics

Sources: [VRCGraphics](https://creators.vrchat.com/worlds/udon/vrc-graphics/) (2025-04-15),
[VRChat shader globals](https://creators.vrchat.com/worlds/udon/vrc-graphics/vrchatshader-globals) (2026-02-23),
SDK 3.10.2 release notes.

## `references/testing.md`

- Multi-client black screen: Canny [1865 "2nd client always opens on black screen"](https://feedback.vrchat.com/bug-reports/p/1865-2nd-client-always-opens-on-black-screen-when-doing-build-test)
  (merged from "Can't Build & Test multiple clients any more", 2025-12-16 – 2026-08-14); workaround confirmed in
  [ask.vrchat.com 48714](https://ask.vrchat.com/t/local-world-testing-frozen-on-black-screen-anybody-else/48714) (2026-07).
- ClientSim known bugs: [vrchat-community/ClientSim issues](https://github.com/vrchat-community/ClientSim/issues) #118, #129, #130, #137, #142, #143.
- ClientSim PlayerData window: [creators.vrchat.com](https://creators.vrchat.com/worlds/clientsim/playerdata-editor-window) (2024-11-19).
- Launch flags, `halted` search: [world debug views](https://creators.vrchat.com/worlds/udon/world-debug-views) (2026-01-29),
  [debugging Udon projects](https://creators.vrchat.com/worlds/udon/debugging-udon-projects) (2025-04-04),
  [using Build & Test](https://creators.vrchat.com/worlds/udon/using-build-test).

## `references/persistence.md` — Network ID ceiling

Sources: Canny ["Networking breaks when assigning network IDs beyond an undocumented range"](https://feedback.vrchat.com/udon/p/networking-breaks-when-assigning-network-ids-beyond-an-undocumented-range) (2025-05-06, tracked);
[OpenNID](https://github.com/BobyStar/OpenNID) by BobyStar.

## `references/events.md`

- Player trigger/collision caveats: [player collisions](https://creators.vrchat.com/worlds/udon/players/player-collisions) (2025-04-09).
- FieldChangeCallback cross-field reads: Fax, ["UdonSharp Nitpicks"](https://wiki.vrchat.com/wiki/Guides:UdonSharp_Nitpicks) (VRChat community wiki);
  [ask.vrchat.com 40444](https://ask.vrchat.com/t/fieldchangecallback-execution-order/40444) (2025-01 – 03).

## `references/networking-bandwidth.md` — per-behaviour overhead

Source: [ask.vrchat.com 24903 "Question about Udon bandwidth"](https://ask.vrchat.com/t/question-about-udon-bandwidth/24903) (2024-06 – 07); single stress test, not a spec.

## `references/troubleshooting.md` — physics queries and protected objects

Sources: [Physics and layers](https://creators.vrchat.com/worlds/layers), [Items](https://creators.vrchat.com/worlds/items) (2025-06-12).

## `references/sdk-migration.md` — Toon Standard

Sources: SDK 3.10.5 release notes (2026-09-04), [Quest content limitations](https://creators.vrchat.com/platforms/android/quest-content-limitations).

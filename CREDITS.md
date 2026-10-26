# Credits

External sources this kit draws on, grouped by kind. Each entry lists creator, title, URL,
licence where known, and the kit files that use it. Inclusion of a tool, prefab or asset site
is a pointer to where the knowledge came from, not a warranty; check each source's current terms.

## Source list

Several guides, prefabs and tools below were first recommended in a community source list
compiled and shared by **Just_Rocs** (2025-08-27). The prefab and tool picks marked
*(Just_Rocs pick)* are their recommendations; the kit's notes on them are our own review.

## Inspiration

- **Ryan6-VRC** — [Atelier](https://github.com/Ryan6-VRC/atelier), MIT: an AI-operated workshop for
  VRChat avatar work. Its structure (bootstrap doc, routing docs, skills, an editor tools package
  with two-phase async calls) inspired AWDK; no code from it was copied. Used by
  `.omp/docs/bootstrap.md`, `.omp/docs/unity-tools.md`.
- **arjun988** — [blender-skills](https://github.com/arjun988/blender-skills), MIT: its
  reference-image-match workflow (reference analysis, camera match first, ranked gap list, capped
  self-iterations) and silhouette → panel breaks → detail order were adapted in our own words; no text
  or code copied. Used by `.omp/agents/blender-modeler.md`.

## Guides & documentation

- **Silent (s-ilent)** — Silent Cel Shading Shader wiki *(Just_Rocs pick)*:
  [Light Baking](https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Light-Baking),
  [Post Processing](https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Post-Processing),
  [Reflection Probes](https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Reflection-Probes).
  Used by `.omp/skills/bakery-light-baking/reference/silent-lighting-guides.md`,
  `.omp/skills/bakery-light-baking/SKILL.md`, `.omp/skills/vrchat-world-gotchas/SKILL.md`.
- **Geom (Mr F)** — Bakery GPU Lightmapper manual and wiki *(Just_Rocs pick)*:
  [Manual](https://geom.io/bakery/wiki/index.php?title=Manual),
  [wiki index](https://geom.io/bakery/wiki/index.php?title=Main_Page). Bakery itself is a paid,
  separately licensed product. Used by `.omp/skills/bakery-light-baking/` (SKILL.md and
  `reference/silent-lighting-guides.md`), `.omp/skills/lightmap-allocation/`,
  `.omp/skills/unity-vrc-world-sdk-3/references/community-world-tooling.md`.
- **Haï~ (hai-vr)** — Knowledge Index Notion guides *(Just_Rocs pick)*:
  [World Lighting](https://hai-vr.notion.site/World-Lighting-abc870d06dd647ac9fcd60fe60af05d9),
  [Miscellaneous World Tech](https://hai-vr.notion.site/Miscellaneous-World-Tech-ad2f49c88f444ec58c1cab3c33d469e4),
  [World Design](https://hai-vr.notion.site/World-Design-6a6b0f4a447e44078cd62422a886c203).
  Used by `.omp/skills/vrchat-world-gotchas/` (SKILL.md, `reference/hai-guides-refresh.md`,
  `reference/portal-blocking.md`, `reference/fetch-notion-page.py`).
- **VRChat** — [Creator Docs](https://creators.vrchat.com/) (source:
  [vrchat-community/creator-docs](https://github.com/vrchat-community/creator-docs)),
  [UdonSharp docs](https://udonsharp.docs.vrchat.com/), [client release notes](https://docs.vrchat.com/),
  [SDK packages releases](https://github.com/vrchat/packages/releases),
  [Ask forum](https://ask.vrchat.com/), [Canny](https://feedback.vrchat.com/),
  [wiki: Trusted URLs](https://wiki.vrchat.com/wiki/Trusted_URLs). Used throughout
  `.omp/skills/unity-vrc-udon-sharp/`, `.omp/skills/unity-vrc-world-sdk-3/`,
  `.omp/skills/vrchat-world-gotchas/`, `.omp/skills/vrc-udon-workflow/references/texture-decisions.md`,
  `AGENTS.md`.
- **Silent (s-ilent)**, with tips from the developers of *The Devouring* — [Occlusion Culling and You](https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Occlusion-Culling)
  (mirror: [VRChat Wiki](https://wiki.vrchat.com/wiki/Guides:Occlusion_Culling_and_You)). Used by
  `.omp/skills/vrchat-world-optimization/references/merging.md`, `.omp/skills/unity-vrc-world-sdk-3/references/performance.md`.
- **VRChat Wiki (community-written)** — [How to atlas your VRChat world](https://wiki.vrchat.com/wiki/Guides:How_to_atlas_your_VRChat_world),
  [World thumbnails](https://wiki.vrchat.com/wiki/Guides:World_thumbnails),
  Fax, [UdonSharp Nitpicks](https://wiki.vrchat.com/wiki/Guides:UdonSharp_Nitpicks). Used by
  `.omp/agents/blender-optimizer.md`, `.omp/skills/vrchat-world-thumbnail/SKILL.md`,
  `.omp/skills/unity-vrc-udon-sharp/references/events.md`.
- **Lura (QuickBrown Design Studio)** — [Unityライトベイクのいろは](https://cgworld.jp/article/2409-313T-vrchat02.html),
  CGWORLD, 2024-09-25. Used by `.omp/skills/bakery-light-baking/SKILL.md`.
- **れいんつ (laynts)** — [VRChat World「Chrono Cabin」ができるまで](https://note.com/laynts_/n/nbd10954de90d), 2024-08.
  **Arfox** — [KURAGARI COFFEEができるまで](https://note.com/arfox/n/n66cea5e16e0b), 2024-09. Used by
  `.omp/skills/vrchat-world-optimization/references/draw-call-attribution.md`,
  `.omp/skills/spatial-design/references/spatial-design.md`, `.omp/agents/world-builder.md`,
  `.omp/knowledge/notes/animate-decor-by-vertex-offset-to-stay-lightmapped.md`.
- **Kenomo** — [ワールド制作サウンドTips](https://kenomo.jp/worldsoundtips), 2023-10. Used by
  `.omp/skills/spatial-design/references/spatial-design.md` §5.8.
- **wata23** — [ワールドの軽量化](https://note.com/watahumi_mina/n/ned5a874f6c52), 2024-02. Used by
  `.omp/skills/vrchat-world-optimization/references/texture-caps.md`.
- **Fujito** — [VRChatワールドはどのようにつくるのか？](https://note.com/fujito88/n/n19204b6ae044), 2026-01. Used by
  `.omp/skills/vrchat-android-worlds/SKILL.md`.
- **GameDev.net** — [Design Guide for Room Scale VR](https://gamedev.net/tutorials/game-design/game-design-and-theory/design-guide-for-room-scale-vr-r4355),
  2017 (comfort principles only). Used by `.omp/skills/spatial-design/references/spatial-design.md`.
- **VRCLibrary** — [The VRChat Creation Compendium: Lighting](https://vrclibrary.com/wiki/books/the-vrchat-creation-compendium/page/lighting).
  **VRCreators** — [Android/mobile worlds guide](https://vrcreators.net/docs/vrchat/android-mobile-worlds-guide),
  [Quest compatibility checklist](https://vrcreators.net/docs/vrchat/quest-compatibility-checklist). Used by
  `.omp/skills/unity-vrc-world-sdk-3/SOURCES.md` (LTCGI), `.omp/skills/vrchat-android-worlds/references/port-workflow.md`.
- **Meta** — [Device-specific optimization](https://developers.meta.com/vr/resources/device-optimization-comparison/),
  [Unity performance analysis](https://developers.meta.com/horizon/documentation/unity/unity-perf),
  [agentic-tools performance checklist](https://github.com/meta-quest/agentic-tools/blob/main/skills/hz-unity-code-review/references/performance-checklist.md).
  Used by `.omp/skills/vrchat-android-worlds/`.
- **Unity Technologies** — [Unity 2022.3 Manual](https://docs.unity3d.com/2022.3/Documentation/Manual/)
  (reflection probes, assembly definitions, texture import, mipmap streaming, occlusion culling, GPU
  instancing, lightmap technical information). Used by
  `.omp/skills/bakery-light-baking/reference/silent-lighting-guides.md`,
  `.omp/skills/unity-vrc-udon-sharp/references/assembly-definitions.md`,
  `.omp/skills/vrc-udon-workflow/references/texture-decisions.md`,
  `.omp/skills/vrchat-world-optimization/references/`, `.omp/skills/vrchat-android-worlds/`,
  `.omp/skills/lightmap-allocation/` (Generating lightmap UVs, `ModelImporter.secondaryUVPackMargin`).
- **Microsoft** — [BC6H format](https://learn.microsoft.com/en-us/windows/win32/direct3d11/bc6h-format)
  (16-byte 4×4 blocks: 1 byte per texel). Used by `.omp/skills/lightmap-allocation/`.
- **NVIDIA Developer Forums** — [OptiX 6 broken on driver 591.44](https://forums.developer.nvidia.com/t/optix-6-0-0-is-broken-on-driver-591-44/353738).
  Used by `.omp/skills/bakery-light-baking/SKILL.md`.
- **Creative Commons** — [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/),
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) deeds. Used by
  `.omp/skills/worldbuilding-assets/references/community-asset-sources.md`.
- **Joost van Dongen** — [Interior Mapping: rendering real rooms without geometry](https://www.gamedeveloper.com/programming/interior-mapping-rendering-real-rooms-without-geometry)
  and the [Interior Mapping paper](https://www.proun-game.com/Oogst3D/CODING/InteriorMapping/InteriorMapping.pdf)
  (CGI 2008); **Polycount** thread [Interior Mapping in Spider-Man PS4](https://polycount.com/discussion/204601/interior-mapping-in-spider-man-ps4);
  **Alan Zucconi** — [Shader Showcase #9](https://www.alanzucconi.com/2018/09/10/shader-showcase-9/);
  **Insomniac Games** tech talk ([YouTube](https://www.youtube.com/watch?v=L2wr7vebb6Y)).
  Used by `.omp/knowledge/notes/interior-mapping-fake-rooms-behind-windows.md`.

## Third-party skills & code (licences retained in-folder)

- **niaka3dayo** — [agent-skills-vrc-udon](https://github.com/niaka3dayo/agent-skills-vrc-udon), MIT.
  Adapted as `.omp/skills/unity-vrc-udon-sharp/` and `.omp/skills/unity-vrc-world-sdk-3/` (`LICENSE.txt`).
- **sechiro** — [VRCUdonSkills-for-Codex](https://github.com/sechiro/VRCUdonSkills-for-Codex), MIT,
  pinned commit `1a19d149`. Adapted as `.omp/skills/vrc-udon-workflow/` (`LICENSE`,
  `SOURCES.md`, `references/texture-decisions.md`).
- **nemurigi** — [UdonSharp program-asset AssetPostprocessor gist](https://gist.github.com/nemurigi/dea7c0a1fb94f7b9cf1c36481a459ded), MIT.
  Used by `.omp/skills/unity-vrc-udon-sharp/assets/templates/UdonSharpProgramAssetAutoGenerator.cs`,
  `.omp/skills/unity-vrc-udon-sharp/references/editor-scripting.md`.
- **GitHub** — [Unity.gitignore](https://github.com/github/gitignore/blob/main/Unity.gitignore) (licence not recorded).
  Basis of `.omp/scripts/unity-world.gitignore`.

## Tools, prefabs & repos

- **Sacchan-VRC (fork of Pool Parlor by metaphira/Toasterly, originally Harry-T; Neko Mabel)** —
  [MS-VRCSA-Billiards](https://github.com/Sacchan-VRC/MS-VRCSA-Billiards), synced pool table, MIT-style
  root licence plus Unlicense module *(Just_Rocs pick)*.
- **JLChnToZ** — [VizVid (VVMW)](https://github.com/JLChnToZ/VVMW) video player, MIT *(Just_Rocs pick)*.
- **pema99** — [GITweaks](https://github.com/pema99/GITweaks) GI / light-baking tools, licence in repo,
  bundles Harmony *(Just_Rocs pick)*.
- **z3y** — [XatlasLightmap](https://github.com/z3y/XatlasLightmap) lightmap packing, MIT, bundles
  xatlas (MIT, Jonathan Young) via [guycalledfrank/xatlasLib](https://github.com/guycalledfrank/xatlasLib)
  *(Just_Rocs pick)*.

  The four above are reviewed in `.omp/skills/unity-vrc-world-sdk-3/references/community-world-tooling.md`
  (VizVid also in `references/audio-video.md`).
- **Generation backends** wired by `scripts/tool.py` (no code copied; API docs only): OpenAI Images
  API, Google Gemini API, [ComfyUI](https://github.com/comfyanonymous/ComfyUI) (GPL-3.0) with
  Qwen-Image-2512 / Qwen-Image-Edit-2511 (Apache-2.0) or [Qwen-Image 2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) (Qwen Research License, non-commercial; the shipped `scripts/comfyui/` workflows follow its Comfy-Org reference graph), [Tripo API](https://developers.tripo3d.com),
  [Meshy API](https://docs.meshy.ai), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) (MIT).
- **z3y** — [GLIM](https://github.com/z3y/glim) Vulkan GPU lightmapper. Used by
  `.omp/knowledge/notes/glim-vendor-portable-gpu-lightmapper.md`, `.omp/skills/lightmap-allocation/`.
- **MerlinVR** — [VRC-Bakery-Adapter](https://github.com/MerlinVR/VRC-Bakery-Adapter); **zulubo** —
  [SpecularProbes](https://github.com/zulubo/SpecularProbes). Linked from Silent's guide; mentioned in
  `.omp/skills/bakery-light-baking/reference/silent-lighting-guides.md`.
- **CoplayDev** — [unity-mcp](https://github.com/CoplayDev/unity-mcp) (MCP for Unity). Used by
  `.omp/docs/bootstrap.md`, `.omp/docs/hosts.md`, `.omp/scripts/install-unity-mcp.py`, `.omp/scripts/unity_mcp.py`,
  `.omp/scripts/README.md`.
- **ahujasid** — [blender-mcp](https://github.com/ahujasid/blender-mcp). Used by
  `.omp/docs/bootstrap.md`, `.omp/agents/blender-modeler.md`.
- **vrc-get** — [vrc-get](https://github.com/vrc-get/vrc-get) CLI and [ALCOM](https://vrc-get.anatawa12.com/alcom/)
  (VPM package managers); **VRChat** — [Creator Companion](https://vcc.docs.vrchat.com/). Used by
  `.omp/docs/bootstrap.md`, `.omp/docs/new-world.md`.
- **Astral** — [uv](https://docs.astral.sh/uv/). Used by `.omp/scripts/README.md`, `.omp/scripts/unity_mcp.py`.
- **TechAnon** — ProTV via VPM repo `https://vpm.techanon.dev/index.json`. Used by
  `.omp/knowledge/notes/free-cc0-asset-sources-and-download-apis.md`.
- **Sacchan-VRC** — [SaccFlightAndVehicles](https://github.com/Sacchan-VRC/SaccFlightAndVehicles),
  Udon aircraft and ground vehicles, licence in repo. Used by
  `.omp/knowledge/notes/saccflight-ground-vehicles-install-and-seating.md`.
- **REDSIM** — [VRC Light Volumes](https://github.com/REDSIM/VRCLightVolumes) (`red.sim.lightvolumes`),
  MIT (README, docs, releases, issue #95). Used by `.omp/knowledge/notes/vrc-light-volumes-traps.md`,
  `.omp/knowledge/notes/lightvolume-component-repushes-intensity.md`, `.omp/skills/fumo-plushie/SKILL.md`,
  `.omp/skills/lightmap-allocation/`, `.omp/skills/bakery-light-baking/` (workspace lighting
  standard), `.omp/docs/new-world.md` (install).
- **mworchel** — [xatlas-python](https://github.com/mworchel/xatlas-python), MIT, Python bindings of
  [xatlas](https://github.com/jpcy/xatlas) (Jonathan Young, MIT); installed by the user, not bundled. Used by
  `.omp/skills/fumo-plushie/scripts/` (`retopo_prep.py`).
- **PiMaker** — [LTCGI](https://github.com/PiMaker/ltcgi) ([docs](https://ltcgi.dev/)), MIT plus required
  attribution. **llealloo** — [AudioLink](https://github.com/llealloo/audiolink), MIT. **oneVR** —
  [VRWorld Toolkit](https://github.com/oneVR/VRWorldToolkit), MIT. Used by
  `.omp/skills/unity-vrc-world-sdk-3/references/community-world-tooling.md`,
  `.omp/skills/vrchat-world-optimization/references/texture-caps.md`, `.omp/agents/perf-optimizer.md`,
  `.omp/skills/vrchat-world-gotchas/SKILL.md`.
- **Silent** — [Filamented](https://gitlab.com/s-ilent/filamented); **orels1** —
  [ORL Shaders](https://shaders.orels.sh/docs/orl-standard/base-shader); **z3y** —
  [Graphlit](https://github.com/z3y/Graphlit) (successor of the archived [z3y/shaders](https://github.com/z3y/shaders)).
  Offered only on user request. Used by `.omp/skills/bakery-light-baking/`.
- **Silent (s-ilent)** — [Crispy Foliage](https://gitlab.com/s-ilent/crispy-foliage), MIT. Used by
  `.omp/knowledge/notes/fade-edge-on-leaf-cards-at-glancing-angles.md`,
  `.omp/skills/lowpoly-tree-generation/references/lessons-trees.md`, `.omp/skills/lowpoly-tree-generation/SKILL.md`;
  its wind (terrain-grass wave + Horizon Zero Dawn tremble) is ported into
  `.omp/skills/lowpoly-tree-generation/unity/SoftCrown.shader`.
- **vrchat-community** — [ClientSim](https://github.com/vrchat-community/ClientSim) issues,
  [EasyQuestSwitch](https://github.com/vrchat-community/EasyQuestSwitch). Used by
  `.omp/skills/unity-vrc-udon-sharp/references/testing.md`, `.omp/skills/vrchat-android-worlds/`.
- **MMMaellon** — [SmartObjectSync](https://github.com/MMMaellon/SmartObjectSync), [LightSync](https://github.com/MMMaellon/LightSync), MIT.
  Used by `.omp/knowledge/notes/smartobjectsync-maintenance-and-prefab-pickup-defaults.md`.
- **BobyStar** — [OpenNID](https://github.com/BobyStar/OpenNID). **JanSharp** —
  [VRCOcclusionUtils](https://github.com/JanSharp/VRCOcclusionUtils). Used by
  `.omp/skills/unity-vrc-udon-sharp/references/persistence.md`,
  `.omp/skills/vrchat-world-optimization/references/merging.md`.
- Deprecation status checked 2026-10 (not used): CyanTrigger, CyanPlayerObjectPool, NetworkedEventCaller,
  USharpVideo, MerlinVR/UdonSharp 0.x. Listed in `.omp/skills/vrchat-world-gotchas/SKILL.md`.

## Asset sources

- [Open3DLab](https://open3dlab.com/) — mostly game rips; check licences *(Just_Rocs pick)*.
- [Sketchfab](https://sketchfab.com/3d-models?features=downloadable) — downloadable models; many paid
  or needing fixes *(Just_Rocs pick)*.
- [TheBaseMesh](https://www.thebasemesh.com/model-library) — untextured CC0 base meshes *(Just_Rocs pick)*.

  The three above are reviewed in `.omp/skills/worldbuilding-assets/references/community-asset-sources.md`
  and listed in `.omp/skills/worldbuilding-assets/SKILL.md`.
- [Poly Haven](https://polyhaven.com/) (CC0), [ambientCG](https://ambientcg.com/) (CC0),
  [Quaternius](https://quaternius.com/) (CC0), [Freesound](https://freesound.org/) (per-sound licence;
  CC0 filter used). Used by `.omp/knowledge/notes/free-cc0-asset-sources-and-download-apis.md`,
  `.omp/knowledge/notes/seamless-ambient-audio-loop-ffmpeg.md`, `.omp/skills/worldbuilding-assets/SKILL.md`,
  `.omp/agents/asset-finder.md`.
- [coquelicotz / Imaginary Caravan](https://coquelicotz.booth.pm/), [spookyghostboo](https://spookyghostboo.booth.pm/),
  [Unity Asset Store](https://assetstore.unity.com/), [SweetHome3D free models](http://www.sweethome3d.com/freeModels.jsp),
  [TurboSquid free](https://www.turbosquid.com/Search/3D-Models/free), NoEmotion HDRs (`noemotionhdrs.net`).
  Used by `.omp/skills/worldbuilding-assets/SKILL.md`.
- Kenney (kenney.nl), cgbookcase (cgbookcase.com), ShareTextures, Poly Pizza (poly.pizza), OpenGameArt
  (opengameart.org), itch.io, CGTrader, Free3D, Booth.pm. Listed in `.omp/agents/asset-finder.md`.
- [Blendkit](https://www.blendkit.com/) (formerly BlenderKit) search/download API (`/api/v1/search/`,
  `/api/v1/downloads/`) and [licence terms](https://www.blendkit.com/docs/licenses/) (royalty-free, CC0).
  Used by `.omp/skills/worldbuilding-assets/scripts/blendkit.py`, `.omp/agents/asset-finder.md`.

## Research references

Sourced research the pipeline's layout agents read. Each skill keeps its bibliography in its own
`SOURCES.md` (e.g. `.omp/skills/spatial-design/SOURCES.md`, grouped by citing file); those lists are
the authoritative credits and are not duplicated here:

- `.omp/skills/spatial-design/sources/research/architecture-interior.md`
- `.omp/skills/spatial-design/sources/research/social-architecture.md` (Gehl, Whyte, Oldenburg,
  Alexander, Susanka, Sommer, residential, hospitality and cinema planning)
- `.omp/skills/spatial-design/sources/research/social-vr.md`
- `.omp/skills/clip-planes/references/clip-planes-and-precision.md` (VRChat camera settings,
  depth and float precision, far clip, fog and skybox backdrops), digested in `skills/clip-planes/SKILL.md`
- `.omp/skills/spatial-design/references/spatial-design.md`, the digest of the three spatial-design
  research files above

Other research references:

- **Douglas Pennant** — *Solving an Invisible Problem: Designing for Color-Blindness in Games*,
  [talk](https://www.youtube.com/watch?v=KbFs9ghIIEI) (linked from Haï's World Design guide). Used by
  `.omp/skills/vrchat-world-gotchas/`.
- **Google Fonts** — [Japanese subset filter](https://fonts.google.com/?subset=japanese). Used by
  `.omp/skills/vrchat-world-gotchas/`.

## Everything else

Material without a listed source comes from the maintainers' own production experience and
word-of-mouth from other creators.

# Sources: bakery-light-baking

Bibliography and attribution for `.omp/skills/bakery-light-baking/SKILL.md`. Not needed to use the skill; open it only to check
where a claim or tag came from. Sections are grouped by the file that cites them.

## `SKILL.md`

- **Official Bakery manual** — <https://geom.io/bakery/wiki/index.php?title=Manual>
  (the settings reference: samples/rays, Samples Multiplier, incremental export,
  Adjust Sample Positions, Fix Bright Edges, texels-per-unit ranges, probe modes)
- **Bakery wiki index** — <https://geom.io/bakery/wiki/index.php?title=Main_Page>
  (entry point for the other pages: Light types, Sectors, Volumes, Scripting, FAQ)
- Unity manual: Lightmap Encoding (Player Settings)
- **[Lura CGWORLD 2024]** — Lura (QuickBrown Design Studio), "VRChatのワールドのクオリティが爆上がりする！Unityライトベイクのいろは", CGWORLD, 2024-09-25 (Unity 2022.3.22f1), <https://cgworld.jp/article/2409-313T-vrchat02.html>
  (zero-light baseline step; gradient emitter faces and concealed cove/cornice fill)
- "Unity shine" symptom row — shader options read 2026-10-13: [Filamented](https://gitlab.com/s-ilent/filamented) (1.4.0),
  [ORL Standard base shader](https://shaders.orels.sh/docs/orl-standard/base-shader) (7.3.x),
  [Graphlit](https://github.com/z3y/Graphlit) (2.7.4)
- Driver R590+ / OptiX 6 removal — [NVIDIA's response to Bakery's developer](https://forums.developer.nvidia.com/t/optix-6-0-0-is-broken-on-driver-591-44/353738)

## `reference/silent-lighting-guides.md`

All four supplied guides were read in full (including the full paged Bakery manual):

- [Silent — Light Baking](https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Light-Baking): UV authoring, light costs, mixed lighting, probe placement, Bakery workflow, ringing. Retrieved through the site's `.md` version. WIP with Unity 2018/2019-era passages; prices, light limits, and performance claims are historical guidance.
- [Silent — Post Processing](https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Post-Processing): PPv2 layer/volume setup, tone mapping, bloom/exposure, VR comfort and effect cautions. Retrieved through `.md`; its Unity 2019 install recipe is not a current package-version pin.
- [Silent — Reflection Probes](https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Reflection-Probes): custom environment fallback, local/box-projected probes, batching, supersampling, specular proxies and changing lighting. Retrieved through `.md`; do not treat its simplified anchor/nearest-probe explanation or memory figures as universal.
- [Bakery — Manual](https://geom.io/bakery/wiki/index.php?title=Manual) ([reviewed revision 1871](https://geom.io/bakery/wiki/index.php?title=Manual&oldid=1871), page last edited 2026-06-26): complete settings, components, material compatibility, shader features, render-pipeline notes, upgrade and scripting sections. Installed-version source remains the authority for internal APIs.

Supplemental check: [Unity 2022.3 — Using Reflection Probes](https://docs.unity3d.com/2022.3/Documentation/Manual/UsingReflectionProbes.html) documents bounds/intersection, importance and blend modes. An attempted VRChat official post-processing URL (`https://creators.vrchat.com/worlds/scene/post-processing/`) returned HTTP 403 through the reader and **Page Not Found** in the browser; a site-restricted search found no replacement. Consequently, PP package/client compatibility below is not independently confirmed by a current official VRChat page. No supplied source was inaccessible. Embedded demonstration media and downloadable profiles/tools were not installed or runtime-verified.

2026-10-13 additions to §2: [MerlinVR/VRC-Bakery-Adapter README](https://github.com/MerlinVR/VRC-Bakery-Adapter) (v0.4, 2019-10-20);
VRChat [whitelisted world components](https://github.com/vrchat-community/creator-docs/blob/main/Docs/docs/worlds/whitelisted-world-components.md) (last commit 2025-11-25, no Bakery component);
specular-occlusion shaders: Filamented, ORL Standard, Graphlit (links above) and [z3y/shaders](https://github.com/z3y/shaders) (archived).

## `README.md` (credits)

Distilled from real debugging sessions on VRChat world projects (nighttime interior scenes, e.g. the ASMR Home World / Airship lighting passes), Unity 2022.3 + Bakery. All settings values, field names, and reflection recipes were verified working in those sessions.

Cross-checked against the official Bakery manual (<https://geom.io/bakery/wiki/index.php?title=Manual>), which corrected the sample-cost model (samples are the √ of ray count, so cost is quadratic) and supplied the `sampleDivisor` / incremental-export knobs. Internal field and method names were re-verified against the bundled `ftRenderLightmap.cs` source rather than taken from the wiki.

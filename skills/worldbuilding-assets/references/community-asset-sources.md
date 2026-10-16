# Community asset sources — reviewed 2026-09-12

Scope: the three supplied catalog URLs, relevant first-party information, and representative item pages. This is source research, not a complete inventory audit or Blender/Unity compatibility test. No assets were downloaded, imported, or installed. Recommendations below are workflow decisions; third-party recommendations are not personal user preferences.

## Decision order and rights gate

1. **Workspace policy:** search the `asset-library` from `.omp/local/config.md` and the existing local pack inventory (`.omp/local/assets-catalog.md`, when present) first. Local possession still requires checking the retained license/provenance; do not redownload a suitable owned asset.
2. Prefer a suitable original asset with a clear CC0 or CC BY grant. Of these three sources, TheBaseMesh is a useful first stop for editable generic geometry; Sketchfab offers broader finished/scanned assets; Open3DLab requires particularly careful item provenance and software checks.
3. For every candidate record title, creator/uploader, original source URL, item URL, license name/version and link, retrieval date, third-party credits, supplied formats, and planned edits. Preserve the actual license text with an eventual acquisition, not just a catalog badge.
4. **Privacy is not permission.** Private, friends-only, or unlisted worlds do not cure missing rights. Neither attribution, a free download, a staff pick, an uploader's CC tag, nor kitbash/remodel work automatically authorizes use of someone else's game assets. If provenance or authority is unclear, obtain applicable rights-holder permission or choose an original alternative.
5. CC0 waives the affirmer's copyright-related rights, not other people's rights or trademarks/patents, and supplies no warranty. CC BY requires appropriate attribution, a license link, and indication of changes; retain supplied notices and source links. NC and SA add separate conditions; ND is not suitable as a default for assets needing adaptations. Publishing is not automatically commercial, but public distribution needs permission and commercial uses need commercial rights. Do not reduce license analysis to whether the world earns money.

Primary licensing sources: [CC0 1.0 deed](https://creativecommons.org/publicdomain/zero/1.0/) and [CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/). These summaries do not replace each asset's applicable legal terms.

## Open3DLab

Supplied [filtered catalog](https://open3dlab.com/?query=&page=1&furry=0&nsfw=0&property_tag=&character_tag=&software_tag=&general_tag=&order_by=-last_file_date); [FAQ/about](https://open3dlab.com/about/); [terms, updated January 13, 2026](https://open3dlab.com/about/tos/).

**Observed/source facts**

- An independent resource host in the Open3DLab/SmutBase/SFMLab network. FAQ lists FBX, Blender, Maya, and 3ds Max uploads; site introduction also lists textures, sceneries and HDRIs. It is not a Unity-ready asset-pack guarantee.
- The supplied URL requests furry/adult exclusion and descending last-file-date order. Browser showed the Home surface with category/software filters, Last Updated sort, staff picks and recent updates; do not treat staff picks or sidebar content as a verified filtered result set. Visible staff picks included Resident Evil, Cyberpunk and Mass Effect environments. This proves such content exists, not that a measured majority of the entire site is ripped.
- FAQ says files are free to download for anyone. The sampled item offers free limited-speed servers and subscriber-only faster servers; terms allow use without registration with some features limited. The old skill's categorical claim that a free account is always required was unsupported. Actual file retrieval/login behavior was not tested.
- FAQ disclaims accuracy, quality and legality of user uploads and provides a takedown process. Terms require lawful uploads and prohibit infringing use. Generic terms reserve rights except where otherwise specified and describe personal/noncommercial sharing where expressly allowed: inspect the specific item grant; do not infer one uniform site-wide commercial license. Seek clarification when item text and general terms conflict.
- FAQ describes manual moderation and verified-uploader bypass, while terms contain generic no-moderation wording. Neither is evidence of rights clearance. Site access is adult-restricted even when browsing non-explicit assets.

**Representative item, not a recommendation:** [Zoe Baker's Trailer — Resident Evil 7](https://open3dlab.com/project/1d4a3074-6eec-497a-a4e4-22c1465b2ed6/), uploader AkkoNSFW, collaboration credited to QuickE. Page lists a roughly 598 MB `.blend` and **Beerware**, not CC. Its license panel explicitly says uploader-selected licensing is unverified and fan art may have additional terms. “Do whatever you want” is uploader text, not proof of authorization from underlying rights holders. No rights clearance established.

**Practical choice:** search original generic props/materials and verify authorship, texture origins, model version and any required Blender add-ons. Budget for shader rebuilding, scale/pivot correction and removing animation-only dependencies. Recognizable game-derived content should not be selected merely because it looks finished or carries a permissive tag.

## Sketchfab

Supplied [weekly downloadable, most-liked catalog](https://sketchfab.com/3d-models?date=week&features=downloadable&sort_by=-likeCount); [free-model landing page](https://sketchfab.com/features/free-3d-models); [license agreement](https://sketchfab.com/licenses).

**Observed/source facts**

- The catalog showed This week, Most liked, and **licenses Any**. `features=downloadable` is not a CC0/commercial-use filter. Results included weapons, branded vehicles and game interiors; popularity is not a provenance or realtime-performance review.
- The free-model landing page distinguishes downloadable Creative Commons models from royalty-free shopping on **Fab**. Read the actual item/acquisition license. The `/licenses` page describes standard/editorial purchase terms, not a replacement license for every free CC download and not proof that a Fab acquisition has those same terms.
- That standard/editorial agreement distinguishes editorial-only use from general use, restricts standalone redistribution, and disclaims warranties of rights/quality. An ordinary decorative hangout use is not automatically an editorial use. Do not assume “royalty-free” means CC0 or unlimited redistribution.

**Representative item, not a recommendation:** [Girls' Frontline 2: Exilium — Dormitory](https://sketchfab.com/3d-models/girls-frontline-2-exilium-dormitory-ae87e285656d491883d0c7bbd5ea8aff), VuckyZ / VuckyZ123, published September 5, 2026. Page states “extracted with Assets Studio, clean up in Blender,” lists about **66.7k triangles / 43.4k vertices**, and displays **CC Attribution-NonCommercial-ShareAlike**. This is direct evidence of extraction and extra license conditions; the tag does not establish game-owner permission. Download formats and runtime cost were not inspected.

**Practical choice:** start with category/search terms plus CC0 or CC BY license filtering, then examine each author's original source, description, model statistics and texture/material requirements. Use the 3D viewer for topology/backside/texture inspection, but a beautiful viewer render does not establish Unity shader parity, UV2, LODs, or VRChat performance. Confirm the actual download formats before choosing a Blender/Unity route; do not assume all items include FBX, source files or textures.

## TheBaseMesh

Supplied [model library](https://www.thebasemesh.com/model-library); [home](https://www.thebasemesh.com/); [FAQ](https://www.thebasemesh.com/faq); [about](https://www.thebasemesh.com/about).

**Observed/source facts**

- Creator Tim Steer describes a donation-supported library for modeling, game prototyping, previs and education. Catalog showed **1,254 assets** at review, with useful Furniture, Home, Architectural, Kitchen, Lighting and Industrial categories; counts are a dated snapshot.
- FAQ expressly licenses the models **CC0**, permits commercial use and makes attribution optional. The request not to put substantially unaltered meshes behind a paywall is framed as a spirit-of-sharing request, not an added mandatory CC0 condition. Preserve provenance nonetheless; CC0 does not guarantee third-party rights or asset quality.
- Homepage promises real-world scale and **basic UVs**, and markets clean topology. Treat these as publisher claims to inspect, not verified measurements. Basic texture UVs do not establish a separate nonoverlapping lightmap UV channel.
- Sample item pages explicitly list `.fbx`, `.obj`, `.glb`, and `Unwrapped: Yes`: [Air Vent 01](https://www.thebasemesh.com/asset/air-vent-01), **504 triangles**, Urban; [Abacus](https://www.thebasemesh.com/asset/abacus), **9,880 triangles**, Home. ZIP links were visible but not fetched. A seemingly simple prop can still be relatively dense.
- FAQ accepts donated FBX, OBJ, glTF, GLB **or Blender** files, prefers but does not require quads, and says submissions need not be unwrapped because topology may be revised. These are contributor input requirements, **not a guarantee that every download includes all those formats or a `.blend` file**. Donors agree to CC0; check an item's credits/source rather than assuming every mesh is solely Tim's work.
- Reviewed pages do **not** establish a catalog-wide guarantee of included PBR textures, authored Unity materials, texturelessness, rigs, LODs or lightmap UV2. Plan to author/adapt the final surface treatment and inspect the chosen package before estimating that work. Do not label every model textureless solely from the name “BaseMesh” or plain previews.

**Practical choice:** a strong candidate for generic blockout, kitbash starting geometry and props that will use the world's existing shared materials. For close-up hero props, evaluate silhouette, bevels, normals, UV distortion and actual texture readiness; CC0 plus a publisher quality claim is not a visual sign-off.

## Blender → Unity checklist (workflow guidance; not exercised here)

- Search the local library first and resolve item rights before acquisition. On eventual import, keep original archives/license notices and editable DCC sources outside `Assets`; import only needed runtime exports/textures. Import `.unitypackage` through Unity rather than copying the package into `Assets`.
- Open unfamiliar `.blend` files with automatic script execution disabled; inspect add-on/script dependencies instead of enabling them blindly. Check Blender version, missing external images and linked libraries.
- Measure real dimensions; correct units, forward/up axes and floor/wall mounting pivot. Apply transforms deliberately on export meshes; do not indiscriminately apply transforms to rigs. Check mirrored/negative scale, face normals, shading, holes, hidden duplicate geometry and unnecessary subdivisions.
- Count **triangles after modifiers/export**, material slots, renderers and texture memory. Remove irrelevant cameras/lights/rigs from static-prop exports. Share appropriate existing materials; do not collapse meshes across culling/interaction boundaries merely to reduce a counter.
- Inspect material UVs separately from lightmap UVs. Preserve suitable authored UV2; generate/repack nonoverlapping UV2 with padding when absent or unsuitable for baking. “Unwrapped” alone is not lightmap-ready.
- Prefer an explicit FBX export for a predictable existing Unity pipeline. OBJ is useful for static geometry but is not a full rig/material interchange. GLB/glTF needs a compatible importer already available in the target project or deliberate Blender conversion; do not silently install one. Export only intended objects and resolve external textures.
- Rebuild/verify materials in the target project's actual shader and render pipeline. Blender procedural nodes do not automatically become Unity materials; bake suitable maps where needed. Verify normal-map import, color versus data textures, roughness/smoothness conversion, channel packing, alpha mode and double-sided geometry. Do not assume liltoon/Poiyomi/Mochie support on every target platform.
- **Workspace policies:** use Unity MCP for open-editor changes; props/furniture/decor default to **no colliders**. Disable generated mesh colliders, strip imported prop colliders and primitive auto-colliders. Movement blockers use minimal boxes; never a MeshCollider on walked-on geometry. Stairs use one smooth ramp box. Explicitly requested pickups have their own tightly bounded collision exception, not a blanket prop exception.
- Strip imported `VRC_Station` / `VRCStation`; never add seating unless explicitly requested. Do not convert scenery into pickups/interactables by default. Set only appropriate static flags: Batching Static, ContributeGI and ReflectionProbeStatic serve different purposes, not a blanket “Static fixes performance” switch.
- In the actual world, verify dimensions/orientation, material appearance, UVs and player paths; measure target-platform cost. After a lighting bake, bake reflection probes immediately. Finish actual visual work through the stage reviewer (`dressing-reviewer` before the bake, `final-reviewer` after it); this research does not constitute a SHIP IT verdict.

## Access and evidence limits

- All three supplied catalogs were reached. Open3DLab reader initially substituted an unusable RSS feed; a browser recovered the Home/catalog controls and visible featured/recent content after its normal bot check. It did not establish the complete filtered result order. Open3DLab FAQ, terms and sample item were readable.
- TheBaseMesh catalog/FAQ/about and sample metadata were readable. Homepage reader also substituted RSS; browser recovered the homepage claims. No ZIP contents were inspected, so formats/UVs are item-page claims and materials remain package-dependent.
- Sketchfab catalog and license agreement were readable; free-model and sample-item reader requests returned bot-check HTML, then browser recovered both. An attempted Fab download-help URL (`https://support.fab.com/s/article/Downloading-3D-Models`) failed certificate validation in reader and showed page-not-found in browser; the old Sketchfab help URL (`https://help.sketchfab.com/hc/en-us/articles/201368589-Downloading-3D-models`) returned 404. No download-login or format guarantees were derived from these failed help pages.

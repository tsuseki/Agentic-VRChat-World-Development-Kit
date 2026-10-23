---
name: worldbuilding-assets
description: >-
  Find 3D assets — furniture, props, environment models, textures, materials — for
  VRChat/Unity world creation. Curated sources ranked by license safety, plus import
  and licensing guidance. Use whenever sourcing, searching for, recommending, or
  downloading models/textures/asset packs for a world project (furniture, props,
  environment pieces, textures, etc.).
---

# Worldbuilding Assets

Where to get 3D assets for VRChat worlds, ordered by how safe the license is. This file is the
decision layer: pick a source, understand the license, import it correctly. Your own catalog of
the `asset-library` (local packs and owned purchases) lives at `.omp/local/assets-catalog.md`
when present.

For the **2026-09-12 Open3DLab / Sketchfab / TheBaseMesh review**, per-item provenance
examples, licensing corrections and Blender → Unity checklist, read
[Community asset sources](references/community-asset-sources.md).

If nothing suitable exists, consider building a custom prop — see `.omp/skills/image-to-3d-props/SKILL.md`.

## License first — it decides everything

Every asset needs rights covering its intended use and distribution; monetized/commercial
uses also need commercial rights. Public does not automatically mean commercial, and
private does not mean permission-free. Sort sources by license before aesthetics:

| License | What you can do | Sources here |
|---|---|---|
| **CC0** | Broad copyright reuse, no attribution required; not a warranty or clearance of third-party rights | TheBaseMesh, Poly Haven, original CC0 libraries |
| **CC BY** | Credit, link the license, indicate changes and retain supplied notices; check version and provenance | per-item on Sketchfab and other hosts |
| **Uploader-declared license on game-derived assets** | Covers only rights the uploader can grant; private/unlisted use does not cure missing rights-holder permission | Open3DLab and Sketchfab examples |
| **Booth "free"** | Price is not permission. Read the item's 利用規約 (terms of use) for world use and redistribution limits | spookyghostboo, Nekoyama, other Booth shops |
| **Marketplace EULA** | Per-item/acquisition; inspect permitted uses, editorial restrictions and source redistribution terms | TurboSquid, Unity Asset Store, Fab |

Prefer original CC0 assets when suitable, but still check provenance, third-party rights
and package contents. No label removes all downstream risk.

## Check the local library first — the `asset-library`

If `.omp/local/config.md` names an `asset-library` (Assets), **look there before recommending a
download**: packs, world tooling and audio may already be present, and owned packs from
`owned packs` may be used in worlds (never redistributed). The inventory, when kept, is in
`.omp/local/assets-catalog.md`. Most packs are `.unitypackage` (import directly) or `.zip`/`.7z`
(extract into `Assets/`).

## Blendkit — search it second, from the shell

Blendkit (formerly BlenderKit) is installed as a Blender 5.1 extension and searchable without
Blender: `python .omp/skills/worldbuilding-assets/scripts/blendkit.py search "<item>" --max-faces N`,
then `download <id>` (GLB plus `blendkit.json` provenance under `<asset-library>/World/Blendkit/`
when the `ASSET_LIBRARY` environment variable is set, else `./Blendkit`; or `--out <dir>`).
Free-plan assets download anonymously; Full-plan assets need the user logged in to the add-on.
Licence `royalty_free`: use in published worlds without credit, never resell or redistribute the
asset (no Booth packs, shared prefabs). Models target Cycles: expect 4K–8K textures and no UV2;
search `faces` are mostly quads (tris ≈ 2×), measure with `blendkit.py inspect`. GLB textures are
WebP (Unity 2022.3 can't import them): route every pick through Blender to FBX + PNG.
Details: agent `asset-finder` §2.

## Go-to sources (start here)

1. **coquelicotz / Imaginary Caravan** — https://coquelicotz.booth.pm/ — **the default pick.**
   Lightweight furniture Sets 1–4, books, plants, and a CC0 material pack. **All CC0**,
   built specifically for VRChat, ZIP downloads (FBX + textures). Check each item's current terms.
2. **spookyghostboo** — https://spookyghostboo.booth.pm/ — Western creator, free furniture
   & interior prop packs plus free starter worlds. Note: modeled at **larger/real-world
   scale** — expect to scale down ~0.6–0.7× to real-world size (measure a door or chair
   first), then ×k (k = eye ÷ 1.6) like everything visible: furniture, props, buildings, trees
   and other environment pieces alike (spatial-design §5.9).
3. **Unity Asset Store** — https://assetstore.unity.com/ — rotating free assets, native
   `.unitypackage` import. E.g. **Furniture Mega Pack (Free)**:
   https://assetstore.unity.com/packages/3d/props/furniture/furniture-mega-pack-free-330002
4. **SweetHome3D free models** — http://www.sweethome3d.com/freeModels.jsp — huge low-poly
   furniture library (OBJ/DAE), great as filler/background props.
5. **TurboSquid free** — https://www.turbosquid.com/Search/3D-Models/free — filter to
   `.unitypackage`/FBX; read each model's license (free ≠ CC0).
6. **Sketchfab** — filter **Downloadable + license** (CC0 or CC-BY); credit CC-BY authors.
7. **Poly Haven** — https://polyhaven.com/ — CC0 models, textures and HDRIs (much of it is
   already in the local library; see import caveats below).
8. **Open3DLab** — https://open3dlab.com/ — free resource host (sibling of SFMLab/Smutbase).
   Mixed DCC formats and licenses; item pages offer free limited-speed mirrors alongside paid
   faster servers. Read the caveat below before selecting an asset for any world.
9. **TheBaseMesh** — https://www.thebasemesh.com/model-library — publisher-declared CC0,
   basic UVs and real-world scale; sampled items list FBX/OBJ/GLB. Useful editable generic
   geometry, not guaranteed finished materials or lightmap UV2. See the dated review above.

Aggregators for discovery: **pandagraph's free-asset guide** (note.com), **boothplorer.com/world-assets**,
**vr-items.me**. Functional Udon assets (video players, mirrors, teleporters, chairs, clocks) and
base room shells are listed in your `.omp/local/assets-catalog.md` when you keep one.

## Open3DLab caveat — verify provenance per item

The catalog includes recognizable game-derived models/environments alongside other resources.
Uploader-selected licenses are explicitly unverified by the site; a CC or Beerware label cannot
grant rights the uploader does not own. The same caveat applies to other community hosts.

- **Private is not permission:** private/friends-only/unlisted worlds, blockout and
  kitbash-then-remodel are not blanket exemptions. Obtain applicable rights-holder permission
  or select a clearly authorized original alternative.
- **Filter for suitability, then verify rights:** original generic props, HDRIs and materials
  can be good candidates, but an “original” tag is not conclusive evidence of authorship.
- The supplied browse URL requests adult/furry exclusion and newest file updates:
  `https://open3dlab.com/?query=&page=1&furry=0&nsfw=0&property_tag=&character_tag=&software_tag=&general_tag=&order_by=-last_file_date`
  Confirm visible filters/results; featured content and sidebars need not follow that order.
- Check exact file formats/software versions, dependencies, units and materials. DCC previews
  do not guarantee Unity shader compatibility. See the dated review for sampled item evidence,
  access limitations and the site's general-terms/per-item-license distinction.

## Booth access note

Booth (`*.booth.pm`) is age/region-gated and returns **HTTP 403 to automated fetches** — I
often can't open item pages directly. When you paste a Booth link I may not be able to read
it; give me the title/contents, or I'll rely on the catalog and web search. Downloading
requires a logged-in Booth account and manual click — I can't do that for you.

## Importing into a Unity world project

Most Booth/coquelicotz packs are **raw ZIPs of FBX + textures**, not `.unitypackage` — so:

1. Extract into `Assets/<PackName>/` inside the target world project.
2. Build materials yourself if none are included. **Use lilToon by default for prop materials**
   (the kit default; a world's brief or `.omp/local/AGENTS.local.md` may name another shader);
   use a different shader only when the user explicitly requests it.
3. Set only appropriate static flags; Batching Static is not a guaranteed performance win,
   and is distinct from ContributeGI and ReflectionProbeStatic.
4. Preserve suitable lightmap UV2 or generate/repack it when baking; material UVs are not UV2.
5. **Check scale and orientation** against measured scene dimensions before committing.
   Poly Haven FBXs commonly import at **1/100 scale** (set the model importer
   `globalScale = 100`); many are **Z-up** and center-pivoted. Verify actual scale and
   orientation in-scene. Generated/downloaded GLBs: seat and scale them per
   [image-to-3d-props §7](../image-to-3d-props/SKILL.md#7-scale-and-place-correctly).
6. Inspect triangles, material/renderer counts and texture memory; measure target-platform
   performance rather than assuming “low-poly” or catalog popularity means cheap.
7. **No prop colliders or seat stations:** strip imported furniture/decor colliders and
   `VRC_Station` / `VRCStation`. Add movement-blocking boxes only where necessary; never
   stations unless explicitly requested. See the full import checklist in the dated review,
   [Community asset sources](references/community-asset-sources.md).

Unity Asset Store items import as `.unitypackage` directly (Window → Package Manager → My
Assets, or double-click the download) and usually ship ready-made materials.

Import `.unitypackage` files through Unity, **never copy them into `Assets/`**. Check
`git status` after import: a package can overwrite existing files that share its GUIDs.

## 360 panoramas / skyboxes for a window view — match the CAMERA HEIGHT first

An equirectangular panorama nails the horizon at the height the photographer stood at. Put a
street-level HDRI outside a tower's window and the skyline looms *up* at the player with pavement
under the balcony; nothing — rotation, scale, fog — corrects it. Filter by viewpoint before taste.

- **CC0 (Poly Haven) has almost nothing from height.** Query the API directly:
  `https://api.polyhaven.com/assets?t=hdris&c=night` returns all 61 night HDRIs with categories,
  tags and resolution in one call, and thumbnails live at
  `https://cdn.polyhaven.com/asset_img/thumbs/<slug>.png?width=512`. Of those 61, `shanghai_bund`
  is the only real skyline and it is shot from a ground-level promenade.
- **NoEmotion HDRs** (150 free 15000×7500 panos, `noemotionhdrs.net`) — the Night set is entirely
  ground-level office parks and garages, and the licence is **CC BY-ND**: no derivatives, which
  a resize or cubemap conversion arguably is. Skip for game use.
- **Booth is the real source for high-viewpoint night city skyboxes** — JP world creators sell them
  precisely to answer "what goes outside the window", authored so the eye level reads right from a
  high floor. Search `booth.pm/ja/search/夜景 skybox` (the JP term finds an order of magnitude more
  than "night city skybox"). Prices ¥100–¥700; typical contents are an 8192×4096 equirect PNG plus
  a 6-sided 2048 set plus a pre-wired skybox material. Some sellers ship free daytime tiers and
  sample VRChat worlds to inspect before paying.
- **Booth returns 403 to plain HTTP fetches** — drive it with the `browser` tool. A spawned
  Chromium reads item pages, descriptions and variation tiers; preview images on
  `booth.pximg.net` download only with a `Referer: https://booth.pm/` header, and an in-page
  `fetch` of them is blocked, so collect the URLs in the page and download them from Node.
- Two acceptance checks before buying: does the pack include the **nadir** (photo panos shot from
  inside a building usually do not — fine behind glass, visible over a terrace parapet), and is it
  **AI-generated** (fine as a 200 m backdrop, mushy through a 5 m window).
- After assigning any skybox, **re-bake the reflection probes** — glazing reflects it.

Sourcing lessons checklist: [references/lessons-sourcing.md](references/lessons-sourcing.md).

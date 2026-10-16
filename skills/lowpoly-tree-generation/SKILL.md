---
name: lowpoly-tree-generation
description: Making custom low-poly stylised or realistic trees (olive, maple, cypress, birch, ficus, pine, any species) for VRChat/Unity worlds in Blender — scripted skeleton + tube bark + alpha-cutout leaf cards, image-gen leaf/bark textures, crown-proxy canopy normals, ~2.5–3.3k tris, FBX export and Unity import/lighting setup.
---

# Low-poly tree generation (Blender script pipeline)

Proven method: a family of 11 trees (6 olive variants, Japanese maple, Italian cypress, birch clump/single/weeping, ficus, stone pine) at **2.5–3.4k tris each**, gpt-image textures. The user liked the style ("custom olive style") enough to ask for a matching family. He **disliked toon-style trees** (a toon birch and an aspen were rejected) — aim realistic-textured, low-poly silhouette.

Everything is headless Blender **5.1** (run through the kit's `blender` tool, `python .omp/scripts/tool.py blender`) plus Python 3 with `numpy pillow scipy` for textures. Scripts are in `scripts/`; the Unity shader in `unity/`.

| Script | Runs in | Job |
|---|---|---|
| `tree_family_build.py` | Blender | species `CFG` → skeleton → bark tubes → leaf cards → UVs → canopy normals → FBX + .blend |
| `tree_uv.py` | (module) | uniform-texel cylinder UVs for bark, `stretch_stats` |
| `tree_normals.py` | (module) | crown-proxy normal transfer + card winding |
| `tree_finish.py` | Blender | re-run UV/UV2/normals/export on an existing or hand-edited `.blend` |
| `process_gpt_textures.py` | Python | key generated leaf sheets → RGBA; bark → tileable albedo + normal |
| `branch_atlas.py` | Python | 2×2 leaf-spray atlas with stem base pinned to cell bottom-centre + JSON |
| `check_key_spill.py` | Python | key-colour spill check on every mip |
| `tree_family_textures.py` | Python | fallback textures from CC0 scans (Poly Haven + ambientCG), pre-gpt pass |
| `prompts/*.txt` | — | the exact image-gen prompts used |

## Pipeline

```
B="python .omp/scripts/tool.py blender"   # headless Blender from .omp/local/tools.json
# 1 textures (see Textures)
python scripts/process_gpt_textures.py bark bark_src.png TEX/Olive_Bark_Albedo.png TEX/Olive_Bark_Normal.png 3
python scripts/branch_atlas.py TEX/Olive_Leaves_RGBA.png TEX/Olive_Leaves_Cards.json spray_a.png spray_b.png spray_c.png
python scripts/check_key_spill.py TEX/Olive_Leaves_RGBA.png
# 2 build (no LODs by default)
$B --script scripts/tree_family_build.py -- Olive --tex TEX --out Assets/Trees/Olive --blend Source/Olive [--qa qa.png] [--config my_species.py] [--lod1]
# 3 optional: after hand edits in the .blend
$B --blend Source/Olive/Olive_Tree.blend --script scripts/tree_finish.py -- Olive ellipsoid --out Assets/Trees/Olive [--sprig]
```
The build prints `STAT` lines (tris, bounds, bark UV stretch, card attach error, open edges, leaf normal spread) — read them, then render `--qa` and look at it.

### 1. Skeleton (`build_skeleton`)
- `stems=(count, lean, length, r0, r1, gnarl, base_spread)`: trunks fanned around the azimuth, bases spread out (multi-trunk olives 3–6 stems, spread 0.15–0.22 m). `lean_dir`/`lean_fan` = all trunks lean one way.
- `levels=[{n, at, ang, len, r, tip, gnarl, up}]`: children per parent, placed at fractions `at` along it, `ang`° off the parent, radius `r`× parent, `tip` end radius, `up` = phototropism (negative = weeping). `len_scale` 1.6 for olives' long sweeping limbs; `len_taper` shortens higher limbs (cypress).
- Gnarl uses **deterministic** `noise.noise()` at 3 offsets. `mathutils.noise.noise_vector()` is randomised per Blender session (three runs, three trees) — never use it, or an approved tree can't be rebuilt.
- `seed=None` → `pick_seed()` scores seeds 1–59 for centred crown, target width/height, no twigs below ground.

### 2. Bark mesh (`tube`)
- One tube per branch, ring by ring; sides 7 / 5 / 4 by depth. `lobe` (0.3–0.36 olive, 0.08 birch/ficus, 0.16 default) wobbles the trunk cross-section for a gnarled base; trunk base ring flattened to z=0.
- `taper=True`: each end narrows to 3 mm over its last 40 %, starting past the last child fork (so child bases never poke out). `caps=True`: 2 cm pointed cone on every end; child bases closed by a cone buried in the parent. No open rings, no flat discs.

### 3. Canopy cards (`crown`)
Material index 1, quads (or 2-quad V-folded cards, `fold` 0.08–0.1). Modes:
- `sprig` (olives, best result): every card's atlas stem-base point lands **exactly** on a branch axis (`sprig_card` + atlas JSON), every terminal end above `minz` gets a card, then `fill.frac` (≈0.45) of cards on inner limbs leaning to the crown axis to close gaps between clumps. 380–630 cards, size 0.75–0.85 m.
- `twig` (maple, birch): cards along depth≥1 twigs above `minz`, pointing outward (`out`) with vertical range `upr` (negative = hanging).
- `ellipsoid` (ficus, stone pine flattened `rad=(2.45,2.45,0.5)`), `spindle` (cypress profile with `peak`).
UV2 = Smart UV Project 66°, margin 0.01 (lightmaps); `UVMap` = textures.

### 4. Bark UVs (`tree_uv.cylinder_uvs`)
V = arc length / `TILE` (0.6 m per texture repeat), U = ring circumference / TILE; thick rings snap to whole wraps so the seam closes. Gives uniform texel density from trunk to twig (measured `stretch max/min` 1.2–2.1).

### 5. Canopy normals — see the section below.

### 6. Export
`export_scene.fbx(use_selection, apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Z', axis_up='Y', bake_space_transform=True, mesh_smooth_type='OFF', use_mesh_modifiers=True, add_leaf_bones=False, object_types={'MESH'})` — imports upright at 1:1 with custom normals intact.

## Canopy normals (crown-proxy transfer)
**Why:** leaf cards are flat alpha-cutout planes at random positions/orientations. With their own face normals each card catches light independently → a flat, noisy, obviously-card canopy (bright/dark speckle, cards flash as you walk around). Giving every leaf vertex the normal of a **smooth volume shaped like the crown** makes the whole canopy shade as one soft lit mass (lit side / terminator / shadow side) while the alpha keeps the leafy silhouette. Bark keeps its own normals.

**Before/after metric** (`leaf_normal_spread`, mean |dot(loop normal, face normal)|): 1.0 = flat cards; measured after transfer olive 0.45, cypress 0.59–0.63.

**Implementation (`tree_normals.transfer_crown_normals(ob, kind, inflate=1.05)`):**
1. `align_card_winding`: flip every card whose front faces into the crown (BVH nearest point on the proxy), else back-face-flipping shaders/Cycles turn half the cards' normals inward → near-black crown.
2. Proxy is fitted to the **leaf-vertex bounding box**: centre = bbox centre, half-extents = bbox half-size, × `inflate` 1.05. No separate centre offset or face-normal blend parameter exists (no blend = 100 % proxy normal).
3. `ellipsoid` / `capsule` → **analytic**: per leaf loop `n = normalize((p−c).x/rx², (p−c).y/ry², (p−c).z/rz²)` (ellipsoid gradient; for a sphere that's `normalize(p − c)`), written with `me.normals_split_custom_set(loops)`.
4. `hull` → icosphere shrink-wrapped (nearest surface point) onto the convex hull of leaf verts, Smooth ×8 at factor 1, inflated; then a **Data Transfer** modifier on the tree: loop data `CUSTOM_NORMAL`, mapping `POLYINTERP_NEAREST` (nearest face, interpolated), vertex group = leaf verts only, mix REPLACE 1.0 — **applied** (`modifier_apply`).
5. All faces set `use_smooth=True` (Blender 4.1+/5.x has no auto-smooth toggle; custom split normals just need smooth faces). Normals are baked into the mesh before export; FBX writes them.

**Which proxy per crown shape** (`proxy=` in CFG):
| Crown | Proxy | Used for |
|---|---|---|
| round / ball | `ellipsoid` (bbox-fitted; sphere if equal extents) | olives, ficus, single birch |
| columnar | `capsule` (tall ellipsoid, same analytic code) | Italian cypress |
| umbrella / flat-top | `ellipsoid` — the bbox fit squashes it automatically (z-extent small) | stone pine, acacia |
| clumpy / irregular | `hull` (shrink-wrapped smoothed hull) | Japanese maple, birch clump, weeping birch |
| conical (fir/spruce) | not built yet: add a cone kind — n = normalize(radial·cosα + up·sinα) with α the cone half-angle, or a cone mesh through the `hull` Data-Transfer path | — |
| weeping (willow) | `hull` already follows drooping sides; or an ellipsoid with lowered centre | weeping birch |
| multi-clump | not built yet: one proxy per clump (cluster leaf verts, fit each), assign each leaf vert the nearest clump's normal, blend near borders | — |

**Unity side:** FBX import **Normals: Import** (`normalImportMode: 0`), not Calculate — Calculate throws the transfer away. The two-sided shader must NOT flip these normals on back faces: `unity/FoliageCutout.shader` flips via `VFACE` by default (right for ordinary cards), so set **`_UseMeshNormalsBothSides = 1`** on canopy-normal leaf materials; flipping makes the crown patchy.

## Textures
**Leaves** (`prompts/olive_leaves_top.txt` is the approved one): botanical flat-lay, straight down, flat overcast light, no shadows, background **one uniform flat magenta #FF00FF** (chroma green #00FF00 for red/purple foliage like Japanese maple), ONE spray of 5–7 twigs fanning up from a single stem entering at the **exact bottom centre**, fills ~90 %, light overlap, upper leaf surfaces only (no silver undersides/flowers/fruit). Generate 3 variants (a/b/c).
- `process_gpt_textures.leaf(src, dst, key, soft=True)`: keyness = min(R,B)−G (magenta), threshold from border median ×0.45, soft alpha ramp, opening + speck removal (<60 px) + 1 px erosion, despill, then **colour of every non-opaque texel = nearest opaque core texel** (distance-transform dilation) so no mip shows key colour. `triple` = 3 plumes side by side for narrow sprays (cypress).
- `branch_atlas.py`: 2048² atlas, 4 cells of 1024², each spray uniformly scaled so its stem centroid (bottom 3 opaque rows) sits on the cell's bottom-centre, 16 px margin; JSON `{"cells":[{"rect":[u0,v0,u1,v1],"attach":[u,v]}]}` feeds `sprig` mode. Expect `stem_offset_px_after` ≈ 0, `border_alpha…` = 0.
- `check_key_spill.py`: per box-filtered mip, `magenta_px` must be **0** (edge spill ≤ ~50/255 was accepted).
**Bark** (`prompts/*_bark*.txt`): seamless orthographic unrolled bark, flat light, trunk vertical. `process_gpt_textures.py bark src albedo normal <strength>`: half-offset edge-blend tileable, 1024², OpenGL normal from blurred luminance (strength ~2–4).
Names the builder expects: `<tex>_Bark_Albedo.png`, `<tex>_Bark_Normal.png`, `<tex>_Leaves_RGBA.png`, `<tex>_Leaves_Cards.json`. Variants can share one texture set via `tex=`.

## Tri budgets (measured)
LOD0 2.5–3.4k (olive 3.3k: 1.8k bark + 1.5k leaf; cypress 2.6k: 0.6k + 2.0k). Optional LOD1 0.7–1k. Compare: the stock trees they replaced were 15–16k each.

**LODs: off by default.** In worlds under ~300 m across trees are always seen at LOD0 range, so a LOD1 + LODGroup is only extra memory and bake/probe complexity (Bakery skips LODGroup renderers without per-LOD setup). Use `--lod1` (exports `_Tree_LOD0`/`_LOD1` in one FBX: 5/4/3 sides, half the deepest twigs, 60 % cards at 1.35× size, unfolded) only for very large worlds, then add a LODGroup (transition heights are a per-world choice; check them in VR).

## Big trees around walkways (treehouse, 2026-10)
Giant jungle trees (70–100 m, crowns r 12–28 m, houses inside the crown) use the same builder plus optional CFG keys (all off by default):
- `clear=[dict(poly=[(x,y)…], z=(z0,z1), margin=m) | dict(seg=((x,y,z),(x,y,z)), r=m)]`: keep-out volumes (deck prisms, stair/bridge capsules). Limbs never start inside one, stop `clear_pad` m before entering one (segment midpoints are tested too), and cards are rerouted, then shrunk, then skipped. A card is tested along its axis and at its corners (±width/2 at base, 35/70/100 %). A skipped tip card counts as `tips_uncovered`; a few (≤ 4 of 100+) next to decks are expected.
- `side=[dict(n, z=(lo,hi), len, ang, r, tip, gnarl, up)]`: extra trunk limbs at absolute heights, without children (dead stubs low down; leafy secondary limbs get one tip card above `minz·0.8`).
- `buttress=dict(n, z, reach, r)`: flaring roots from the lower trunk out and down to z = 0. Only where the trunk base is visible on dry ground; in flooded worlds the base is under water, so leave it off ("roots are submerged trees are sticking out of the water").
- `vines=dict(count, size, z)`: hanging sprig cards under depth ≥ 1 branches (draped foliage/epiphytes), rooted on the axis like sprigs.
- `bark_tile` (0.6): metres per bark repeat; on 2–6 m trunks use 2–3 m per repeat, scaled by trunk radius (`bark_tile_r`, `bark_tile_min`), plus a large-scale tint/moss macro variation (`bark_macro`) and a per-tree UV offset. A scan with distinct single knots grids up visibly ("bark is too repeated"): pick one with even, ridged texture.
- `lod1_cards` / `lod1_size` (0.6 / 1.35): LOD1 card share and size, e.g. 0.24 / 1.8 for ≤ 2k LOD1 on a 7k LOD0.
Per-tree configs can be generated from a layout file (one species per tree, volumes in tree-local coordinates; FBX maps Blender (x,y,z) to Unity (−x,z,−y), so place at rotation 0). Example: a per-world layout script such as `<project>/Blender/trees/<world>_trees.py`, checked with `verify_tree.py` (exact z-fight pairs, vertices inside walk volumes, crown floor). Measured (treehouse world): 10.3–21.0k tris per village kapok (2.6–10.4k bark, 6.4–13.1k leaf), ring trees 6.2–6.7k with LOD1 1.8–1.9k.
For night worlds grade the leaf atlas once (a per-world `grade_atlas.py` next to the layout script: soft shoulder on linear luminance, knee 0.07 → max 0.20): gpt leaf sprays carry glossy highlights that render near-white under torches.

## Realistic trees: checklist
1. Crowns grow from the branches; blockout spheres are placeholders, never leaf targets.
2. Many long medium branches; leaves only near branch ends. Check a leaves-hidden render.
3. Open canopy: gaps, sky shows through, no fill cards on giants.
4. Real leaf size, measured against the avatar (kapok leaflet 8–20 cm, fig 15–25 cm).
5. One leaf branch per atlas cell, little overlap (olive method).
6. One natural green; vary leaf type between trees, not colour.
7. Leaves matte (smoothness 0); per-cluster normals on giants.
8. Obey the setting (no roots under water); compare with the user's reference photos.

## Unity setup
- FBX: Scale 1, **Normals Import**, Generate Lightmap UVs **off** (UV2 comes from Blender), Add Colliders off, Read/Write off, mesh compression off. Materials extracted/assigned manually.
- Bark material: Standard, albedo + normal, tiling 1.
- Leaf material: `unity/FoliageCutout.shader` (Cull Off, explicit `clip()` — the `alphatest` pragma blended leaves against bright HDR backgrounds and burned them white; addshadow + meta pass so bakes use the leaf silhouette). `_Cutoff` 0.45, Smoothness 0 (glossy leaves rim against the sky), `_UseMeshNormalsBothSides` 1, optional `_AlphaToCoverage` with MSAA.
- Leaf texture: Alpha Is Transparency on, **Mip Maps Preserve Coverage on, alpha reference 0.45** (= cutoff, so the crown doesn't thin out in the distance), max 2048, Clamp.
- **No colliders** on trees (walk-through; add one thin BoxCollider on the trunk only if the world needs it). No seat stations.
- Static: one renderer holds bark + leaves → mark Contribute GI / lightmap static (+ Reflection Probe Static); leaves are **lightmapped, not probe-lit**. Give it enough lightmap scale for the canopy.

## Lighting gotchas
- **Tree uplights:** a narrow cone hugging the trunk lights only the trunk up to the first fork — the lightmapped leaves receive ≈0 (bark occludes them). Place ground uplights **1.75–2 m out** from the trunk on the viewer side (path/building), aim at the **LOD0 bounds centre** (tilt ≈35–37°), 60° cone, inner 40 %; then tune intensity until lit leaves read (a modelled mean ≈0.12 on the leaves needed intensities 9.5–15.75 in a night scene).
- A wrong winding/normal flip shows as a near-black or patchy crown: re-check `align_card_winding` and `_UseMeshNormalsBothSides`.
- After any lighting bake, rebake reflection probes.

## Verify before calling it done
`STAT` tris in budget, `open_bark_edges_above_ground 0`, `tips_uncovered 0`, `attach out_of_tolerance 0`, bark stretch max/min ≲ 3, leaf normal spread < 0.7; `--qa` render; in Unity a composition review from eye height and from below at night.

Blender and mesh lessons checklist: [asset-import/references/lessons-blender-and-geometry.md](../asset-import/references/lessons-blender-and-geometry.md).

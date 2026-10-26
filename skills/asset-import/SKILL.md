---
name: asset-import
description: Bring a 3D model into a VRChat world — FBX, GLB, a .unitypackage prefab, a Blender export or image-to-3D output — with correct importer settings, real-world scale, up and front axes, pivots, lightmap UV2, clean meshes (normals, winding, duplicates, z-fighting) and clean prefabs (no seat stations, no small-prop colliders, no idle Animators), then prove it in the scene. Use whenever a model file or asset pack enters a world project, an imported prop renders wrong (tiny, lying down, black, blank, white, banded, back-to-front), or a model already placed is replaced by a new export.
---

# Asset import for VRChat worlds

Scope: Unity 2022.3, Built-in Render Pipeline, VRChat Worlds SDK. This skill starts when a file is
chosen and ends when the prop sits in the scene, measured and clean. Finding and licensing the file:
[`.omp/skills/worldbuilding-assets/SKILL.md`](../worldbuilding-assets/SKILL.md). Generating a prop
from approved references: [`.omp/skills/image-to-3d-props/SKILL.md`](../image-to-3d-props/SKILL.md)
(its §6–§7 are the GLB-specific version of §3–§4 here). Modelling in Blender: the `blender-modeler`
agent. Decimating an existing rigid model: the `blender-optimizer` agent.

Stage: C.1 Build-out (furniture placed in 3D and dressing, see `.omp/skills/world-pipeline/SKILL.md`). The
gate is the `dressing-reviewer`'s SHIP IT, not this checklist. Drive the open Editor through the Unity
MCP `execute_code` tool, never by editing scene or prefab YAML.

## 1. Get the file into the project
| Source | Do |
|---|---|
| `.unitypackage` | Import through Unity, never copy into `Assets/`. GUID identity beats folder location, so a bundled old copy of a library overwrites the installed VPM package: run `git status Packages/` and restore modified files with `git checkout --`. Delete a duplicate `UdonSharpProgramAsset` it drops in `Assets/`; keep the package's. Recolour packs whose `.meta` GUIDs collide with originals: import the images without their `.meta` into a separate folder. |
| Vendor world package | Missing-script components mean the `.cs` was not shipped; disable what depends on it (dropping the `.cs` in later with its original GUID heals every instance). lilToon-only materials go magenta without lilToon; untextured ones convert to Standard nearly losslessly. |
| Raw FBX / OBJ pack | Extract to `Assets/<PackName>/`. 3ds Max OBJ in inches needs `globalScale = 0.0254`; a missing `.mtl` means binding textures by hand on new materials. Check the texture set is complete. Keep `.blend`, `.spp` and layered PSDs outside `Assets/`. |
| Blender export | Copy a known-good export call verbatim: `apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, object_types={'MESH'}` (`FBX_SCALE_NONE` looks right in Blender and imports at 1/100). Convert curves/text to mesh first (silently skipped otherwise). Unity orders submeshes by first face reference, so `sort_elements(type='MATERIAL')` before export. |
| GLB (image-to-3D, Sketchfab) | Imports through glTFast; its embedded textures bypass compression (RGB24 2048² ≈ 37 MB each, readable copies). Convert to FBX + texture files (Blender) or re-encode, then delete the shipping GLB. |
| Poly Haven FBX | Authored in cm: set `globalScale = 100`. Models can import Z-up face-down with mid-height or back-edge pivots; vegetation is Z-up with centred pivots. |

After writing or reimporting files from a script, measure in a **later** `execute_code` call: the same
call still sees the old mesh, and an instance created in that call reports absurd sizes. Files written
to disk may need `AssetDatabase.ImportAsset(path, ForceUpdate | ForceSynchronousImport)`.

## 2. Importer settings for a static prop
Set on the `ModelImporter`, `SaveAndReimport()`, read back in the next call.

- **Scale:** fix units in the importer (`globalScale`, or `useFileScale = false, globalScale = 1` for a
  metre FBX that a Blender round-trip declared in cm), not by scaling each instance. The importer
  fix brings the model to real-world size; the placed instance then goes ×k (k = 0.8,
  fixed; spatial-design §5.9), furniture and props included. Real size is the
  full-size adult value: an imported prop pack placed at real size came in "super huge" in a room
  and had to be scaled down.
- **Rig and animation off:** `animationType = None`, `importAnimation = false`, so instances get no
  `Animator` that costs CPU every frame with nothing playing. Remove controller-less Animators and
  unused armatures from instances already placed.
- **Lightmap UVs:** pack FBXs often ship with *Generate Lightmap UVs* off; turn `generateSecondaryUV`
  on before the prop goes lightmap-static, with margin method **Manual** (pack margin ~6). Never pair
  `secondaryUVMarginMethod = Calculate` with a low `secondaryUVMinLightmapResolution` (16
  texels/unit): the gutters collapsed the islands into a corner. See §5.
- **Normals:** `Import` when the source carries custom normals (leaf cards with crown-proxy normals),
  never `Calculate`; also disable the foliage shader's back-face normal flip.
- **Materials:** `materialImportMode = ImportStandard`, `materialLocation = InPrefab`, then `AddRemap`
  keyed on the **FBX-internal** material name read from `GetExternalObjectMap()`, not the `.mat`
  filename; a wrong key is accepted silently, and with `External` the remap is ignored. Clearing the
  table drops the pack's working entries too. Alternative: create Standard materials named like the
  source materials and call `SearchAndRemapMaterials(BasedOnMaterialName, Everywhere)`.
- **Shaders:** Built-in RP only; URP/HDRP materials and missing third-party shaders render magenta.
  Substance roughness must be inverted into a `MetallicSmoothness` map (RGB metallic,
  `A = 255 − roughness`, sRGB off).
- **Textures:** authored and dropped-in textures import at aniso 1 / Bilinear, which smears grain;
  set aniso 8 and Trilinear on floors, walls and grained surfaces.

## 3. Scale, axes and pivot
1. **Measure, don't trust the exporter.** Instantiate a temp copy and read `Renderer.bounds` (world
   space). `sharedMesh.bounds` is mesh space: on a rotated child `.y` is not height. A cubic `(0.02,
   0.02, 0.02)` on a non-cubic prop is the 1/100 tell.
2. **The root transform carries the import fix.** Unit scale (×100, even non-uniform) and the −90° X
   stand-up (`(270, 0, 0)`) live on the model root or its child nodes. In scripts, multiply and
   compose, never assign: `SetParent(par, false)` first, then `localScale = src.localScale * s`,
   `rotation = Euler(0, yaw, 0) * src.rotation` (`src` = the prefab asset), tilt as a world delta on
   top: `Euler(tiltX, 0, tiltZ) * Euler(270, yaw, 0)`. On a Z-up model "height" is local Z, so scale
   along the model's local axes. A script that builds its own GameObjects must copy each child's
   local transform from the source.
3. **Decide Z-up once per source file** and hard-code it per family, never per mesh by aspect ratio:
   `size.z > size.y` also fires on wide, low Y-up shrubs and lays them on their backs.
4. **Front axis varies inside one pack.** Instantiate every candidate in one row at identity rotation,
   far from the scene, one directional light, and shoot it from +X: anything showing a plain slab
   has its front on −X. The same contact sheet settles style.
5. **Build a placement-ready prefab** for anything placed more than once: floor-centre pivot, upright
   rotation baked, materials bound. Place the prefab, never the raw model.
6. **Place by renderer bounds or a downward raycast, not the pivot**: FBX pivots can sit metres from
   the mesh (`position += target − bounds.center`, then seat `bounds.min.y`). Prefabs with UI,
   cameras or unposed skinned meshes have junk bounds: raycast with their own colliders disabled.
   Ceiling- or rig-mounted props are not floor-seated; render once from a low oblique angle.
7. **After any rescale, recompute `LODGroup.size`**: it is stored, not derived, and a 1/100 value
   culls the prop a few metres out. Health check: `size ÷ max renderer-bounds dimension` = 1.0000; fix
   via `LoadPrefabContents`, set size, `SaveAsPrefabAsset`. Terrain trees then need
   `RefreshPrototypes()` + `Flush()`.
8. Never parent props under a scaled primitive (board, slab, wall): its scale multiplies into them.

## 4. Materials on placed instances
- Instantiating from the FBX gives its **stub materials** (untextured, same names as yours, or
  `Default-Material`). Audit `material | shader | mainTexture`, never the name alone. A white,
  untextured prop is a binding problem, not lighting.
- Per-renderer overrides on scene instances beat importer remaps (the asset preview looks right while
  the scene doesn't): set `sharedMaterials` on the instances and read materials back off a **scene**
  renderer. Edits to FBX-embedded materials don't persist; use material assets.
- A Blender round-trip can reorder material slots; read per-submesh material names from both prefabs
  and permute the instance array: `newMats[j] = oldMats[oldOrder.IndexOf(newOrder[j])]`.

## 5. Lightmap UV2 and static flags
- **Lightmap or Light Volumes?** Decide per renderer class with `.omp/skills/lightmap-allocation/SKILL.md`
  §1 (glass and small decor whose UV2 fails the audit go to Light Volumes and keep casting; furniture
  stays lightmapped with a UV2 that passes its audit). Anything not lightmapped, and every dynamic
  prop or pickup, needs an LV-compatible material (`<name>_LV.mat` copy); Standard is a finding.
- **Every lightmapped mesh has UV2 in range.** "Has UV2" is not the test: scan UV2 for values outside
  0..1 or NaN. One bad mesh fails Bakery's packer for its whole group (infinite
  `lightmapScaleOffset` on hundreds of renderers). The importer unwrap can silently fail on one LOD;
  run `Unwrapping.GenerateSecondaryUVSet` on the finished mesh (it adds vertices at seams, so write
  the channel unconditionally on a reused mesh asset). Combined meshes need a fresh unwrap too.
- **UV2 charts ÷ triangles ≈ 1.0 is the alarm** (≈ 0.5 is normal on boxy meshes): duplicate
  coincident triangles. Dedupe, weld by position + normal + uv0 (position alone kills hard corners),
  re-unwrap, rebake.
- "Overlapping UVs" warnings are a gutter problem: widen the pack margin until the gap is at least
  padding + 1 texels, then trim `scaleInLightmap` back, before re-unwrapping.
- The Unity Quad primitive has no UV2 (the Cube has); copy UV0 into UV2 on a saved mesh asset.
- **Static flags are per GameObject**: `SetStaticEditorFlags` on a prefab root leaves its child
  renderers out of the bake; flag every child. `ReflectionProbeStatic` is a separate flag from
  `ContributeGI` (leave it off glass, screens and small props).

## 6. Mesh hygiene
| Symptom | Check first |
|---|---|
| Blank slab where detail should be | Facing: the prop shows its back. Average the content submesh's per-triangle normals in local space and orient from that. |
| Black door, lift or picture | The leaf/canvas sits inside or behind its frame; make it 2–3 cm proud of the frame's front face and sweep the whole class. |
| Black modular kit piece | You are looking at the hidden side, which the kit maps to a black atlas patch; check from inside the assembly. |
| See-through or inside-out | Compare each triangle's `Cross(b−a, c−a)` with its stored normal: conclusive only for meshes you generated (a primitive Cube reads 0/12 inverted); for imports the render is the oracle. Make scripted builders flip opposing pairs themselves. Check every section (caps, flaps), not the first triangle. |
| Hard flat bands after the bake | Duplicate coincident triangles, not normals (see charts ÷ tris, §5). |
| Pale, grainless, faintly shiny | A generated mesh without tangents: `RecalculateTangents()`; no rebake needed. |
| Flickering seams | Coplanar faces between parts: push joints 1–3 cm into each other, inset from shared edges; run the z-fight gate (§9). |
| Torn cardboard rocks | Photoscan pieces are open shells: gate on volume ÷ surface area (not bbox aspect), thicken to ≥ 8 cm or swap. |
| Smeared or postage-stamp texture | Effective repeats per metre = mesh UV per metre × material tiling, per axis (~0.5–1 reads right for wood/plaster). Fix in UV1 (copy UV2 through untouched), never by rebuilding geometry; measure density as `sqrt(worldArea / uvArea)`, not from UV span. Scaled Cube primitives can't match anything. |
| Mirrored artwork | UV handedness: sibling panels on one wall must agree; prove with a panel showing text. |
| Rebuild "did nothing" | Which LOD is on screen? Clamp every LOD to the triangle floor, not just LOD0; screenshot inside the LOD0 distance. |
| `Invalid AABB` console flood | A NaN vertex; sweep renderer bounds for NaN/Infinity. |

Writing meshes from scripts: save a **new** asset with `AssetDatabase.CreateAsset` rather than
`CopySerialized` into an existing one (the renderer keeps drawing the old mesh). If the object still
has a `ProBuilderMesh`, make the mesh an independent asset, then remove the component, then assign:
ProBuilder otherwise rebuilds over your mesh on reload, and destroying the component (or a clone)
destroys the mesh it owns.

## 7. Prefab hygiene (the kit's hard rules, `.omp/RULES.md` rules 2 and 3)
- **Strip every `VRCStation` / `VRC_Station`** from imported chairs, sofas, beds and vehicles. Never
  add one unless the user explicitly asks.
- **Strip imported colliders from small props** (chairs, stools, couches, side tables, decor). Big
  furniture (big tables, counters, cabinets, wardrobes, bookcases) gets one always-on child
  `SolidCollider` `BoxCollider`, floor to top surface. Beds and couches get a top-surface child
  `LieDownCollider` `BoxCollider`, disabled by default. Never a `MeshCollider` on anything walked on.
  Destroy the auto-added collider of any primitive. Keep a modular kit floor's invisible collider
  submesh material: it is intentional.
- **No idle `Animator`s** or unused armatures on static props (§2).
- Count what each instance of a vendor prefab adds: stations, object syncs, UdonBehaviours.
- Dressing lives under `<Area>/Props` (or `<Area>/Dressing`) so the audit sees it
  (`.omp/docs/unity-tools.md` "WorldAudit").
- Reparenting a child out of a prefab instance silently fails: unpack first. Scripted hierarchy edits
  need `MarkSceneDirty` before saving, or `SaveScene` returns true without writing.

## 8. Replacing a model that is already placed
Copy the new FBX **over the old asset path** so every instance keeps transform, flags and colliders.
Before the copy: same submesh count and slot order (else `NULL` material slots), comparable bounds and
`minY`, same unit convention (a cm→m change doubles the import correction). Afterwards set
`sharedMaterials` on the instances. Swapping instances to a different asset instead: strip the old
root's scale/rotation and re-apply the new asset's root, and remove any per-instance −90° X fix the
new export doesn't need.

## 9. Verification (builder runs, reviewer judges)
| # | Check | Pass |
|---|---|---|
| 1 | Units | one sample's `Renderer.bounds.size` matches the real object in metres after the import fix, and the placed instance is real × k (measured in a later call than the import) |
| 2 | Upright | `bounds.min.y ≥ floor − 0.05` after every rotate/scale pass; upright props `size.y > 0.55 × max(size.x, size.z)`, rosettes excepted |
| 3 | Front | a contact-sheet or 3/4 render shows the detailed face toward the room |
| 4 | LODs | `LODGroup.size ÷ bounds max dimension` = 1.0000 on every prefab; screenshots taken inside the LOD0 distance |
| 5 | Materials | no `Default-Material`, stub or magenta material on a scene renderer; GLB textures gone or compressed |
| 6 | UV2 | every lightmapped renderer has UV2 inside 0..1, no NaN; charts ÷ tris well below 1.0 |
| 7 | Static flags | read back on every child renderer, not the root |
| 8 | Z-fighting | `AWDK.AgentTools.ZFightScan` ends `PAIRS=0 COMPLETE` over the touched root; `ZFightRender` shows no magenta in grazing close-ups (`.omp/docs/unity-tools.md`) |
| 9 | Rules | `AWDK.AgentTools.WorldAudit.Run(root)`: no stations, no prop colliders except `SolidCollider` / `LieDownCollider`, no MeshCollider on walked surfaces, no static renderer without UV2, no uncompressed textures |
| 10 | Mesh sanity | no active, enabled renderer with `sharedMesh == null` or zero/NaN bounds; no `ProBuilderMesh` left on an object wearing an authored mesh |
| 11 | Packages | `git status Packages/` clean after any `.unitypackage` |
| 12 | Render | a rendered before/after from player eye height; numbers locate problems, only renders prove fixes |

Then sweep `__*__` capture objects and hand the pass to the `dressing-reviewer` with the z-fight
output and the list of imported assets.

Blender and mesh/UV lessons checklist: [references/lessons-blender-and-geometry.md](references/lessons-blender-and-geometry.md).

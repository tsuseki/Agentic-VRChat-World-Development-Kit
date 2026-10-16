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

Stage: C.1 Build-out (furniture swap and dressing, see `.omp/skills/world-pipeline/SKILL.md`). The
gate is the `dressing-reviewer`'s SHIP IT, not this checklist. Drive the open Editor through the Unity
MCP `execute_code` tool, never by editing scene or prefab YAML.

## 1. Get the file into the project
| Source | Do | Note |
|---|---|---|
| `.unitypackage` | Import through Unity, never copy into `Assets/`. Then `git status Packages/`: modified files there are a GUID clobber; restore them. Delete a duplicate `UdonSharpProgramAsset` it drops in `Assets/`. | [unitypackage GUID clobber](../../knowledge/notes/unitypackage-import-can-overwrite-package-files.md) |
| Vendor world package | Missing-script components mean the `.cs` was not shipped; disable what depends on it. lilToon-only materials go magenta without lilToon. | [vendor packages](../../knowledge/notes/vendor-packages-missing-udonsharp-scripts-and-liltoon-materials.md) |
| Raw FBX / OBJ pack | Extract to `Assets/<PackName>/`. 3ds Max OBJ in inches needs `globalScale = 0.0254`; a missing `.mtl` means binding textures by hand. Keep `.blend`, `.spp` and layered PSDs outside `Assets/`. | [legacy models](../../knowledge/notes/import-legacy-models-inches-z-up-and-substance-maps.md) |
| Blender export | Copy a known-good export call verbatim: `apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, object_types={'MESH'}`; convert curves/text to mesh first; sort faces by material so submesh order matches slot order. | [export recipes](../../knowledge/notes/blender-fbx-export-and-modeling-recipes.md), [FBX_SCALE_NONE is 1/100](../../knowledge/notes/blender-fbx-export-scale-all-not-scale-none.md) |
| GLB (image-to-3D, Sketchfab) | Imports through glTFast; its embedded textures bypass compression (RGB24 2048² ≈ 37 MB each). Convert to FBX + texture files (Blender) or re-encode, then delete the shipping GLB. | [GLB textures](../../knowledge/notes/glb-imported-textures-bypass-compression.md) |
| Poly Haven FBX | Authored in cm (imports 1/100); vegetation is Z-up with centred pivots. | [Poly Haven import](../../knowledge/notes/polyhaven-fbx-import-and-terrain-detail-density.md) |

After writing or reimporting files from a script, measure in a **later** `execute_code` call: the same
call still sees the old mesh ([verify reimports later](../../knowledge/notes/verify-reimports-in-a-later-call-and-edit-instances-safely.md)).

## 2. Importer settings for a static prop
Set on the `ModelImporter`, `SaveAndReimport()`, read back in the next call.

- **Scale:** fix units in the importer (`globalScale`, or `useFileScale = false, globalScale = 1` for a
  metre FBX that a round-trip declared in cm), not by scaling each instance.
  [import traps](../../knowledge/notes/fbx-import-into-unity-traps.md)
- **Rig and animation off:** `animationType = None`, `importAnimation = false`, so instances get no
  `Animator` that costs CPU every frame with nothing playing. [import traps](../../knowledge/notes/fbx-import-into-unity-traps.md)
- **Lightmap UVs:** pack FBXs often ship with *Generate Lightmap UVs* off; turn `generateSecondaryUV`
  on before the prop goes lightmap-static. Don't pair `secondaryUVMarginMethod = Calculate` with a low
  `secondaryUVMinLightmapResolution`: the gutters swallowed the islands. See §5.
  [cozy interior note](../../knowledge/notes/interior-reads-cozy-only-if-darker-outside.md),
  [glass is probe-lit](../../knowledge/notes/glass-should-be-probe-lit-not-lightmapped.md)
- **Normals:** `Import` when the source carries custom normals (leaf cards with crown-proxy normals),
  never `Calculate`. [foliage normals](../../knowledge/notes/foliage-cards-need-crown-proxy-normals.md)
- **Materials:** `materialImportMode = ImportStandard`, `materialLocation = InPrefab`, then `AddRemap`
  keyed on the **FBX-internal** material name read from `GetExternalObjectMap()`; a wrong key is
  accepted silently. Or create Standard materials named like the source materials and call
  `SearchAndRemapMaterials`. [AddRemap keys](../../knowledge/notes/fbx-addremap-keys-are-internal-names.md),
  [import traps](../../knowledge/notes/fbx-import-into-unity-traps.md)
- **Shaders:** Built-in RP only; URP/HDRP materials and missing third-party shaders render magenta.
  Substance roughness must be inverted into smoothness (`A = 255 − roughness`, sRGB off).
  [legacy models](../../knowledge/notes/import-legacy-models-inches-z-up-and-substance-maps.md)
- **Textures:** authored and dropped-in textures import at aniso 1 / Bilinear; set aniso 8 and
  Trilinear on floors, walls and grained surfaces. [aniso 8](../../knowledge/notes/authored-textures-need-aniso-8-and-trilinear.md)

## 3. Scale, axes and pivot
1. **Measure, don't trust the exporter.** Instantiate a temp copy and read `Renderer.bounds` (world
   space). `sharedMesh.bounds` is mesh space: on a rotated child `.y` is not height. A cubic `(0.02,
   0.02, 0.02)` on a non-cubic prop is the 1/100 tell. [root transform](../../knowledge/notes/fbx-root-transform-carries-unit-scale-and-rotation.md)
2. **The root transform carries the import fix.** Unit scale (×100, even non-uniform) and the −90° X
   stand-up live on the model root or its child nodes. In scripts, multiply and compose, never assign:
   `localScale = src.localScale * s`, `rotation = Euler(0, yaw, 0) * src.rotation`, tilt as a world
   delta on top. [compose rotation](../../knowledge/notes/compose-fbx-root-rotation-never-assign.md),
   [tilt as delta](../../knowledge/notes/apply-tilt-as-delta-on-z-up-fbx.md)
3. **Decide Z-up once per source file**, never per mesh by aspect ratio (wide, low Y-up shrubs fail the
   test). [up axis per file](../../knowledge/notes/resolve-up-axis-per-source-fbx.md)
4. **Front axis varies inside one pack.** Shoot every candidate in one row at identity rotation from
   +X; anything showing a plain slab has its front on −X. [front axis](../../knowledge/notes/prefab-front-axis-varies-within-a-pack.md),
   [contact sheet](../../knowledge/notes/pick-pack-prefabs-from-a-contact-sheet.md)
5. **Build a placement-ready prefab** for anything placed more than once: floor-centre pivot, upright
   rotation baked, materials bound. Place the prefab, never the raw model.
   [legacy models](../../knowledge/notes/import-legacy-models-inches-z-up-and-substance-maps.md)
6. **Place by renderer bounds or a downward raycast, not the pivot**: FBX pivots can sit metres from
   the mesh. Ceiling- or rig-mounted props are not floor-seated.
   [up axis per file](../../knowledge/notes/resolve-up-axis-per-source-fbx.md),
   [raycast seating](../../knowledge/notes/seat-objects-by-downward-raycast-not-bounds.md),
   [mounting](../../knowledge/notes/check-prop-mounting-before-floor-seating.md)
7. **After any rescale, recompute `LODGroup.size`**: it is stored, not derived; a 1/100 value culls
   the prop a few metres out. Health check: `size ÷ max renderer-bounds dimension` = 1.0000.
   [LODGroup size](../../knowledge/notes/lodgroup-size-stale-after-rescale.md)
8. Never parent props under a scaled primitive. [scaled parent](../../knowledge/notes/never-parent-props-to-a-scaled-primitive.md)

## 4. Materials on placed instances
- Instantiating from the FBX gives its **stub materials** (untextured, plausible names). Audit
  `material | shader | mainTexture`, never the name alone. [stub materials](../../knowledge/notes/fbx-instantiated-donors-carry-stub-materials.md)
- Per-renderer overrides on scene instances beat importer remaps; set `sharedMaterials` on the
  instances and read materials back off a **scene** renderer. Edits to FBX-embedded materials don't
  persist; use material assets. [overwrite in place](../../knowledge/notes/overwrite-fbx-in-place-to-swap-all-instances.md),
  [verify reimports later](../../knowledge/notes/verify-reimports-in-a-later-call-and-edit-instances-safely.md)
- A Blender round-trip can reorder material slots; permute the instance array by submesh name.
  [import traps](../../knowledge/notes/fbx-import-into-unity-traps.md)

## 5. Lightmap UV2 and static flags
- **Lightmap or probe-light?** Small props and thin glass are better as `receiveGI = LightProbes`;
  a UV2-less prop can still be `ContributeGI` and cast baked shadows that way.
  [UV2-less props](../../knowledge/notes/uv2-less-props-can-cast-baked-shadows-with-receivegi-lightprobes.md),
  [glass](../../knowledge/notes/glass-should-be-probe-lit-not-lightmapped.md)
- **Every lightmapped mesh has UV2 in range.** "Has UV2" is not the test: scan UV2 for values outside
  0..1 or NaN. One bad mesh fails the packer for its whole Bakery group. When the importer unwrap
  silently fails on one LOD, run `Unwrapping.GenerateSecondaryUVSet` on the finished mesh (it adds
  vertices at seams). [one bad UV2](../../knowledge/notes/one-bad-uv2-poisons-bakery-atlas.md)
- **UV2 charts ÷ triangles ≈ 1.0 is the alarm** (≈ 0.5 is normal on boxy meshes): duplicate
  triangles; dedupe, weld by position + normal + uv0, re-unwrap.
  [duplicate triangles](../../knowledge/notes/hard-bands-on-baked-surface-duplicate-triangles.md)
- "Overlapping UVs" warnings are a gutter problem; widen the pack margin in texels before
  re-unwrapping. [gutters](../../knowledge/notes/overlapping-lightmap-uv-warning-is-a-gutter-problem.md)
- The Unity Quad primitive has no UV2 (the Cube has).
  [Quad faces −Z](../../knowledge/notes/unity-quad-primitive-faces-minus-z.md)
- **Static flags are per GameObject**: flag every child renderer, not the prefab root.
  `ReflectionProbeStatic` is a separate flag from `ContributeGI`.
  [flags don't propagate](../../knowledge/notes/static-editor-flags-do-not-propagate-to-children.md),
  [probe static](../../knowledge/notes/reflection-probes-need-reflectionprobestatic-flag.md)

## 6. Mesh hygiene
| Symptom | Check first | Note |
|---|---|---|
| Blank slab where detail should be | Facing: the prop shows its back. Average the content submesh's local normal. | [facing](../../knowledge/notes/featureless-prop-check-facing-before-material.md) |
| Black door, lift or picture | The leaf/canvas sits inside or behind its frame; make it 2–3 cm proud. | [hidden in frame](../../knowledge/notes/door-leaf-or-canvas-hidden-inside-its-frame.md) |
| Black modular kit piece | You are looking at the hidden side the kit maps to a black atlas patch. | [kit black faces](../../knowledge/notes/modular-kit-black-faces-are-hidden-sides.md) |
| See-through or inside-out | Winding vs stored normal is conclusive only for meshes you generated; for imports the render is the oracle. Check every section (caps, flaps). | [winding check](../../knowledge/notes/procedural-mesh-winding-check.md), [per section](../../knowledge/notes/prove-winding-per-mesh-section.md), [self-correcting builder](../../knowledge/notes/scripted-mesh-builder-winding-check.md) |
| Hard flat bands after the bake | Duplicate coincident triangles, not normals. | [duplicate triangles](../../knowledge/notes/hard-bands-on-baked-surface-duplicate-triangles.md) |
| Pale, grainless, faintly shiny | A generated mesh without tangents: `RecalculateTangents()`. | [tangents](../../knowledge/notes/generated-mesh-needs-recalculatetangents.md) |
| Flickering seams | Coplanar faces between parts: overlap joints 1–3 cm; run the z-fight gate (§8). | [joints as overlaps](../../knowledge/notes/build-scripted-joints-as-overlaps-not-flush-contacts.md) |
| Torn cardboard rocks | Photoscan pieces are open shells: gate on volume ÷ surface area, thicken or swap. | [hollow shells](../../knowledge/notes/photoscan-pieces-are-hollow-shells.md) |
| Smeared or postage-stamp texture | Effective repeats per metre = mesh UV per metre × material tiling; fix in UV1, keep UV2. | [repeats per metre](../../knowledge/notes/fix-texture-stretch-via-effective-repeats-per-metre.md), [UVs not geometry](../../knowledge/notes/fix-texture-stretch-with-uvs-not-geometry.md), [density in the material](../../knowledge/notes/uv-density-may-live-in-the-material.md), [texel density](../../knowledge/notes/measure-texel-density-per-triangle.md), [solve UV scale](../../knowledge/notes/solve-uv-scale-from-mesh-triangles.md) |
| Mirrored artwork | UV handedness: siblings must agree; prove with a text panel. | [handedness](../../knowledge/notes/wall-panel-uv-handedness-sibling-check.md) |
| Rebuild "did nothing" | Which LOD is on screen? Clamp every LOD to the triangle floor. | [LOD floor](../../knowledge/notes/lod-tri-floor-must-clamp-every-lod.md) |
| `Invalid AABB` console flood | A NaN vertex; sweep bounds for NaN/Infinity. | [NaN vertex](../../knowledge/notes/nan-vertex-from-pow-of-sine.md) |

Writing meshes from scripts: save a **new** asset rather than `CopySerialized` into an existing one
([stale render](../../knowledge/notes/copyserialized-into-existing-mesh-renders-stale.md)). If the object
still has a `ProBuilderMesh`, make the mesh an independent asset, then remove the component, then
assign, or ProBuilder rebuilds over it and destroying it kills the mesh
([regenerates](../../knowledge/notes/probuilder-regenerates-over-an-assigned-mesh.md),
[owns its mesh](../../knowledge/notes/probuildermesh-owns-its-mesh-destroying-it-or-a-clone-kills-it.md)).

## 7. Prefab hygiene (the kit's hard rules, `.omp/RULES.md` rules 2 and 3)
- **Strip every `VRCStation` / `VRC_Station`** from imported chairs, sofas, beds and vehicles. Never
  add one unless the user explicitly asks.
- **Strip imported colliders from small props** (chairs, stools, couches, side tables, decor). Big
  furniture (big tables, counters, cabinets, wardrobes, bookcases) gets one always-on child
  `SolidCollider` `BoxCollider`, floor to top surface. Beds and couches get a top-surface child
  `LieDownCollider` `BoxCollider`, disabled by default. Never a `MeshCollider` on anything walked on.
  Destroy the auto-added collider of any primitive. Keep a modular kit floor's intentional
  collider submesh material ([kit black faces](../../knowledge/notes/modular-kit-black-faces-are-hidden-sides.md)).
- **No idle `Animator`s** or unused armatures on static props (§2).
- Count what each instance of a vendor prefab adds: stations, object syncs, UdonBehaviours.
  [vendor packages](../../knowledge/notes/vendor-packages-missing-udonsharp-scripts-and-liltoon-materials.md)
- Dressing lives under `<Area>/Props` (or `<Area>/Dressing`) so the audit sees it
  ([`.omp/docs/unity-tools.md`](../../docs/unity-tools.md) "WorldAudit").
- Reparenting a child out of a prefab instance silently fails: unpack first. Scripted hierarchy edits
  need `MarkSceneDirty` before saving. [verify reimports later](../../knowledge/notes/verify-reimports-in-a-later-call-and-edit-instances-safely.md),
  [dirty flag](../../knowledge/notes/unity-scripted-edits-do-not-dirty-the-scene.md)

## 8. Replacing a model that is already placed
Copy the new FBX **over the old asset path** so every instance keeps transform, flags and colliders.
Before the copy: same submesh count and slot order, comparable bounds and `minY`, same unit
convention. Afterwards set `sharedMaterials` on the instances.
[overwrite in place](../../knowledge/notes/overwrite-fbx-in-place-to-swap-all-instances.md),
[decimated swap](../../knowledge/notes/swap-in-decimated-meshes-keeping-submesh-order.md),
[root transform](../../knowledge/notes/fbx-root-transform-carries-unit-scale-and-rotation.md)

## 9. Verification (builder runs, reviewer judges)
| # | Check | Pass |
|---|---|---|
| 1 | Units | one sample's `Renderer.bounds.size` matches the real object in metres (measured in a later call than the import) |
| 2 | Upright | `bounds.min.y ≥ floor − 0.05` after every rotate/scale pass; upright props `size.y > 0.55 × max(size.x, size.z)`, rosettes excepted |
| 3 | Front | a contact-sheet or 3/4 render shows the detailed face toward the room |
| 4 | LODs | `LODGroup.size ÷ bounds max dimension` = 1.0000 on every prefab; screenshots taken inside the LOD0 distance |
| 5 | Materials | no `Default-Material`, stub or magenta material on a scene renderer; GLB textures gone or compressed |
| 6 | UV2 | every lightmapped renderer has UV2 inside 0..1, no NaN; charts ÷ tris well below 1.0 |
| 7 | Static flags | read back on every child renderer, not the root |
| 8 | Z-fighting | `AWDK.AgentTools.ZFightScan` ends `PAIRS=0 COMPLETE` over the touched root; `ZFightRender` shows no magenta in grazing close-ups ([`.omp/docs/unity-tools.md`](../../docs/unity-tools.md)) |
| 9 | Rules | `AWDK.AgentTools.WorldAudit.Run(root)`: no stations, no prop colliders except `SolidCollider` / `LieDownCollider`, no MeshCollider on walked surfaces, no static renderer without UV2, no uncompressed textures |
| 10 | Mesh sanity | no active renderer with `sharedMesh == null` or zero/NaN bounds; no `ProBuilderMesh` left on an object wearing an authored mesh |
| 11 | Packages | `git status Packages/` clean after any `.unitypackage` |
| 12 | Render | a rendered before/after from player eye height; numbers locate problems, renders prove fixes ([metrics that can't see](../../knowledge/notes/metrics-that-cannot-see-their-defect.md)) |

Then sweep `__*__` capture objects and hand the pass to the `dressing-reviewer` with the z-fight
output and the list of imported assets.

# Blender and geometry lessons

Building meshes in Blender or from scripts, and keeping their facing, winding, UVs and topology clean in Unity.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Blender bridge and headless runs
- **Before trusting a Blender MCP session, check which `blender.exe` owns the bridge port; kill a saved, windowless ghost and reopen the file in the GUI** — an orphaned headless Blender or a second window can hold the port, so the agent edits a scene nobody sees (headless-only work: see `blender-modeler` agent banner).

## Blender export
- **Copy the proven FBX export call verbatim, convert curves/text to mesh, and `sort_elements(type='MATERIAL')` before export** — `FBX_SCALE_NONE` imports at 1/100, curves are skipped silently, and Unity orders submeshes by first reference so slots arrive permuted; `bake_space_transform` can mirror extruded text (export it without that flag and stand it up in Unity); open two-sided sheets break under `normals_make_consistent`, so build them as closed prisms; set rough/metal/alpha 8-bit maps to Non-Color and never hand-encode sRGB into `img.pixels` (see SKILL.md §1 "Blender export").
- **Run `recalc_face_normals` on the joined mesh right before export** — Blender previews double-sided, so faces flipped by operations like negative-depth inset look fine there and show up in Unity as holes onto the sky, often only outdoors.
- **Bake decorative rotations into the vertices before splitting a kit into per-object FBXs: zero the world rotation, apply a min-area yaw only when it cuts footprint area by more than 8 %, apply transforms, origin at bottom centre** — yaw left on the FBX node is thrown away as soon as Unity gets a root rotation, and Blender dimensions and Unity bounds won't show the leftover slant (apply-transforms rule: see `blender-modeler` "Modeling discipline").

## Blender mesh recipes
- **Turn a box blockout into one quad per visible face (physics-scanned in Unity, rebuilt in headless Blender) and check the result against the axis traps** — the FBX can come back rotated 180° about Y, wall UVs transpose 90° (swap U/V when the first axis is vertical), and one export rotated every stair box 90° about its own centre; prove enclosure with raycasts, not dark screenshots.
- **Decimate alpha-cutout plants with stock Decimate > Collapse, split by material (leaves roughly 0.4–0.5, stems roughly 0.25–0.4), gated by a UV-coverage metric with a harsh positive control** — a hand-rolled decimator lost leaf coverage where the modifier lost none, and `bmesh.ops.weld_verts` keeps stale UVs (gated rigid-prop decimation: see `blender-optimizer` agent "Procedure").
- **Give leaf cards crown-proxy normals, flip cards that face into the crown, import normals in Unity and turn off the shader's back-face normal flip** — per-card normals make the canopy speckle and the VFACE flip blackens half of the smoothed crown (see SKILL.md §2 "Normals").
- **Paint roads onto a terrain mesh as a signed-distance vertex colour, thresholded per pixel, and export colours as `LINEAR`** — per-face material painting staircases at cell size, and an sRGB curve shifts the 0.5 threshold.

## Facing and occlusion
- **When a door, lift or picture renders as a black slab, make the leaf or canvas 2–3 cm proud of its frame's front face along the measured viewing axis, and sweep every frame pair** — the frame's depth sits between wall and canvas, so a canvas positioned from the wall plane ends up hidden inside its frame (see SKILL.md §6).
- **When a prop renders blank but its materials check out, average the content submesh's local triangle normals and orient from that** — the placer assumed the wrong axis and every frame faced the wall (see SKILL.md §6).
- **Derive a Unity Quad's yaw from its mesh normal (it already faces −Z) and give it a UV2 copy or probe lighting** — rotating it 180° "to face the room" hides it behind the frame, and a ContributeGI quad with no UV2 bakes garbage (see SKILL.md §5).
- **Check a ProBuilder container for a cavity (24 verts, a top face at the centre) before sinking fill below its rim** — scripted planters are solid boxes, so sunk soil vanishes; leave it proud and retile it per pot, comparing each to its own rim.

## Triangle winding
- **Test generated-mesh winding against stored normals with a primitive Cube as the control (12/12), and trust the render for imported FBX** — the test also reports disagreement on correct imports (see SKILL.md §6).
- **Make scripted quad/box builders self-correcting: flip any triangle pair whose winding opposes its normal and log the count** — an inward-winding builder passes a normals check, is see-through from outside and gets misdiagnosed as lighting.
- **Record each section's triangle range in a hand-built mesh and orient each against its own outward direction; build fabric single-sided and 4–9 mm proud** — one facing test covers only the body, not the caps or flaps, and duplicated reversed faces shade as a black band.

## Writing meshes from scripts
- **Save a rebuilt mesh as a new asset (`CreateAsset`) instead of `CopySerialized` into the existing one** — the CPU data updates but the renderer keeps drawing the old mesh; a 0.00 % render diff means the pipeline is stale, not that the change was too subtle.
- **Call `RecalculateTangents()` in every generator whose mesh wears a normal-mapped shader** — without tangents the normal map does nothing and the surface reads pale, grainless and faintly shiny, which looks like an unbaked-lighting problem.
- **Clamp trig terms to zero before `Pow`/`Sqrt`/`Log` and sweep generated bounds for NaN/Infinity** — `Sin(π)` is slightly negative, one NaN vertex poisons the bounds, and the `Invalid AABB` flood names no object.
- **On an object that still has a `ProBuilderMesh`, save your mesh as an independent asset, destroy the component, then assign; prove it by reloading the scene from disk** — ProBuilder rebuilds from its stored data on reload and overwrites the assigned mesh; re-meshing also needs a fresh UV2 and `lightmapIndex = -1` until the next bake (see SKILL.md §6).
- **Never destroy a `ProBuilderMesh` or an `Instantiate`d ProBuilder clone without cloning its mesh first; afterwards sweep active, enabled renderers for a null or zero-bounds mesh** — the component owns the mesh, and a clone shares it, so the original goes invisible with no error.

## UVs and texel density
- **For "bad textures" on a procedural mesh, print the effective repeats per metre per axis (mesh UV per metre × material tiling) and fix the anisotropy with a per-axis world box projection in UV1, copying UV2 through** — editing the shared material breaks the rest of the set, and rewriting UV2 re-lays the lightmap (see SKILL.md §6).
- **Fix texture stretch from non-unit scale by scaling the UVs, not by rebuilding geometry; print a property-filtered sweep's match list before it writes** — a "rebuild at world scale" sweep turned spheres, cylinders and rotated parts into axis-aligned boxes.
- **Measure texel density per mesh as sqrt(sum of world triangle area ÷ sum of UV triangle area), and re-measure after every geometry edit** — UV span after a packed unwrap has no fixed relation to metres (off by 3.3×), and moiré on big flat surfaces is a pitch problem, not a filtering one.
- **Solve metres per UV from the dominant face's largest triangle before setting tiling, and count grout lines to get the texture period** — Cube primitives (0..1 per face), ProBuilder (1 UV unit per metre) and hand-built meshes all use different conventions.
- **Before matching a neighbour's density, check whether it comes from the mesh UVs or from `mainTextureScale`** — on a shared ProBuilder material the tiling lives on the material, so authoring UVs to the shipped figure doubles the scaling; scaled Cube primitives can never match.
- **Make sibling panels on one wall share UV handedness and prove it on a panel showing text** — choosing the outward face by raycast ties on collider-less walls and mirrors some panels, which abstract art hides.
- **Remap content textures (screens, art, signs) on ProBuilder faces to 0..1 on an instantiated mesh, then remove the `ProBuilderMesh` and check UV2** — Auto UVs are world-scaled, so a 4.4 m screen tiles its image in a grid, and a refresh brings the bug back.

## Overlaps, duplicates and edges
- **On a lightmapped mesh, treat UV2 charts ÷ triangles ≈ 1.0 as duplicate triangles: dedupe, weld by position + normal + uv0, re-unwrap, rebake** — coincident copies z-fight with different baked values and look like missing smooth shading (see SKILL.md §5).
- **Build scripted joints as 1–3 cm overlaps, extend runs past their ends, inset parts from shared edges, and assert zero coplanar pairs** — scripted placement hits the exact contact every time, so every instance z-fights (z-fight gate: see SKILL.md §9, `blender-modeler` "Modeling discipline").
- **Make water sheets wider than the basin and bury every edge vertex under the banks; check the minimum burial number** — a sheet that ends before the bank shows its own straight polygon boundary as the shoreline.

## Shape, LODs and shells
- **Apply the per-prop triangle floor inside the LOD loop for every level, and check which LOD is on screen before judging a rebuild** — ratios multiply through a floor applied only to LOD0, and a small prop's LOD0 stops rendering a few metres out.
- **To tilt a prop with a wide base plate, hinge the vertices above a joint (with a collar over the cut), or deliver a different variant** — rotating the whole object sinks a plate corner about 3 cm per degree at any angle.
- **Gate photoscan fragments on volume ÷ surface area (or bbox fill), then thicken them to 8–12 cm or swap them for closed proxies** — they are open shells, and a curled shell has a chunky bounding box that passes aspect tests (see SKILL.md §6).

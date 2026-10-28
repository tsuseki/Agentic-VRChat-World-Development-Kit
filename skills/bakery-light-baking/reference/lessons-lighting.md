# Lighting and baking lessons

Baked lighting in Unity for VRChat worlds: running Bakery or Progressive bakes, lightmap groups and texel density, occluders and leaks, emissive fixtures, mood and exposure, and diagnosing bad bakes.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Running, monitoring and recovering bakes

- **A bake that stalls while Unity sits idle is usually a hidden ftrace error dialog: run Bakery → Utilities → Detect optimal settings, or pin the tracer from script (`runsRTX6 = false`, OptiX 9 exe, `rtxMode = true`, `exportTerrainAsHeightmap = false`)** — Bakery launches the tracer with no window and caches `runsRTX6`. When a driver drops OptiX 6, the modal box never closes, so the exit-code fallback never fires. The progress bar names the first group, not the one at fault.
- **Never compile, refresh or reimport while `bakeInProgress`. Before launching, force a compile, wait until `isCompiling`/`isUpdating` stay false for 20 s or more, and check for `error CS`. Turn `exportTerrainTrees` off. Follow any cancel with a successful bake or `RequestScriptReload()`** — Bakery calls `AssetDatabase.Refresh` itself, so any pending script edit reloads the domain and kills the export. A cancel also leaks tens of GB, so the next export runs out of memory.
- **Drive scripted bakes through the window instance (`LoadRenderSettings` then `RenderButton`) and poll `bakeInProgress` from separate calls. Never `Thread.Sleep`. After every bake, re-check scene state, call `MarkSceneDirty` and save** — the static entry point does nothing and `RenderButton` returns silently in play mode. Bakery also reloads the scene, so objects you toggled can come back inactive (see SKILL.md §Scripted bakes).
- **Read the OptiX fallback lines as normal, read `.ftracelog.txt` instead of Editor.log, and check `bakeInProgress` before every launch. Never launch from `delayCall`** — `RenderButton` has no re-entry guard, so two exports collide in `%TEMP%\frender`. A killed export can also save empty storage bindings.
- **Pick the tracer and denoiser from the live GPU and driver: on non-RTX cards use `rtxMode = false` with CPU OIDN, and test candidates by replaying a logged ftrace command against each exe. Close SteamVR before baking on 6 GB cards** — compatibility flips between GPU generations and driver branches, and VRAM held by other apps crashes every trace.
- **Bake with Progressive GPU by default and switch a scene to Progressive CPU (or Bakery) only when Editor.log shows `PathTracer … 0rpt`; never trust `buildProgress`** — Progressive GPU can schedule zero rays on large scenes and hang the editor at about 1% (see SKILL.md §Without Bakery).
- **Treat a bake as finished only when `LightingData.asset`'s mtime passes the bake start, or when re-measured hashes differ** — `isRunning == false` and the "Total bake time" line both arrive before the EXRs are written, so an early check makes a good bake look like it changed nothing.
- **Iterate with a DRAFT preset (low texels and samples, same bounces) or the Samples Multiplier. After a preset switch, run a full Render, and run a separate probe pass after selected-group bakes** — selected-group bakes are refused after any geometry or atlas-resolution change and skip light probes. GI cost grows with the square of the sample count (see SKILL.md §Two-stage workflow).
- **GLIM (Vulkan, free) is the lightmapper when Bakery isn't owned or the GPU isn't NVIDIA: pin its version per project and move a Bakery scene to it only off the deadline path** — Bakery needs OptiX, and its groups and light meshes do not carry over to GLIM (see SKILL.md §Without Bakery: GLIM).
- **After every Bakery render in a test scene, `git status Assets/Bakery/ft*Storage.asset` and the shared model folders must be clean. Never enable Unwrap UVs there, and give tests their own model copies** — Bakery registers models in a project-wide registry and re-applies its UV2 on every import, so a test render can break other scenes' lightmaps (note `bakery-unwrap-registry-rewrites-shared-models`).
- **Before every Bakery render on a scene with a Terrain, delete any `__ExportTerrain*` objects under the Terrain and save, and never start while a script compile is pending** — an export cut short by a crash or domain reload leaves them behind, the next save keeps them, and every later export then throws `ArgumentOutOfRangeException` in `ftBuildGraphics.ExportScene` (note `bakery-stale-export-terrain-crashes-export`).

## Lightmap groups, atlas share and texel density

- **Reception, groups, density, UV2 quality and allocation audits have their own checklist** — `.omp/skills/lightmap-allocation/references/lessons-lightmap-allocation.md`.

## Scripted lighting prep and audits

- **Set static flags on every renderer from `GetComponentsInChildren<MeshRenderer>`, not on prefab roots** — `SetStaticEditorFlags` affects only the object you pass, and imported prefabs keep their meshes on children.
- **Run lightmap prep after any finalize pass and read every flag back after a full rebuild. Keep Bakery selectors on a root that survives the rebuild. Clear ContributeGI on mirrors and video screens** — builders silently undo flags and destroy selectors. A mirror makes Progressive loop forever. Only use `uv2 = uv0` when uv0 is a valid layout of charts.
- **Aim spot and wash lights with `LookRotation(target - pos)` and assert that `dot(forward, toTarget) > 0.99`** — a hand-typed Euler angle can point a light 180° away, and you only find out after a full bake.
- **In a sealed-light audit, skip directional lights and inactive or disabled renderers, and treat a light sitting on a face as escaped (require a margin)** — a raw `bounds.Contains` check double-counts lights and the escape pass never converges.
- **After adding or cloning Baked lights without a bake, copy a baked sibling's `bakingOutput` onto them and assert zero active lights with `!bakingOutput.isBaked`** — Unity lights meshes from `bakingOutput`, not `lightmapBakeType`, so an unbaked "Baked" spot renders realtime in the editor and in the uploaded world.

## Leaks, occluders and black shade

- **Set single-face environment meshes to `TwoSided` and turn the thick structural blockout boxes back on as ShadowsOnly occluders (colliders off)** — one-sided faces cast no shadow from behind, and zero-thickness seams leak sun that shadow bias cannot cure.
- **Put ShadowsOnly occluders only behind exterior shell faces, never on the room side and never on shared walls. Measure buried area with an OBB test** — an occluder in front of the visible face bakes the wall solid black, and pushing it out only moves the black face next door.
- **Give every ShadowsOnly renderer a dark (about 0.25 grey) material** — primitives keep the white Default-Material. The hidden boxes are still traced with ContributeGI and amplify bounce until sealed rooms bake hot.
- **Lift ShadowsOnly proxy boxes to the object's real underbody clearance, make them about 85% of its height, and use them only for objects that never move** — a box resting on the ground bakes a black slab, and a short box hides its own shadow. A moved object leaves its shadow behind.
- **When a hard black slab bakes onto a floor, compare the winding normal and shading normal of nearby ContributeGI meshes against a known ground truth, and write fixes to a new mesh asset** — face-down decal quads are invisible from above but still occlude the surface below. Inward-wound boxes bake themselves black.
- **Add a `BakerySkyLight` (skybox cubemap, `hemispherical`, `bakeToIndirect`) to every outdoor Bakery scene** — Bakery ignores Unity's ambient settings. Open shade survives on ground bounce while roofed shade bakes black.
- **Set the sun's `bakeToIndirect = true`, and if the bake overshoots, lower its `indirectIntensity` instead of dimming the sun** — with it off the sun produces no bounce, and with black flat ambient every exterior shade bakes to about zero.
- **With stock GLIM, expect two-sided leaf crowns to bake about 40% darker than Progressive. Bake foliage with the double-sided GI fork, or with Progressive or Bakery (Backface GI 1)** — GLIM 0.11's bounce pass returns black for every back-face hit even when Double Sided GI is on (note `glim-backface-black-on-two-sided-foliage`).
- **Judge sunlit exteriors on the baked daylight alone and tell the reviewer that light counts are out of scope there** — "enough fixtures" is an interior criterion. Point lights outdoors only add bake cost and noise.

## Emitters, fixtures and lamps

- **Give small or bright emitters a `BakeryLightMesh`, size its intensity as power (`worldArea × intensity`), and never set `selfShadow` off with non-zero `samples2`** — material emission alone barely lights a room, intensities do not copy between emitters of different size, and that combination bakes black (see SKILL.md §Emissive fixtures and SSS).
- **Give point-like emissive fixtures (under about 0.25 m²) a real baked light, and ease their emission** — baked emissive light scales with area, so a lit lens leaves the floor below dark. Long cove strips are the exception.
- **Before placing a lamp's light, ray-sweep the lamp mesh (with an open-air control point) and put several shadow-casting lights in its free space** — asset-pack bulbs are sealed cavities, so a light "in the bulb" contributes nothing.
- **In the pre-bake emissive sweep, flag every emissive renderer whose bounds sit fully inside another renderer, and check exposed emitters for near-white albedo** — a buried glow strip lights nothing and looks like a design choice.
- **To bake a lights-off variant, edit the material assets themselves (snapshot to JSON first, restore every field afterwards)** — Bakery reads the shared material asset, so `MaterialPropertyBlock` overrides never reach the bake.
- **Build a glowing lampshade as a lightmapped, shadow-casting `computeSSS` shade with zero emission plus a small emissive bulb child that carries the light mesh; keep the light mesh on the shade instead if its look will be iterated often** — a light mesh on the shade makes it probe-lit and flat like cardboard but leaves emission as a no-rebake knob, while the SSS shade costs a bake per tweak (see SKILL.md §Emissive fixtures and SSS).
- **On large canopies, check that soffit luminance stays below sunlit ground, and scale SSS with `sssColor`, not samples** — SSS turned a fabric roof into an overhead area light that erased every contact shadow underneath.
- **Choose which faces of an emissive overlay to keep by `dot(normal, viewer - centre) > 0`, not by axis sign** — screen meshes are double-sided and parents are often rotated 180°, so axis selection lights the wrong side half the time.
- **Model sky light through a window as one flat emitter panel filling each opening, never as a shell lining the walls** — an emitter 0.1–0.5 m from a surface makes a 1/d² hotspot at every point where it nears the wall.
- **Move a lamp's spill (emitter intensity) and its fixture look (shade emission and colour) as separate knobs, often in opposite directions** — "too bright" usually means the wash on the room. The shade's look needs no bake when it carries the light mesh (see SKILL.md §Workspace lighting standard).
- **Light a painting with one cone per work from a light set out from the wall (axis about 30° off vertical, range past the bottom corner). In a dark room, make the canvas self-emissive instead** — aiming at the centre puts the hot spot above the frame, and overlapping cones never blend.
- **With non-realistic falloff, widen a high fixture's range to reach the floor instead of raising intensity** — range is a hard cutoff, and more intensity blows out the ceiling before the floor reads.

## Brightness, mood and exposure

- **Treat albedo near 1.0 on large interior surfaces as a bug: audit by lit area and darken the surface driving the gain, never the floor** — multi-bounce gain is about 1/(1−albedo), so a white ceiling made a small light change bake 5× brighter.
- **Measure region luminance first. If the outside out-measures the inside, darken fog, sky, sun and sky light by one shared factor in one atomic pass** — a cozy interior needs that contrast ordering before it needs props, and scaling them separately breaks the locked brightness order.
- **For a misty night, order values ground < vegetation < fog < horizon, dim the lights instead of the materials, and use a gradient skybox whose below-horizon colour equals the fog colour** — the fog then reads as the luminous element. Skybox/Procedural adds bright wedges.
- **After any global dim pass, re-render every recorded "ambient-only / no emission" exception** — those decisions depended on the old ambient level, and the pass turns them pitch black without any warning.
- **Restrict helper and preview realtime lights to their own layer with `cullingMask`, or delete them, before judging a bake** — a shadowless realtime directional light adds flat light to every lightmapped surface (see SKILL.md §Washed-out bake debug sequence).
- **Match the HDRI sun to the baked sun in azimuth as well as elevation by measuring the skybox's peak luminance, fix it with the skybox `_Rotation`, then re-render the probes** — a 180° azimuth error puts the visible sun on the shadow side, and nothing warns.

## Diagnosing a bad-looking bake

- **When a new prop reads cold, check `lightmapIndex` before re-tinting** — -1 means it was not in the last bake and falls back to skybox ambient. A re-tinted material will be wrong once the bake lands.
- **Find lights that baked black by listing `%TEMP%\frender\light_<n>_1_HDR.lz4` sizes after a bake** — dead lights all compress to one identical small size, while working lights vary.
- **Sample lightmap irradiance under each submesh (Blit to float, map UV2 through `lightmapScaleOffset`) before blaming occluders** — a floor reading "baked black" had normal irradiance and was just dark carpet.
- **Tell dark geometry from a baked shadow by rendering the same pixel with the suspect renderer on and off** — comparing against the surfaces on either side gives contradictory answers in a gradient. A deleted caster leaves its shadow in the atlas until you rebake.
- **Clamp a few blown texels with a C1 soft-shoulder curve (scale RGB to keep hue) after proving players can actually see those texels** — this is cheaper than a rebake, a hard clip creates bands, and many hot texels sit in unsampled padding.
- **Remove a smooth ramp near an emitter by dividing out a world-space, per-channel, low-frequency field with gain ≤ 1, ignoring shadowed texels** — unlike a clamp, this keeps the high-frequency detail. A blur in UV space bleeds across chart islands.
- **Read Radiance `.hdr` files with a real RGBE decoder (RLE scanlines, `m·2^(e−136)`), not imageio** — imageio returns the uint8 mantissa without the exponent, so every radiance statistic is meaningless.
- **Tag a custom alpha-cutout shader's SubShader `"RenderType"="TransparentCutout"`, never `Opaque`** — the Progressive lightmapper picks alpha-tested shadow casting from that tag, so an Opaque-tagged leaf shader bakes every card as a solid rectangle shadow even though `clip()` cuts it on screen.

## Motion and runtime lighting states

- **For day/night or lights-off switches, bake twice with identical atlas packing, append bake B to `storage.maps`, and offset `Renderer.lightmapIndex` from Udon** — these setters are exposed to Udon and Bakery rebinds lightmaps at runtime. Adding or removing a light mesh between the two bakes repacks the atlas.

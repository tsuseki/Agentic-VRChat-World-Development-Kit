---
name: fumo-plushie
description: "Make a fumo-style plush pickup of a character (usually from VRChat avatar screenshots) for a VRChat world, end to end: concept views with user approval, Tripo Studio generation (Smart Mesh P2.0 Quad, polycount 2000, 4 takes, sidebar texture), Blender prep without decimation to one material and a 1024 texture, colour grade, mandatory self-review against the best existing plush, lineup with existing plushies and a 1.4 m figure, Unity import, gravity pickup with rest supports, fire-scream wiring, shelf placement and dressing review. Use when: the user asks for a plush, fumo or doll of a person/avatar/character in a world, or a placed plush needs regenerating, fixing, moving or screaming."
---

# Fumo-style plush pickups

A plush is a small hero prop that players pick up, carry and drop, so it must read as *that*
character at 25 cm, cost about as much as a cup, and rest on a shelf without floating or falling
through. Lessons: [references/lessons-fumo.md](references/lessons-fumo.md).

Tools: `python .omp/scripts/tool.py image-edit | image-to-3d | blender` (`.omp/docs/tools.md`).
Exit 3 = hand-off (do it yourself or ask the user); exit 4 = the spend needs the user's approval: stop
and report the cost. Scripts below are in `scripts/`; Blender ones run through the `blender` tool
(`--script <path> -- <args>`) and need xatlas in Blender's Python for `retopo_prep.py`.

Keep each run in `<project>/SourceAssets/Fumos<date>_<Name>/`: `refs/`, `work/`, `prompts/`, `views/`,
`tripo_slots/`, `gen/`, `k/` (generation and prep outputs), `ship/` (the deliverable), `BRIEF.md`
(character list, approvals, take choice).

## The recipe in one paragraph (the "Kutsu way")

Approved four-view concept → Tripo Studio, **Smart Mesh P2.0, Topology Quad, polycount 2000, four takes**
(about 2,600–2,900 faces, 4.4–4.5k tris) → pick the take from all sides → sidebar texture,
**Remove Lighting on, 2K** → export FBX → `retopo_prep.py` (scale, bottom-centre pivot, xatlas UV2,
**no decimation**, UV0 and the generated texture untouched) → grade colour casts → 1024 texture, crunch
off → self-review gate → lineup → Unity. The earlier "minimum quad count, 2,500 tris, 512² crunched,
decimate and rebake" rule is removed: it produced meshes and faces the user judged worse than Kutsu.

## Budgets

| Item | Target |
|---|---|
| Triangles | about 4.5k as generated (polycount 2000); never decimate unless a strict budget is imposed (see Fallback) |
| Materials / textures | 1 material; BaseColor only, 1024², compressed, **crunch off**; no normal map |
| Lightmap | none for pickups (Light Volume lit); a static display plush: authored UV2, Scale In Lightmap 8 |
| Size | 0.25 m tall including ears, bottom-centre pivot, Y up, front -Z |
| Proportions | stubby legs no taller than the head, normal fumo smile |
| Audio | one shared scream clip, mono Vorbis, 3D 0.5–8 m |
| Copies | one per character per world |

## Pipeline

**1. Reference.** Collect the avatar screenshots (full-body front, face, side, back); crop to
`work/ref_*.png`. List the identifying features; ask only about what the screenshots don't show. A
character that already exists in the world is moved or replaced, never duplicated.

**2. Concept views + approval.** Front first, then left/right/back as "reproduce EXACTLY … change ONLY"
edits of the approved front. Prompts, references and commands:
[references/concept-prompts.md](references/concept-prompts.md). Rules that always apply: stubby legs
(≤ head height, even with thigh-highs), normal fumo smile, asymmetric features named by image side,
a real-fumo photo (and an approved plush of the world) as style reference, simple flat-felt hair
shapes (wide locks, plain full-coverage black tops rather than fine detail). Show the four-view sheet
beside the screenshot. **The user approves the views before any generation; a design approval is not a
spend approval.** Copy the approved views to `tripo_slots/{front,left,right,back}.png`.

**3. Generate (Studio, four takes).** Tripo Studio only; the API cannot select these options.

```
export TRIPO_STUDIO_PROFILE=<persistent logged-in Chrome profile directory>
python scripts/tripo_studio.py generate <run> 2000    # P2.0 Quad, 4 takes, same polycount
python scripts/tripo_studio.py takes <run>            # contact row of the four takes
python scripts/tripo_studio.py views <run>            # all sides of each take (clay)
```

Credits: about 100 for the four takes, 10 for the texture. Pick the take from all sides: eyes and fringe
clean, no hair over the eyes, legs short, tail/wings/ears intact, asymmetric features not mirrored. If no
take passes, generate again with more takes before you touch anything else.

**4. Texture and export.**

```
python scripts/tripo_studio.py texture <run> <take>   # sidebar panel, Remove Lighting ON, 2K
python scripts/tripo_studio.py export  <run> <take>   # FBX zip -> <run>/gen/export/
```

Never run the service's Smart UV (it deletes the texture) and never use the viewer-bar texture button.
Before each Studio step kill only the stale Chrome whose command line contains the profile directory.

**5. Prep without decimation.**

```
B="python .omp/scripts/tool.py blender --script .omp/skills/fumo-plushie/scripts"
$B/retopo_prep.py -- gen/export/<model>.fbx k/out sheets Fumo_<Name> 0.25
```

Writes `Fumo_<Name>.fbx` (UV0 `UVMap` as generated, UV2 `UVMap_Lightmap`, 0.25 m, bottom-centre) and
`Fumo_<Name>_BaseColor.png` (2048, Standard view transform). Check the REPORT line (tris about 4.5k, one
material) and run `texture_check.py -- <written.png> <source.png>` (must PASS).

**6. Grade colour casts.** Tripo's Remove-Lighting textures drift from the concept (a pale blond
arrived orange, dark brown arrived near black red, ash hair arrived tan). Measure, then grade only the
class that drifted:

```
python scripts/grade_texture.py measure k/out/Fumo_<Name>_BaseColor.png hair_blond   # median RGB of that class
python scripts/grade_texture.py measure views/front.png hair_blond                   # same class in the concept
python scripts/grade_texture.py grade k/out/Fumo_<Name>_BaseColor.png k/out/graded_2k.png hair_blond=229,191,145[@0.5]
```

Classes: `hair_blond`, `hair_blond_tex`, `hair_ash`, `hair_brown`, `skin`, `red`, `blue`. Use the class
window that is wide enough that unmasked patches don't show as blotches; use strength 0.5–0.7 when hair
and skin drift the same way. Only grade what clearly differs; an untouched texture that matches the
concept is the best result.

**7. Ship the texture.** Downsample the final 2K to 1024 with LANCZOS, `optimize=True`, under the file
name the FBX expects: `Fumo_<Name>_BaseColor.png`. Copy FBX and texture to `ship/`.

**8. Self-review gate (mandatory, before showing anything).** Render near-reach front and 3/4 close-ups
of the face and body next to the best existing plush (Kutsu in the first world):

```
$B/closeup.py -- <out> <HZ> <DF> kutsu=<fbx>=<tex> <name>=<fbx>=<tex>
```

`HZ` is the camera height as a fraction of body height (0.6 face, 0.3 torso, 0.07 legs), `DF` the
distance factor (0.5–0.7 face, 0.85 body); vary `HZ` per character so the eyes sit mid-frame. The new
plush must look at least as clean as the reference. Fail if any of these show:

- eyes smeared, offset or double; mouth missing or not a normal smile
- fringe shredded, hair bleeding into the eyes
- legs longer than the head
- colour cast against the concept (hair, skin, clothing); oversaturation
- scuffed or noisy flat clothing (then `clean_flat_regions.py`, see below)
- asymmetric features mirrored; missing inner faces, holes, torn tails or wings
- seams or blotches on the face

On a failure redo the step that caused it (another take, a re-grade), with more takes if needed. Do not
patch with ad-hoc scripts. Write the take choice and what was redone to `BRIEF.md`.

**9. Lineup sheet.** Render the new plush beside the existing ones and a 1.4 m figure:

```
$B/lineup_sheet.py -- sheets <new fbx> <existing plush fbxs...>        # scale lineup: heights and SPREAD
$B/lineup_flat.py   -- <out> name=<fbx>=<tex> ...                      # front, q34, side, back tiles
$B/lineup_shaded.py -- <out> name=<fbx>=<tex> ...                      # shaded 3/4 on a shadow catcher
```

Compose tiles with PIL or `lineup_compose.py` (6 columns, labelled). Show the user the concept front, a
`sheet.png` (concept, front, 3/4, left, back, right) and the face close-ups beside the reference. Fix height
in prep, not in Unity.

**10. Unity import.** Drive the open editor through MCP (`.omp/skills/unity-mcp-scripting/SKILL.md`).
Copy FBX + texture into the world's plush folder, then run `scripts/unity/unity_fumo_import.cs.txt`
(SessionState `FumoImport`): scale 1 with file scale, **no generated lightmap UVs**, no imported
materials, texture 1024 compressed, **crunch off**, one material `M_Fumo_<Name>`
(`Light Volume Samples/Light Volume PBR` by default; the script warns on a fallback to Standard in a legacy
world; metallic 0, smoothness 0.1). Read the console for errors; measure in a later call.

**11. Pickup + placement.** Choose the shelf (rules below), then run `scripts/unity/unity_fumo_pickup.cs.txt`
(SessionState `FumoPickup`): replaces `Fumo_<Name>` in place if it exists, else places it bottom-centre on
the support point at the given height and yaw. One tight BoxCollider, Rigidbody gravity on and not
kinematic, `VRCPickup` proximity 0.1 / AutoHold No, `VRCObjectSync`, layer Pickup, not static, probes on;
it reports the support and the gap. `NO SUPPORT` or a support that isn't the visible surface: add one with
`scripts/unity/unity_rest_support.cs.txt` (`<room>/PickupRests/Rest_<Surface>`, BoxCollider on layer
Walkthrough 17, top flush with the surface) and re-run. A decoration-only plush gets no collider,
Rigidbody or sync; static, ContributeGI, authored UV2, Scale In Lightmap 8.

**12. Scream in fire.** Only when the world has fires (fireplace, fire pit, brazier; candles are not).
Copy `scripts/unity/Udon/*.cs` to `Assets/<World>/Udon/` and `scripts/unity/Editor/FumoScreamBuilder.cs`
to `Assets/<World>/Editor/`, wait for the compile (no `error CS`), then `FumoScreamBuilder.CreatePrograms`
→ wait → `ImportClips` → `Settings(clipPath)` → `Zone(name, centre, size)` per fire (flame area only) →
`WireAll()`. Clips: [references/scream-clips.md](references/scream-clips.md); the user picks. After
replacing a plush, run `WireAll()` again.

**13. Review.** Dispatch `dressing-reviewer` (`.omp/agents/dressing-reviewer.md`), stage C.1, with the
plush list and positions, the approved concept fronts and concerns: scale against neighbours and the
1.4 m eye, floating or sinking, style match with the other plushies, natural placement. Only SHIP IT
finishes the plush. Record each placed plush (path, support, height) in the project `AGENTS.md`, then
make a local backup commit.

## Optional steps and fallbacks

- **Flat clothing scuffed** (black or white clothing speckled, grey hairlines, lilac-tinted white):
  `uvpos.py` for the UV to 3D map, then `clean_flat_regions.py <tex> <uvpos.npz> <out> [--white-sat 0.35]`.
  It never touches the face, eyes, hair or coloured parts.
- **Ambient occlusion in the texture.** `uvpos.py` → `bake_ao.py` (per-vertex AO against a voxel proxy,
  cage-free, on the existing UV0) → `combine_ao.py <tex> <ao.npy> <uvpos.npz> 0.35 <prefix> 1024`;
  compare with `lv_ab_render.py` (Light Volume-style gradient light, A without and B with AO). The 2026-10-26
  test of five plushes found the difference between A and B barely visible: a slightly deeper shade under
  the fringe and chin on the two plushes with the most occluded geometry, nothing on the other three, no seams
  on the faces. Not shipped by default; keep the AO file as an optional `_AO` texture only if the A/B clearly
  looks better.
- **Strict triangle budget imposed** (the default does not need it): `protected_decimate.py -- <in.fbx> <out_dir>
  <name> <target_tris> 1` decimates while keeping the face zone (`FACE_Z0`, `FACE_Z1`, `FACE_W`
  environment variables) at full resolution so the embroidered eyes keep their UV mapping. Do not rebake
  through a cage: a 12 mm rebake cage tore the fringes and a uniform decimation smeared Nikki's eyes.

## Placement rules

- One copy per character, active. Move, never duplicate; never place clay placeholders.
- Plushies are decoration at the side of a room: **on a shelf**; where the room has none, a sideboard,
  credenza, window or fireplace ledge, or a desk corner. Several may share one shelf, spaced naturally.
- **Never on a sofa, armchair, chair or bed**, on a walkway, on stairs, in a door swing, on a counter in
  use, in front of a screen or inside a fire zone.
- Never move a plush the user placed. Check git history first.
- Spread through the world, one or two per room, facing into the room, not lined up on a bare display.
- Reachable by hand from where a player stands or sits (proximity is only 10 cm).

## Verification (report each with its value)

| Check | Pass |
|---|---|
| Re-import | `mesh_stats.py` on the shipped FBX: one mesh, about 4.5k tris, UV0 `UVMap` and UV2 `UVMap_Lightmap`; in Unity (later call) renderer height 0.25 ±1 cm, one material |
| Texture colour | `texture_check.py` PASS; unlit render beside the concept front shows the same colours; grading recorded |
| Self-review | the failure list in step 8 is clear, close-ups beside the reference saved in `ship/` |
| Importer | `generateSecondaryUV` false; texture 1024, compressed, crunch off |
| Contact / float | pickup script `support=<the visible surface or its Rest_*>`, gap within ±3 mm; play mode (wait a few seconds): plush moves < 5 mm, tilts < 2°, none fell; no scene save after play without this check |
| Pickup | proximity 0.1, AutoHold No, ObjectSync, gravity on, kinematic off, layer Pickup, exactly one BoxCollider |
| Scream | positive control: a plush moved into a zone in play mode screams once; every resting spot near a fire stays silent |
| One copy | exactly one object named `Fumo_<Name>` in the scene |
| Visual | `dressing-reviewer` SHIP IT |

Related: [asset-import](../asset-import/SKILL.md) (importer and placement details),
[image-to-3d-props](../image-to-3d-props/SKILL.md) (non-character props),
[bakery-light-baking](../bakery-light-baking/SKILL.md) (Light Volumes),
[unity-vrc-udon-sharp](../unity-vrc-udon-sharp/SKILL.md) (sync modes, network events).

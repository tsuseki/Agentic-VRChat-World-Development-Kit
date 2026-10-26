---
name: fumo-plushie
description: "Make a fumo-style plush pickup of a character (usually from VRChat avatar screenshots) for a VRChat world, end to end: concept views with user approval, image-to-3D at the minimum quad count, Blender prep to ~2.5k tris / one material / 512² texture, lineup with existing plushies and a 1.4 m figure, Unity import, gravity pickup with rest supports, fire-scream wiring, placement and dressing review. Use when: the user asks for a plush, fumo or doll of a person/avatar/character in a world, or a placed plush needs regenerating, fixing, moving or screaming."
---

# Fumo-style plush pickups

A plush is a small hero prop that players pick up, carry and drop, so it must read as *that*
character at 25 cm, cost about as much as a cup, and rest on furniture without floating or falling
through. Lessons checklist: [references/lessons-fumo.md](references/lessons-fumo.md).

Tools: `python .omp/scripts/tool.py image-edit | image-to-3d | blender` (`.omp/docs/tools.md`).
Exit 3 = hand-off (do it yourself or ask the user, save to `output`); exit 4 = ask the user to approve
this spend, then re-run with `--approve-spend`. Scripts below are in `scripts/` (Blender ones run
through the `blender` tool: `--script <path> -- <args>`); xatlas must be installed in Blender's Python
for `retopo_prep.py` / `fumo_remesh_bake.py`.

Keep each run in `<project>/SourceAssets/Fumos<date>_<Name>/` (`refs/`, `work/`, `prompts/`, `views/`,
`gen/`, `unity/`, `sheets/`, `BRIEF.md` with the character list, approvals and backend used).

## Budgets

| Item | Target |
|---|---|
| Triangles | ≈ 2,500 (≤ 3,000); generate at 1,000–1,500 quads |
| Materials / textures | 1 material; BaseColor only, 512² crunched (~170 KB); no normal map |
| Lightmap | none for pickups (probe / Light Volume lit); a static display plush: authored UV2, Scale In Lightmap 8 |
| Seated height | the world's existing plushies (default 0.25 m incl. ears); spread ≤ ±5 % |
| Audio | one shared scream clip, mono Vorbis, 3D 0.5–8 m |
| Copies | one per character per world |

## Pipeline

**1. Reference.** Collect the user's avatar screenshots (full-body front, face, side, back) and crop them
to `work/ref_*.png`. List the features that identify the character; ask only about what the
screenshots don't show. Check `WORLD.md` / project `AGENTS.md` for plushies already placed: a
character that already exists is moved or replaced, never duplicated.

**2. Concept views + approval.** Front first, then left/right/back as edits of the approved front:
references, prompt templates and commands in [references/concept-prompts.md](references/concept-prompts.md).
Show the four-view sheet next to the screenshot. **The user approves the views before step 3.**

**3. Image-to-3D at minimum quads.**

```
python .omp/scripts/tool.py image-to-3d --front views/front.png --left views/left.png \
  --back views/back.png --right views/right.png --faces 1500 --output gen/<Name>.glb
```

Exit 4: get the user's OK for this generation. Pick the best candidate from all sides
(`$B/render_glb.py -- gen/<Name>.glb sheets/glb`, `$B` as in step 5), checking that asymmetric
features did not mirror.
If the image-to-3d backend is Tripo: Smart Mesh **P2.0**, Topology **Quad**, the lowest quad count
(1,000–1,500), every candidate at that count; Studio and API credits are separate. When the configured
backend cannot select these, do the step in the web studio (manual hand-off) and save the GLB.

**4. Texture.** If the backend is Tripo: the **sidebar Texture panel** (not the viewer-bar button),
**Remove Lighting on**, **2K**. Never Smart UV (it deletes the texture). Other backends: textured
generation with baked-in lighting off where offered.

**5. Blender prep to budget.**

```
B="python .omp/scripts/tool.py blender --script .omp/skills/fumo-plushie/scripts"
$B/glb_to_fbx.py   -- gen/<Name>.glb work Fumo_<Name> 0.25          # scale, bottom-centre origin, BaseColor out
$B/mesh_stats.py   -- work/Fumo_<Name>.fbx                           # pieces, non-manifold (a few are fine)
$B/retopo_prep.py  -- work/Fumo_<Name>.fbx unity sheets Fumo_<Name> 0.25   # xatlas UV2, seam sheets, REPORT tris
$B/texture_check.py -- unity/Fumo_<Name>_BaseColor.png work/Fumo_<Name>_BaseColor.png   # must PASS
$B/fbx_sheet.py    -- unity/Fumo_<Name>.fbx sheets Fumo_<Name>       # textured + seams, 4 views
```

- Over budget: regenerate at a lower quad count (preferred), or decimate with
  `fumo_lv_prep.py -- <fbx> <out> Fumo_<Name> <target_tris> 512` (keeps UV0 and the texture).
- Probe-lit plush that looks flat: `fumo_lv_prep.py` with `target_tris` = current tris bakes
  AO into the BaseColor (no decimation); its FBX drops UV2.
- Noisy surface (hundreds of lightmap charts, blotchy test bake) on a static plush, or an approved
  older mesh that must keep its shape: `fumo_remesh_bake.py -- <fbx> <out> Fumo_<Name> 1400`.

**6. Lineup sheet.** `$B/lineup_sheet.py -- sheets unity/Fumo_<Name>.fbx <existing plush FBXs...>` renders
the new plush beside the existing ones and a 1.4 m figure (`lineup_scale/front/34.png`) and prints
heights and `SPREAD`. Show it to the user with the concept front. Fix height in step 5, not in Unity.

**7. Unity import.** Drive the open editor through MCP (`.omp/skills/unity-mcp-scripting/SKILL.md`).
Copy `Fumo_<Name>.fbx` + `_BaseColor.png` into the world's plush folder, then run
`scripts/unity/unity_fumo_import.cs.txt` (SessionState `FumoImport`): scale 1 with file scale, **no
generated lightmap UVs**, no imported materials, texture 512 crunched, one material
`M_Fumo_<Name>` (`Light Volume Samples/Light Volume PBR` when the project has VRC Light Volumes, else
Standard; metallic 0, smoothness 0.1). Read the console for errors; measure in a later call.

**8. Pickup + placement.** Choose the spot (rules below), then run
`scripts/unity/unity_fumo_pickup.cs.txt` (SessionState `FumoPickup`): replaces `Fumo_<Name>` in place if
it exists, else places it bottom-centre on the given support point at the given height and yaw. It sets
one tight BoxCollider, Rigidbody gravity on / not kinematic, `VRCPickup` proximity 0.1 / AutoHold No,
`VRCObjectSync`, layer Pickup, not static, probes on, and reports the support under it and the gap.
`NO SUPPORT` or a support that isn't the visible surface: add one with
`scripts/unity/unity_rest_support.cs.txt` (`<room>/PickupRests/Rest_<Surface>`, BoxCollider on layer
Walkthrough 17, top flush with the surface), then re-run the pickup script.

A plush the user wants as decoration only (not a pickup): no collider, Rigidbody or sync; static with
ContributeGI, the authored UV2 and Scale In Lightmap 8, its lowest vertex on the visible surface.

**9. Scream in fire.** Only when the world has fires (fireplace, fire pit, brazier; candles are not
fires). Copy `scripts/unity/Udon/*.cs` to `Assets/<World>/Udon/` and
`scripts/unity/Editor/FumoScreamBuilder.cs` to `Assets/<World>/Editor/`, wait for the compile and check
for `error CS`, then call `FumoScreamBuilder.CreatePrograms(udonDir)` → wait → `ImportClips(audioDir)`
→ `Settings(clipPath)` → `Zone(name, centre, size)` per fire (flame area only) → `WireAll()`. Clip
candidates: [references/scream-clips.md](references/scream-clips.md); the user picks. After replacing a
plush in step 8, run `WireAll()` again.

**10. Review.** Dispatch `dressing-reviewer` (`.omp/agents/dressing-reviewer.md`) with stage C.1, the
plush list with positions, the approved concept fronts, and concerns: scale against neighbours and the
1.4 m eye, floating or sinking, style match with the other plushies, natural placement. Only SHIP IT
finishes the plush. Record each placed plush (path, support, height) in the project `AGENTS.md`, then a
local backup commit of the project.

## Placement rules

- One copy per character, active. Move, never duplicate; never place clay placeholders.
- Plushies are decoration at the side of a room. Put them on a shelf; a bar back shelf counts. Where the room has no shelf, use a sideboard, credenza, window or fireplace ledge, or a desk corner. Several plushies may share one shelf, spaced naturally.
- Never put them on a sofa, armchair, chair or bed, on a walkway, on stairs, in a door swing, on a counter in use, in front of a screen or inside a fire zone.
- Never move a plush the user placed. Check git history first.
- Scattered through the world, one or two per room, facing into the room or the approach; not lined
  up on a bare display where they read as floating.
- Reachable by hand from where a player stands or sits (proximity is only 10 cm).

## Verification (report each with its value)

| Check | Pass |
|---|---|
| Re-import | `mesh_stats.py` on the shipped FBX: one mesh, tris ≤ 3,000; in Unity (later call) renderer height = target ±1 cm, one material |
| Texture colour | `texture_check.py` PASS (median Δ ≤ 10 per channel, chroma ratio ≥ 0.9); unlit Unity front beside the concept front shows the same colours |
| Importer | `generateSecondaryUV` false; texture 512, crunched |
| Contact / float | pickup script `support=<the visible surface or its Rest_*>`, gap within ±3 mm; play mode (wait a few seconds after entering): plush moves < 5 mm, tilts < 2°, none fell; no scene save after play without this check |
| Pickup | proximity 0.1, AutoHold No, ObjectSync, gravity on, kinematic off, layer Pickup, exactly one BoxCollider |
| Scream | positive control: moving the plush into a zone in play mode plays the scream once; negative: every resting spot near a fire stays silent |
| One copy | exactly one object named `Fumo_<Name>` in the scene |
| Visual | `dressing-reviewer` SHIP IT |

Related: [asset-import](../asset-import/SKILL.md) (importer and placement details),
[image-to-3d-props](../image-to-3d-props/SKILL.md) (non-character props),
[bakery-light-baking](../bakery-light-baking/SKILL.md) (Light Volumes, probe-lit props),
[unity-vrc-udon-sharp](../unity-vrc-udon-sharp/SKILL.md) (sync modes, network events).

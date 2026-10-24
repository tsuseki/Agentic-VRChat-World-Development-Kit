# Sources: fumo-plushie

Not needed to use the skill. Grouped by citing file.

## `SKILL.md`, `references/lessons-fumo.md`

- Budgets, generator settings, Blender prep, lightmap density, AgX bug, lighting choice — in-house
  bakeable-plush experiment log of a penthouse world (2026-10-22): 11 experiments on four characters
  (H3.1 multiview, P1.0 retopo, P2.0 quad at 2,000–8,000 faces, xatlas UV2, Bakery/Progressive test
  bakes at 16 texels/m × Scale In Lightmap 1/8/16, remesh + bake, Light Volumes + AO prep), with a
  world-wide prop budget and lightmap-density audit.
- Pickup, rest-support, one-copy, scatter and fire-scream rules — the same world's project log and the
  user's directives (2026-10-22 to 10-24), play-mode settle proof (2026-10-23) and dressing-reviewer
  C.1 SHIP IT for the placed plushies.
- "Light-volume small props and bake AO into the base texture" — a world creator's tip on a VRChat
  creator Discord (2026-10-22), anonymous.
- Pickup defaults (proximity 0.1, AutoHold No) — `.omp/AGENTS.md` "Pickups".
- VRChat reserved layers (Pickup 13, Walkthrough 17) — <https://creators.vrchat.com/worlds/layers/>
- VRC Light Volumes (REDSIM, MIT) — <https://github.com/REDSIM/VRCLightVolumes>
- Tripo Studio and API (Smart Mesh, quad topology, texture panel, separate credits) —
  <https://developers.tripo3d.com>, observed in the Studio UI 2026-10-22.

## `references/concept-prompts.md`

- Prompt templates — the prompts that produced the approved concept views of the 2026-10-22/24 runs
  (style v2 with a real-fumo construction reference; the approved-plush reference from the 2026-10-24
  run on). "Gift fumo" style: the Touhou Project plush line by Gift.

## `references/scream-clips.md`

- Clip list, licences and preparation — the scream candidates' `CREDITS.txt` of the same world
  (2026-10-23); licences as stated on each linked page at download.

## `scripts/`

- `glb_to_fbx.py`, `render_glb.py`, `fbx_sheet.py`, `mesh_stats.py`, `retopo_prep.py`,
  `fumo_remesh_bake.py`, `fumo_lv_prep.py`, `unity/unity_fumo_pickup.cs.txt`, `unity/Udon/*.cs`,
  `unity/Editor/FumoScreamBuilder.cs` — generalised from the experiment and build scripts above.
- `texture_check.py`, `lineup_sheet.py`, `unity/unity_fumo_import.cs.txt`,
  `unity/unity_rest_support.cs.txt` — written for this skill from the same runs' manual checks.
- xatlas Python bindings (mworchel, MIT) — <https://github.com/mworchel/xatlas-python>; xatlas
  (Jonathan Young, MIT) — <https://github.com/jpcy/xatlas>.

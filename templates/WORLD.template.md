# WORLD.md template

Copy into the project root as `WORLD.md`. The orchestrator owns it; agents read it. Keep the
brief short and quote the user's own words where they matter. Sections follow the pipeline phases
A–D (`.omp/skills/world-pipeline/SKILL.md`).

```markdown
# <World name>

## Pitch
<one paragraph, approved by the user on YYYY-MM-DD>

## Stage status
| Stage | Status | Gate result (reviewer, verdict, score, date, report path) |
|---|---|---|
| A.1 Setup | done | console clean |
| A.2 Information gathering | | user OK |
| A.3 Concept (shell layout + concept art) | | layout-reviewer RANKED; user pick; style rounds user pick |
| A.4 Design Lock | | user approval |
| B.1 Floor plan | | |
| B.2 Greybox | | |
| C.1 Build-out | | see Build-out area tracker |
| C.2 Interactions & playability | | |
| D.1 Lighting | | |
| D.2 Performance | | |
| D.3 Ship | | user uploads |
| D.4 Retro | | |

<!-- ===================== A · Concept ===================== -->

## Brief (A.2)
Extracted from what the user supplied; gaps asked. Source: user / doc / reference image / inferred / default.
| Field | Value | Source |
|---|---|---|
| World kind | living space (or: event world) | user |
| Event type and function (event worlds only) | type (talk / race / auction / ...); what happens, in what order, participants vs spectators, phases | user |
| Purpose | hangout | user |
| Space archetypes (A1–A5) and people each | A1 bedroom ×2 (2–4), A2 lounge (8) | user |
| Cuddling / lying close | yes | user |
| Capacity typical / peak | 8 / 16 | user |
| Reference eye height / avatar height | 1.3 m / about 1.4 m (full-size groups: 1.6 m / 1.75 m); everything visible built at real size ×0.8 (fixed), only collision minimums fixed | default |
| Platform | PC; Android: later \| yes \| no; iOS: Android fallback \| own build \| no | user |
| Setting / theme | ... | user |
| Mood, time of day, weather | ... | user |
| Interior darkness | dim | inferred |
| Realism | stylised-realistic | user |
| Scale and shape; view out | house, interior + terrace; city skyline | user |
| Style: palette | warm, muted; one ink-blue accent | user |
| Style: materials | walnut floors, cream plaster, brass | reference image |
| Style: lighting and time of day | night, low amber lamps, city glow | user |
| Style: era and place | 1970s Tokyo apartment | user |
| Style: exterior | interior only; skyline through glass | inferred |
| Style: furnishing feel | full, low, one huge sofa | user |
| Must-have spaces | ... | user |
| Interactions list (built in C.2) | video player in lounge; light toggles per room; lie-down collider toggle (no mirror: personal mirrors) | user |
| Dislikes | ... | user |
| Assets / paid tools | ... | user |

## References (A.2, accepted any time)
Images in `Design/references/`. Reference only — never shipped as world assets. Feel references, never blueprints.
| File | Tags (mood / lighting / palette / materials / massing / layout / object / sky / avoid) | What we take from it | Source |
|---|---|---|---|
| 01_rooftop-bar.jpg | lighting, mood | warm low pools, dark ceiling, city glow through glass | user-supplied |

## Involvement
Preset: Design lock, then autopilot (or: Every step / Custom: <named stops>)
| Stage | Decision | Who |
|---|---|---|
| A.2 | answers to gaps, brief summary | user |
| A.3 | concept pick (layout + look), style rounds | user (layout-reviewer ranks the shell layouts) |
| A.4 | Design Lock | user (once) |
| B.1 / B.2 | floor plan and greybox picks | agent (layout-reviewer) — Every step: user (B review) |
| C.1 / C.2 | each area, interactions | agent (dressing-reviewer) |
| D.1 / D.2 | lighting, perf | agent (final-reviewer, perf-optimizer) |
| D.3 | upload | user (always) |

## Concept (A.3)
Picked YYYY-MM-DD: look <letter> "<idea>" (style track, text → image) — `Design/concepts/genNN-text/`; layout <letter> (layout track, plain captures) — `Design/concepts/genNN-3d/` (images only; prompts in `Design/_prompts/`). Shell blockout `SHELL_PICK` + `Design/layout/vN.json` (layout-reviewer N/10); concept art binds mood and style only.
| Concept | Track | Idea | layout-reviewer | Strengths | Tradeoffs |
|---|---|---|---|---|---|
| A | layout | treetop village round a hearth | 8/10 | ... | ... |

Shell volumes of the pick (geometry authority for B):
| Volume | Use (hub / private / scenic / VIP) | Footprint m² | Storeys / height | Linked to | Notes |
|---|---|---|---|---|---|

## Style rounds (A.3)
Text → image rounds conditioned on the lock images, in `Design/concepts/genNN-style/`; approved set copied to `Design/lock/`.
| Round | Images | User pick / feedback |
|---|---|---|
| r1 | palette ×3, materials ×2, lighting ×2 | "warmer, less brass" |

## Design Lock (A.4)
Approved YYYY-MM-DD — user: "<exact words>". Images in `Design/lock/`, manifest `Design/lock/lock.json`
(`{file, item, tags, caption, feel, free, approved, user_words}`). Builders match the `feel`; reviewers
judge against it. Images bind mood, palette, materials, lighting character and density only — never
positions, proportions or layout. Changes only when the user reopens an item.
| File | Item | Tags | Caption | Feel (binding) | Free (not binding) |
|---|---|---|---|---|---|
| 01_palette.png | palette | palette | warm walnut, cream, one ink-blue accent | walls cream #EFE6D6; wood walnut; accent only on textiles | vignette furniture, layout |
| 03_lighting.png | lighting | lighting, mood | night, low amber pools, dark ceiling | 2700 K lamps at seat height; ceilings stay dark; city glow cool | window count, room shape |


<!-- ===================== B · Blueprint ===================== -->

## Floor plan (B.1)
Picked `Design/plans/vN.png` + `vN.json` (layout-reviewer N/10), inside the locked shells. Room purposes only, no furniture.
| Room | Archetype | People | Area m² | Zone (public→private) | Floor | Adjacent to | Notes |
|---|---|---|---|---|---|---|---|

## Greybox pick (B.2)
Variants `GREY_A..D` (layout-reviewer scores: A 7, B 8, C 6). Picked B YYYY-MM-DD, refined → `GREY_PICK`
(layout-reviewer SHIP IT, N/10). Refinements written back to `Design/plans/vN.json`. Not playable.

## Prop schedule (from the B.2 placeholders)
Exported from the greybox scene: one row per placeholder, id = the plan JSON `furniture` id (`pos`, `rotY`
there). Sizes are W×D×H in metres at the reference scale: real-world size ×0.8 (fixed). `Lie-down` = gets a `LieDownCollider` in C.2; `Solid` = big
furniture that gets an always-on `SolidCollider` in C.2. Source is filled in C.1 as assets are found.

### <Room id> (<archetype>)
| Item id | Type | W×D×H m | Qty | Role | Lie-down | Solid | Source |
|---|---|---|---|---|---|---|---|
| lounge-sofa | L-sofa | 2.3×1.6×0.65 | 1 | anchor | yes | no | to find / asset-finder: <path> / owned pack / to model |
| lounge-table | coffee table | 1.0×0.5×0.33 | 1 | anchor | no | no | to find |
| dining-table | dining table | 1.45×0.75×0.6 | 1 | anchor | no | yes | to find |
Secondary pieces and decor (by rule, not placeholders): density "2–4 small items per surface, none on the
floor mid-room"; style "ceramics, books, brass, dried flowers" (from the boards' feel); examples: vase,
stacked books, candle tray, framed print.

<!-- ===================== C · Build ===================== -->

## Build-out area tracker (C.1)
One row per pass. The pass plan is logged before building; the review's findings plus unfinished work
become the next plan. An area is done on SHIP IT with nothing left on its plan.
| Area | Pass | Plan (shell finish / furniture swap / dressing; assets) | Verdict | Style | Build | Moves from placeholders | Next |
|---|---|---|---|---|---|---|---|
| Lounge | 1 | shell finish + swap sofa, table | NEEDS WORK | 7 | 4 | sofa 0.3 m west (door swing) | fix junctions, dress shelves |

## Interactions & playability (C.2)
| Item | Where | Status | Notes |
|---|---|---|---|
| Colliders: walls, floors, big solid masses | all areas | | no colliders on small props |
| Solid colliders | every `Solid: yes` item | | child `SolidCollider`, BoxCollider, always on, floor to top surface |
| Stair ramps (one box per flight) | | | |
| Spawn + walk test | | | play-mode evidence path |
| Lie-down colliders | every `Lie-down: yes` item | | child `LieDownCollider`, BoxCollider, inactive by default |
| Lie-down colliders toggle (`LieDownColliderToggle`, one per world) | e.g. by spawn | | |
| Teleport doors (on the real doors) and islands | | | |
| Video / toggles / pickups (only if requested) / diegetic mirrors (bathroom, gym, dance room only) | | | |
| VIP gate | | | |
| Clip planes and fog | Reference Camera near/far; runtime near/far | 0.01 / 0.001; far 400; ExpSq ρ 0.007 | clip-planes §2 |
| World extent | cuddle zones < 256 m; occupied < 512 m; islands at ±220 m | | clip-planes §3–§4 |
| Backdrop | real geometry < 60 m; skyline in skybox at ≥ 4.6 km depicted | | clip-planes §5 |

<!-- ===================== D · Finish ===================== -->

## Lighting (D.1)
| Area | Draft bake mood vs boards | Final bake | Probes rebaked | final-reviewer |
|---|---|---|---|---|

## Approved levels (never raise without asking)
- e.g. lounge lamp intensity 0.35 approved YYYY-MM-DD

## Performance (D.2)
| Viewpoint | Frame ms (CPU / GPU) | Draw calls | Tris | Budget | Fixes applied | Visual regression check |
|---|---|---|---|---|---|---|

## Decisions log
Every decision, user or agent, and every D → C loop back.
- YYYY-MM-DD A.3: picked concept 3d:B "..." — user: "<exact words>" (layout-reviewer B 8 > A 7 > C 6; agrees). Route: 3D, because "<reason>".
- YYYY-MM-DD B.2: picked variant C (agent; layout-reviewer C 8 > A 7 > B 6).
- YYYY-MM-DD D.1 → C.1: lounge shelf floats in the draft bake (final-reviewer r-d1-2); redo D.1 lounge bake + probes.

## Lock gaps
Stylistic decisions in B–D that the lock did not cover, decided provisionally by dressing-reviewer against
the boards. Listed in the D.3 upload report; each becomes an information-gathering question at D.4.
- YYYY-MM-DD C.1: window frame colour → dark bronze (closest to 02_materials.png; dressing-reviewer) — intake question added: yes/no
```

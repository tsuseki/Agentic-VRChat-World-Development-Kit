# Spatial design: architecture and interior design for social VRChat worlds

Read this before you draw a plan, place a wall or review a greybox. AWDK worlds are **places people live
in and hang out in**: bedrooms, homes, penthouses, lounges, bars, cinemas and gardens. Design them the way an
architect and an interior designer would design a real home or venue. About 90% of the worlds this kit
builds are **intimate retreats** for 2–8 people who sit, cuddle and lie close together; when in doubt,
design for that case.

This guide condenses the kit's architecture, social-architecture and social-VR research and the maintainers'
production experience, including `case-studies/luxury-penthouse-layout.md`: designs users rejected, and the
fixes they accepted.

Clip planes, float precision, world extent, distant scenery and z-fight separation live in
`.omp/skills/clip-planes/SKILL.md` (cited here as "clip-planes §N").

**Tags.** Untagged rules come from published research.
- `[in-house]` = the maintainers' production experience and word of mouth, including the case study.
  `[in-house, measured]` = measured in the Unity editor (see `.omp/skills/clip-planes/SKILL.md`).
- `[INFERENCE]` = a researcher's synthesis or proposed number. Treat it as a tunable default.
- `[WORKSPACE RULE]` = a fixed policy of this kit.
- `[user rule]` = an explicit instruction from the kit's owner. It outranks research and in-house history.

**Precedence.** User rule > in-house > research. Each conflict is stated in one line marked **Conflict:**.

**Images are feel references, never blueprints.** Concept images, mood/style boards and reference
pictures set mood, palette, materials, lighting character and density. Never take positions,
proportions or layout from them: perspective and scale in AI images don't translate into 3D. Plans,
greyboxes and reviews work from this guide, the locked shell blockout (`SHELL_PICK`), the approved floor plan and the approved greybox
(pipeline skill "Design Lock"; review-protocol "Images are feel references").

**Pipeline stages** (`.omp/skills/world-pipeline/SKILL.md`): A.3 concept: shell-layout blockouts shown as plain captures (massing, links, arrival, extent; §2, §4, clip-planes), with style chosen separately by text → image concept art (mood and style only), B.1 floor plan inside the shells (§1–§4, §1.3 plan organisations, §8.1),
B.2 greybox with big-furniture placeholders (§2, §5, §8.2), C.1 Build-out and C.2 interactions and
playability (§5, clip-planes, §8.2 playability items), D.1 lighting (§5.4).

**Words.** Write about **guests**, **residents** or **people**. "Player" appears only in VRChat technical
facts (player capsule, player audio, `VRCPlayerApi`). Units: 1 Unity unit = 1 m. Eye heights: the
**reference eye height** from WORLD.md (default **1.3 m**, avatar about 1.4 m), very small or seated 0.9 m,
full-size 1.6 m, lying ≈0.4 m. Dimension tables give real-world values for a 1.6 m eye; §5.9 scales them.

---

## 0. Top rules

1. **Name the archetypes first.** Every space in the world is one of A1–A5 (§1). Size, light, seating and
   sound follow from the archetype, not from the theme. [INFERENCE]
2. **Default to A1, the intimate retreat.** Shelter, softness, a view out, warm low light, nobody walking
   past, and a near clip small enough for cuddling (clip-planes §1). [in-house]
3. **Order spaces by the intimacy gradient:** entrance → public → semi-private → private. Retreats sit at
   the far, quiet end.
4. **Never one extruded rectangle.** A building is 1 primary + 2–4 secondary + tertiary volumes. Single
   boxes were rejected twice. [in-house]
5. **Plausible and good-looking, not engineered.** Nothing floats; loads are visibly carried; every cut ends
   on an existing corner. [in-house]
6. **Pick a plan organisation and a section before placing walls** (§1.3), and name the idea in one
   phrase. B.1 floor-plan variants differ in organisation, never only in room sizes. [in-house]
7. **People sit at edges, with their backs covered and a view.** Groups go in pockets along walls,
   windows and alcoves; paths pass behind them, never through them.
8. **Seat groups are sociopetal:** corners and L-shapes, facing seats ≤1.07 m apart, never rows facing a
   wall.
9. **Light in pools,** low and warm, with darker places between them.
10. **Level changes sparingly:** at most one deliberate floor-level change per social zone, ≥3 risers or a
    ramp, never on the entrance → main-area path. No decorative half-steps. [user rule]
11. **Voice carries 25 m through walls.** Separate retreats from loud rooms by distance or an audio zone.
12. **Size for the measured reference eye height** of the group (default 1.3 m, avatar about 1.4 m): the
    shell and outdoor features (trees, shrubs, rocks, landmarks) scale by eye ÷ 1.6, loose props stay real
    size, and nothing drops below the fixed collision minimums (§5.9). [user rule] [in-house]
13. **Stay near the origin.** Cuddle zones < 256 m and any occupied space < 512 m from (0,0,0) on every
    axis, teleport islands included. Pick near and far clip and fog per clip-planes §2. [INFERENCE]
    [in-house, measured]
14. **Workspace constraints are fixed:** no colliders on small props (exceptions: an always-on `SolidCollider`
    box on big furniture such as dining/kitchen tables, counters, cabinets and wardrobes; the disabled-by-default
    `LieDownCollider` on beds, couches and lie-on furniture, switched on by one world toggle); one ramp
    collider per stair flight; no realtime lights; ≤3M visible triangles per viewpoint; private rooms as
    teleport islands ≥200 m from the main area and inside the clip-planes §3 radii; never add seat stations
    unless asked. [WORKSPACE RULE]

---

## 1. Space archetypes

### 1.1 The five archetypes

| # | Archetype | People | Typical rooms | m² per person | Ceiling | Character |
|---|---|---|---|---|---|---|
| **A1** | **Intimate retreat** (default, ~90% of worlds) | 2–8 | bedroom, nook, cozy apartment, cuddle or lying space | 4–8 | 2.1–2.7 m; ≈2.3 m over the bed | shelter, softness, closeness, a view out, away from everyone |
| **A2** | **Social home / hangout** | 8–20 | house, penthouse, lounge with several rooms | 8–14 | common room ≥3.0 m; varied | a house with a heart; rooms of different intimacy round it |
| **A3** | **Gathering venue** | 20–80+ | bar, club, party floor, lounge hall | 4–8 (VR, not code densities) | 3.0–3.7 m; lower soffits over booths | bustle, people-watching, one strong focus, pockets to talk |
| **A4** | **Audience space** | any; all face one focus | cinema, stage, talk room | per seat: row pitch ≈1.4 m | dim house, lit focus | clear views from every seat; social seats at the back |
| **A5** | **Scenic / walk-and-talk** | small groups moving | garden, park, promenade, beach | loop 150–400 m; stop every 30–60 m | open sky; refuges under canopy | walking side by side, stopping at edges with a view |

Areas and ceilings here are real-world values for a 1.6 m eye; scale them per §5.9 (lengths ×k, areas ×k²,
collision clamps apply).

### 1.2 How to pick and combine them

- Gather at A.2 which archetypes the world contains and for how many people each (`intake.md`). If the user
  only says "a cozy place for us", the world is **A1**, possibly nested inside an A2 home. [INFERENCE]
- Size every room from its archetype's m²/person band, then lay the rooms out along the intimacy gradient
  (§4).
- Common mixes:

| Mix | Pattern |
|---|---|
| A2 home + A1 bedrooms | Heart of the house central; bedrooms at the end of the gradient, off a turning corridor or as teleport islands |
| A2 home + A1 away room | A small retreat off the common area for two to four people |
| A3 venue + A1 retreats + A4 stage | Busy floor central, booths along the edges, quiet rooms up a stair, down a turning corridor or ≥25 m away |
| A2 home + A4 media room | Media room off the common area, away from bedrooms; sofas in sociopetal groups that can turn to the screen |
| A5 garden + A1 pavilions | A walking loop with stops; refuges at vegetation edges with views back |

- Each archetype keeps its own rules inside a mix: an A1 bedroom inside a party world is still sized,
  lit and separated as an A1. [INFERENCE]

### 1.3 Plan axes: how B.1 floor-plan variants differ

Every floor-plan variant states one value per axis in a **header line**. Variants differ in **organisation**, not in
room sizes or decoration. [in-house]

| Axis | Values | Tag |
|---|---|---|
| **A Plan organisation** | centralized · linear · radial · clustered · grid | |
| **B House / venue type** | courtyard · L or wings · central hall · gallery / enfilade · open loft · pavilions in a garden · stacked tower | [INFERENCE] |
| **C Section** | single storey with varied ceilings · double-height room with a gallery or mezzanine · split into two storeys (public below, private above) · raised roof with clerestory · bridge or wing over an outdoor room · one deliberate level change (§5.5) | [in-house] |
| **D Relation to outside and view** | introverted (courtyard, view slots) · one framed panorama released at a threshold · extroverted (glass, terraces) · layered threshold rooms (loggia, porch, terrace) | |
| **E Archetype mix** | which of A1–A5, and how they nest (§1.2) | |
| **F Signature space** | the one room people remember: a bed alcove under a skylight, a fireside nook, a library gallery, a rooftop terrace, a bar under a glass roof | [in-house] |
| **G Organizing idea** | one short phrase ("rooms round a courtyard", "core splits public from private") | |

**Divergence tests** [INFERENCE] unless tagged:
1. Header line per concept with all seven axis values.
2. Any two concepts differ on A or B, and on C or D. Same program, same archetype mix (unless the user asked
   for alternatives), equal fidelity: pitch, plan, section, one eye-height image.
3. **Name-swap test:** if B is "A with a room moved, enlarged or restyled", B is a variant. Regenerate it
   with another organisation.
4. **Strip test:** with furniture, materials and theme words removed, the concepts are still distinct in
   plan and section.
5. ≥1 **safe** concept (still not a box) and ≥1 **contrarian** concept that questions a brief assumption.
6. The layout reviewer scores the set against 2–5 before any single concept is chosen. [in-house]

### 1.4 Shotgun process
- Present plans as rendered images, never ASCII. Draw doors. Ground floor above upper floor, portrait. [in-house]
- One change-set per version, closing exactly the previous round's feedback. Keep every version. [in-house]
- B.2 greybox variants side by side in one scene: walls, volumes and big-furniture placeholders, with the
  reference-person capsule and area labels. Expect a pick "with changes", then 3–5 refinement rounds. [in-house]
- Measure the live scene before redrawing it. Plans drawn from memory invented a wall and missed a
  freestanding one. [in-house]
- Preserve approved layouts. Unsolicited reworks get reverted; change layout only against explicit
  feedback. [in-house]

### 1.5 Which sections apply

Decision table: archetype → sections to load. Builders and reviewers both start here: name the
archetype of the target area (from WORLD.md), then work from that row. §5.6–§5.11, §8 and `.omp/skills/clip-planes/SKILL.md` apply to
every archetype; §2 applies wherever architecture is built. Key numbers are real-world values for a 1.6 m
eye; scale them per §5.9.

| Archetype in the area | Read | Key numbers |
|---|---|---|
| A1 Intimate retreat | §5.1, §5.2, §5.4, §5.8, §5.5, §5.11, **§3.1**, §4 if nested | 4–8 m² per person; bed clearance 0.76–0.91; alcove ≤1.83 × 0.9–1.8; facing seats ≤1.07; ceiling over bed ≈2.3 |
| A2 Social home | §5.1–§5.5, §5.8, §5.11, **§3.2**, §3.1 for its private rooms, §4 | 8–14 m² per person; common room ≈5 × 7 m, ≥3 m ceiling; diner clearance 0.91–1.12 |
| A3 Gathering venue | §5.1, §5.2 (seat counts), §5.3, §5.4, §5.8, §5.5, §5.11, **§3.3**, §3.1 for nested retreats, §4 | 4–8 m² per person (VR); room ≤25 m across; stools 0.61–0.76; tables ≥0.30 apart |
| A4 Audience space | §5.4, §5.8, §5.5, §5.11, **§3.4**, §4 | first row ≥0.6 W; vertical angle <25°; row pitch ≈1.4; 30–40° screen field |
| A5 Scenic / walk-and-talk | §5.1, §5.2 (seat counts), §5.3, §5.4, §5.8, §5.5, **§3.5**, §4 | stop every 30–60 m; paths 2–3 m; views ≥6 m deep |
| Any mix of the above | **§4** first, then each area's own row | gradient order; 25 m or an audio zone between loud and quiet spaces |

- Judge each area by **its own row** (§1.2): an A1 nook inside an A3 venue is held to §3.1, not §3.3. [INFERENCE]

---

## 2. Massing and plausibility

### 2.1 Volume hierarchy
| Tier | Role | Share of built volume | Count | Examples | Tag |
|---|---|---|---|---|---|
| Primary | Main program; tallest or most distinctive | 40–60% | exactly 1 | double-height great room, hall, tower | [INFERENCE] |
| Secondary | Supporting wings or blocks | 10–25% each | 2–4 | bedroom wing, kitchen/dining block, stair core, annex | [INFERENCE] |
| Tertiary | Human-scale accents | <5% each | 4–12 | bay window, entrance canopy, chimney, balcony, roof pavilion, planter wall | [INFERENCE] |

- The primary is ≥30% bigger or taller than any secondary. Never two equal primaries (within ±15%). [INFERENCE]
- A bigger mass with a more unusual shape reads as more important. Contrast the primary on ≥2 of height,
  size, shape, orientation, light.
- Massing supports program: every volume maps to a real interior zone. No decorative-only masses. [INFERENCE]
- The envelope moves; the program doesn't. "More dynamic" means "rooms stay mostly the same, only the
  building shape changes": cut corners plus push/pull plus an overhang, "not abstract art". [in-house]

### 2.2 Volumes per footprint [INFERENCE]
| Footprint | Primary | Secondary | Tertiary |
|---|---|---|---|
| ≤150 m² | 1 | 1–2 | 3–5 |
| 150–500 m² | 1 | 2–4 | 5–10 |
| >500 m² | 1 | 4–6, grouped into wings | ≥10 |

- More than ~8 "equal" pieces reads as camouflage: merge them and keep detail tertiary. [INFERENCE]

### 2.3 Cuts and junctions
- Join volumes edge-to-edge, face-to-face or interlocking; subtract for recessed entrances, courtyards and openings.
- **Every diagonal or corner cut terminates on an existing corner.** No leftover notch, dent or pocket. The
  accepted fix ran one clean 45° line corner to corner. [in-house]
- Rotate only the focal mass off-grid, and only with a reason; ~90% of corners at 90° and on-grid. [INFERENCE]
- Smallest articulation that registers: **0.6 m in plan, 1.2 m in height.** 0.1–0.3 m steps read as modelling errors. [INFERENCE]
- Façade: step ≥1.8 m in plan or ≥1.2 m in height every ~7.6 m; no unbroken run over ~8 m; ≥1 projection
  ≥0.6 m deep; recessed porches and balconies ≥1.8 m deep.
- Blank planes >~15 m² facing a main route get rejected (a 24 × 5 m blank stair wall was). Break them with an
  opening, setback, material joint or built-in. [in-house]

### 2.4 Overhang and cantilever plausibility
| Check | Number | Tag |
|---|---|---|
| Cantilever length | ≤1/3 of the visibly anchored backspan; longer needs a deeper edge or visible support | |
| Beam/edge depth | ≈ span/24 (9 m span → ≈0.38 m) | |
| Slab/roof edge (visual) | ≥0.25–0.35 m; 0.4–0.6 m at long spans | [INFERENCE] |
| Column grid | columns ≥0.25–0.5 m on a 6–12 m grid, aligned with walls above | [INFERENCE] |
| Balcony projection | ≤2.4 m projected; ≥1.8 m usable depth | |

- Nothing floats: no gaps >0.02 m at bearings; stairs connect landing to landing. [INFERENCE]
- Glass never visibly holds up a solid mass; a glazed storey under a solid one needs columns or a deep transfer beam. [INFERENCE]
- Heavy at the bottom, lighter on top.
- Long overhangs use one support language (deep fascia, brackets, tie-rods or tip columns). Accepted example:
  a wing whose last 6.25 m is an open balcony on 2 columns. [INFERENCE] [in-house]
- Pools and roof gardens sit over the primary mass or the column grid, not on cantilevers. [INFERENCE]
- No detached "floating ceiling rafts"; bulkheads and soffits bear visibly on walls. [in-house]

### 2.5 Silhouette and rooflines
- Render 4 elevations plus 2 three-quarter views flat black on white. **Pass:** ≥3 distinct top heights
  ≥1.2 m apart, ≥1 recess, ≥1 projection, a dominant mass readable in 2 s. **Fail:** an outline fills >90%
  of its bounding rectangle. [INFERENCE]
- Cascade the roof: highest over the large central rooms, lower toward the edges.
- Set the top volume back ≥1.8 m so the setback is a usable terrace. Finish every roof edge (parapet,
  cornice, overhang). Vary setbacks between floors ("wedding cake" otherwise). [INFERENCE]
- A raised roof with a clerestory over one room is a cheap, well-received height step. [in-house]

### 2.6 Material per volume
- Each secondary volume gets a material distinct from the primary; ≤3 façade materials + 1 accent; change
  material only at joints or setbacks; heavier materials at the base. [INFERENCE]

---

## 3. Per-archetype rules

Areas, room sizes, ceilings and path widths in these tables are real-world values for a 1.6 m eye. Scale
them per §5.9 (lengths ×k, areas ×k², k = eye ÷ 1.6) and clamp at the collision minimums; seat, table, bed
and sightline numbers stay real size.

### 3.1 A1 Intimate retreat (2–8 people)
| Aspect | Rule | Tag |
|---|---|---|
| Area | 4–8 m² per person: 4-person nook 16–25 m², 8-person cozy lounge 35–50 m²; king bedroom for 2 is 11–13.7 m². Below ~3 m²/person feels claustrophobic in VR; above ~10 m²/person voices feel far apart | [INFERENCE] |
| Ceiling | 1.8–2.1 m for one or two people, 2.1–2.7 m for small groups; lower it to ≈2.3 m over the bed, or use a canopy; 1.2 m knee walls under a sloped roof add shelter | |
| Enclosure | Refuge = three enclosed sides plus overhead cover; alcoves ≤1.83 m wide × 0.9–1.8 m deep; bed alcoves; one large shared mat in an alcove is legitimate | |
| Lying | Cuddle bed or mattress platform for 3–4 people ≈2.4 × 2.4 m, one long side and the foot open; 0.76–0.91 m clear on open sides | [INFERENCE] |
| Seating | Corner and L arrangements; facing seats ≤1.07 m apart; least formal seats in corners; built-ins save floor and feel cozy | |
| View | Every A1 room gets a window place (window seat, bay, low sill) and a view ≥6 m deep | |
| Focal | A fire, a view or a screen; give a second focus for when the fire is out | |
| Light | Low warm pools (sconces up and down); refuge light differs from the room next door; several lighting scenes | |
| Sound | ≥25 m from any A3/A4 source or inside an audio zone; two A1 rooms ≥25 m apart or separate zones | |
| Circulation | A dead end is right here: the retreat ends the gradient. Arrive by a corridor that turns away, a compressing vestibule, or a ceiling/material shift. Nobody walks through it to reach anywhere else | |
| Near clip | 0.001–0.01 m at runtime so faces and hands survive at cuddling distance (clip-planes §1) | |

**Pitfalls:** bed floating mid-room under a tall bare ceiling (no shelter); furniture pushed tight to the
walls (room reads too small); oversized room; retreat opening straight off the party floor; door opening
straight onto the bed.

### 3.2 A2 Social home / hangout (8–20 people)
| Aspect | Rule |
|---|---|
| Area | 8–14 m² gross social floor per person; common room ≈4.9 × 7.3 m with a 3.05 m ceiling for kitchen + dining + living; at least one spacious area |
| Heart | One common area at the centre of gravity, paths tangent to it, anchored by food and fire; a big kitchen table under one warm light |
| Plan | Chain or loop the common rooms instead of corridors; private rooms open off them; bathrooms half-way along the gradient |
| Rooms | Couple's realm distinctly separate with its own sitting area; a room of one's own at the far end; an away room off the heart |
| Enclosure | "No one room entirely enclosed; no space totally connected to another": broken plan with half walls, glass, shelving, double-sided fireplaces |
| Ceiling | Vary heights to define places without walls: ≥3 heights ≥0.4 m apart |
| Seating | Several groups of 3–6, each sociopetal, each on its own rug (≈0.45 m rug-to-wall, sofa front legs on it); counter seats 0.61 m each with 0.91–1.12 m behind |
| Entry | A place to stand and glimpse the living space; a foyer focal point |
| Light | Pools per group; daylight on two sides of each room |
| Sound | Loud room (music, games) ≥25 m from quiet groups or behind an audio zone |
| Suite | Primary suite ≥4.9 × 5.5 m bedroom, away from kitchen and guest routes, buffered by closets and corridors; private terrace enclosed on ≥2 sides |

**Pitfalls:** one open box (no retreat, noise everywhere); corridor house; common area at one side cut by
paths; bedrooms off the foyer.

### 3.3 A3 Gathering venue (20–80+ people)
| Aspect | Rule | Tag |
|---|---|---|
| Density | 4–8 m² per expected person on the floor; never <4 m² at maximum capacity; >30 m²/person feels dead. Code occupant loads are egress maxima, not comfort targets | |
| Room size | ≤~25 m across (faces readable, one voice radius); ≤~30 people per room; split larger crowds across rooms and storeys | [INFERENCE] |
| Ceiling | 3.0–3.7 m; lower soffits over booths and alcoves | |
| Focus | Back bar or DJ is the focal point, lit brighter than the room, visible from ≥60% of seats | [INFERENCE] |
| Bar | Stools 0.61–0.76 m apart; 0.76–0.91 m circulation behind; island bars are the most space-efficient | |
| Seating | ≥40% edge or booth seats; booths with walls to the ceiling keep people longer; tables ≥0.30 m apart | [INFERENCE] |
| Zoning | Distinct social, quiet and dining zones; dancefloor larger than other areas, separated from the bar, DJ within it | |
| Retreats | Booth clusters ≥6 m from the dancefloor; quiet lounges ≥25 m or behind an audio zone; rest rooms for long events | |
| Edges | Line the perimeter with active edges: bar, booths, windows, displays | [INFERENCE] |

**Pitfalls:** hall too big; benches spread randomly; one acoustic space; dancefloor mixed with the bar
queue; hidden dark corners.

### 3.4 A4 Audience space
| Aspect | Rule | Tag |
|---|---|---|
| First row | Eye distance ≥0.6 × picture width; vertical angle to screen centre <25° from 1.2 m eye height | |
| Rows | Rake rows so each eye line clears the head in front; row pitch ≈1.4 m; seats 0.50–0.75 m wide. Stepped rows are the one place several level changes are expected; they sit off the entrance → main-area path | [user rule] |
| Home scale | Sit at 30° screen width (≈1.6 × diagonal) or 40° (≈1.2 × diagonal) | |
| Mixed use | Must work when nothing plays: sociopetal sofas that can turn to the screen, a social bar or lounge at the back. A static amphitheatre in a VR event space was ignored | [INFERENCE] |
| Light | Dim house light, lit focus, dark surfaces near the screen | |
| Sound | Screen or stage audio Far = room length, so it does not reach retreats | [INFERENCE] |

### 3.5 A5 Scenic / walk-and-talk
| Aspect | Rule | Tag |
|---|---|---|
| Route | A stop (bench, view, water, pavilion) every 30–60 m; full loop 150–400 m; perceived in stages, never one long straight | [INFERENCE] |
| Width | Main paths 2–3 m so two pairs pass; side paths 1.2–1.5 m | [INFERENCE] |
| Edges | Seats at vegetation edges and under trees: see without being seen too much; half shade with a view | |
| Views | Views ≥6 m, ideally 30 m; reveal slowly with curving edges; the best view at transitions, not from every seat | |
| Stimuli | Touchable water; breeze and rustling plants; ambient sound sources >8 m from benches | [INFERENCE] |
| Ground | Walked surfaces are smooth: terrain smoothed, slopes gradual, no rock/root bumps in the walk collider (each bump bobs the headset and builds sickness); roughness is visual only | |
| Extent | The garden counts as occupied space: it stays inside the clip-planes §3 radii; far scenery goes to backdrops or the skybox (clip-planes §5) | [INFERENCE] |

**Pitfalls:** long straight path with no stops; sunken plaza or stepped detour; benches back to back or
far apart; leftover open lawn with nothing to sit next to.

---

## 4. Combining archetypes: the intimacy gradient and thresholds

- **Order by depth from the entrance:** entrance → public (A3, A4, A5) → semi-private (A2 groups) →
  private (A1). Put sitting spaces at every step of the gradient, shaped by their position.
- **Program follows social exposure, not adjacency convenience.** The VR and server rooms were private, so
  they went upstairs; the gym was more public, so it went on a bridge visible from the garden. [in-house]
- **Arrival.** Approach → threshold → compressed entry → release into the main room. Give the entry a
  place to stand and glimpse the living space; withhold the full view and release it at a transition
  (Zen view). Houses with a transition from the street feel more tranquil.
- **Thresholds are lingering places.** People like spots where they see both spaces at once. At each
  threshold change ≥2 of ceiling height, floor material, light level, sound, enclosure. [INFERENCE]
- **Turn before private rooms:** a branch corridor that turns away, or a vestibule, before every A1 room;
  guests never pass the suite entry on the way to public rooms.
- **Half-open walls** (columns, interior windows, sitting walls, glass, half walls ≤0.9–1.1 m) link
  neighbouring archetypes visually while separating them.
- **Acoustic order:** voice and music get quieter along the gradient: A3 dancefloor → booths ≥6 m;
  A3/A4 → any A1 ≥25 m or an audio zone; two A1 rooms ≥25 m or separate zones. [INFERENCE]
- **Teleport islands** carry the deepest privacy: bedrooms and suites as separate rooms ≥200 m from the main
  area, reached by teleport doors whose fronts read as real rooms (§7). [WORKSPACE RULE] [in-house]

**Pitfalls:** retreat opening onto the dancefloor; all archetypes in one hall; private rooms on the way to
public ones.

---

## 5. Shared rules

### 5.1 Edges, backs and refuge
- People stay along façades and in transition zones where they can see both spaces; open floor fills only
  after the edges are taken. Indoors, guests settle along walls and near furniture.
- Each seat group within 3 m of a wall, rail, window or planter edge; room centres stay free for movement. [INFERENCE]
- ≥1 seat per group sees the room entrance; never seat a group with its back to the door. [INFERENCE]
- Prospect from each group ≥6 m (≥30 m preferred) and partitions in conversation views ≤1.07 m.
- Pockets 3–6 m across for 3–8 people, carved by walls, alcoves, canopies, rugs, planters and bulkheads. [INFERENCE] [in-house]

### 5.2 Conversation seating
- Default group 3–5 seats; add 2-seat pockets and one 6–10-seat big table or fireside. [INFERENCE]
- Corner-to-corner beats face-to-face, and both beat side by side. Facing seats ≤1.07 m front to front
  (1.5–1.8 m tolerated); group 2.4–3.6 m across; split beyond.
- Seats face a shared centre: seat front 0.9–1.6 m from centre, yaw within ±25°. Rows facing a wall or TV are not conversation seating. [INFERENCE]
- Neighbour seat centres 0.8–1.2 m; VR groups average 1.8–2.0 m head to head. [INFERENCE]
- ≥1 m ring behind seats; paths pass along the edge of groups, never through them.
- Seats ≥0.6 × capacity (about half of people sit); vary seating types. [INFERENCE]
- Chairs must be reachable: 0.84–0.85 m approach lanes. Unreachable seats are a blocker even when shots look good. [in-house]
- Sofa → coffee table 0.36–0.46 m. In rooms >5 m wide, float groups with circulation round them.

### 5.3 Focal points and something to share
- One primary focal point per room (fire, view, stair, bar, art wall), opposite or diagonal to the main entry; seat forward vectors converge on it within 30°. [INFERENCE]
- Each group has a non-seat feature within 2 m (table, fire, water, game): triangulation gets people talking.
- **Every view ends on something designed:** a console + lamp + art, a window, a niche. A corridor ending on "a floating pier beside a dark hole" was rejected. [in-house]
- **No world mirrors by default:** VRChat has personal mirrors, so there are no mirror zones or mirror toggles. A mirror goes in only as a real object where the room type has one (bathroom, gym, dance or dressing room), as part of that room, off by default. [user rule]

### 5.4 Light pools
- Lights low and apart, in pools round chairs and tables, with darker places between; warm light and surface colours.
- Non-uniform, peripheral light reads as pleasant; wall-washing adds spaciousness; keep the centre lit where clarity matters.
- Two-sided daylight per main room; daylit depth ≈2.5× window head height.
- Interiors read cozy only when darker outside; no fixtures hanging inside full-height glass. [in-house]

### 5.5 Level changes, used sparingly
- **At most one deliberate floor-level change per social zone.** Make it ≥3 risers or a ramp, edged with a
  contrasting tread, a rail or a ceiling change. Never on the entrance → main-area path, nor between a
  retreat and its bathroom or exit. [user rule]
- **Why sparing:** 1–2 riser steps cause the most stair accidents; people detour to avoid level changes;
  sunken plazas are dead; conversation pits wore thin; a 3–4 in sunken room was filled in.
- **Why allowed:** a step or two still lets the higher and lower places converse while reading as distinct
  places; raised platforms give overview.
- **No decorative half-steps, no pits made for their own sake.** The case study's sunken lounge pit and
  half-steps were ordered flat. [in-house]
- **Conflict:** in-house history says "flat floors inside rooms"; the owner's later rule allows one
  deliberate change per zone. The user rule wins; decorative half-steps stay banned.
- VR: colliders are smooth ramps, so tripping is gone, but head-height jumps, broken sightlines between
  seated groups and furniture placement problems remain. [INFERENCE]
- Most verticality comes from section: double-height rooms with a gallery, a second storey with an overlook,
  bridges, overhanging wings, roof terraces, raised roofs. Between storeys: stairs or fade-teleport lifts. [in-house]
- Under a void the void is real: no hidden ceiling collider acting as an invisible floor. [in-house]

### 5.6 Circulation and doors
- ≥1 loop through the common rooms; 1–3 primary routes. [INFERENCE]
- **Corridors are rooms:** corridor in front of private rooms ≥3.1 m clear (2.2 m was rejected); furnish
  hallway pockets (couches facing the doors they serve); widen junctions into halls (a 4.6 m-deep junction
  hall with a sofa lounge worked); squash sealed rooms first to find the width. [in-house]
- No corridor >10–15 m without a window, widening, niche, light change or turn. Circulation ≤20–25% of floor. [INFERENCE]
- Doors near room corners, not mid-wall. Furniture ≥0.6 m clear of every jamb. [in-house]
- Stairs inside the building (U-turn stairs in volumes); the main stair central and visible, with the
  threshold into the private floor at its top. One smooth ramp collider per flight; no spiral stairs,
  ladders or required jumps. [in-house] [WORKSPACE RULE]
- Every boundary is a believable edge (rail, glass, water, planting); no invisible walls. [in-house]

### 5.7 Spawn and arrival
- Spawn in an entry or vestibule one threshold from the main room, 5–10 m walk from the nearest group and
  ≤25 m from the heart, with the heart visible. In an A1-only world, spawn at the room's entry, facing the
  window or fire, not the bed. [INFERENCE]
- Spawn faces into the space within ±30° of the heart; nothing within 3 m in front; 3 m clear disc; ≥4 m
  clear height where the room allows (A1 rooms: at least the room's own ceiling, never under a soffit);
  flat floor; Respawn Height ≥5 m below the lowest floor. [INFERENCE]
- Video off at spawn; a poster or info wall nearby.

### 5.8 Sound and voice
- Voice reaches 25 m and walls do not block it. Group centres in one room ≥6 m apart (≥8 preferred). [INFERENCE]
- Use audio zones (e.g. UdonVoiceUtils) where distance can't separate loud and quiet.
- Each world audio source's Far = its room size, not the 40 m default; no 2D audio.
- Real-world comfort: conversation fails above ~60 dB background; soft social sounds need 45–50 dB. Keep
  music low near A1 and A2 groups.
- **Two ambience layers in every area.** A base bed always faintly present (room tone/HVAC indoors; soft wind or
  distant traffic outdoors) as one 3D source per room with Volumetric Radius ≈ room size, so it has no audible
  point (never a 2D source); plus placed sources on real emitters (fire, machine, water). No area is silent. [INFERENCE]
- A sourceless ambience's centre is never on a walkable path (it swings 180° as you pass): keep it out of
  reach and wide. Overlapping copies of one loop get variants or ±3–5 % pitch, or they flange.
- A source becomes audible about when its emitter becomes visible (ramp up at the doorway); indoor and outdoor
  versions of the same weather crossfade at the threshold. Mix the bed quieter than "realistic"; disable distant
  sources by zone.

### 5.9 Program, rooms and avatar scale
- Size rooms to the stated program. A residence gets no public showers or oversized gym; when in doubt, a smaller "wellness" room. [in-house]
- Room plans between 1:1 and 1:2.5; a large plan with a low ceiling feels oppressive (15 × 15 m at 2.7 m fails).
- Every room has a seat, focal object or activity, or it is cut. Rooms are unique: no mirrored copies. [in-house]
- **Reference eye height** (`eye_ref`, in WORLD.md): default **1.3 m** (avatar about 1.4 m), because the groups
  this kit builds for play small avatars: build for them, never for a full-size adult. Full-size groups use
  1.6 m. Always confirm at A.2 (intake.md checklist). [user rule]
- **Scaling rule.** §5.11 and the archetype tables hold real-world values for a **1.6 m eye**. With
  **k = eye_ref ÷ 1.6** (≈0.81 at the default):
  - **Shell ×k:** room plan dimensions (areas ×k²), ceilings, storey heights, corridor widths, door widths
    and heights, stair widths, outdoor path widths.
  - **Outdoor features ×k:** trees, shrubs, hedges, rocks, landmarks, terrain features (hills, cliffs,
    banks), bridges and outbuildings. Species and catalogue sizes are full-size real-world values; a
    real-height tree or building next to a 1.4 m person reads as oversized. [user rule]
  - **Built-ins about ×0.9** at the default (counters, millwork, built-in benches, window seats; ×1.0 at 1.6 m).
  - **Loose furniture and props real size** (×1.0), and so are stair risers and goings.
  - Rows marked ‡ in §5.11 were approved in the penthouse after its shrink (1.2 m eye), so they are already
    small-avatar values: scale them by eye_ref ÷ 1.2 instead (≈×1.08 at the default). [in-house]
- **Clamp: never go below VRChat's fixed player collision.** Avatar scaling "does not affect its collision
  with the environment": a 1.4 m avatar collides like a full-size one. Each scaled value is
  **max(scaled value, collision minimum)**, the minimum being the §5.11 Min: clear height over any walked
  floor 2.3 m, door height 2.1 m, stair headroom 2.0 m, nook or over-bed ceiling 1.8 m, door clear 0.81 m,
  primary path 2.0 m, stair width 0.91 m. At the default: small-room ceiling 2.4 × 0.81 = 1.95 → **2.3**;
  door height 2.4 × 0.81 = 1.95 → **2.1**; primary path 2.4–3.0 → **2.0**–2.45; storey 5 → 4.05 m.
  [INFERENCE]
- **Conflict:** the small-avatar shell wants low, narrow spaces; the fixed collision capsule needs
  headroom and width. The clamp wins: a room may read slightly large rather than block a player.
- **Conflict:** research says build at strict real-world scale; in-house shrinks the shell to the group's
  avatar, because perceived emptiness is the failure users report. Evidence: the penthouse was designed for
  a 1.75 m person (1.6 m eye) and "felt empty" to a group whose avatars were about 1.2 m; the shell was
  rebuilt ×0.625 (storeys 5 → 3.8 m), built-ins ×0.9, loose props real size, and after the shrink the doors
  still had to narrow. [in-house]
- Test eye-level views at eye_ref (default 1.3 m), at 0.9 m (very small or seated avatars) and at 1.6 m
  (full-size), plus the lying views (≈0.4 m) in A1 beds and mats. [in-house] [INFERENCE]

### 5.10 Interior composition at greybox
- Each common room: ≥1 alcove, ≥1 window place, ≥1 half-open separation.
- ≥3 ceiling heights ≥0.4 m apart in a home; ceilings >4.3 m get an alcove or gallery for refuge.
- Partitions between same-noise zones ≤0.9–1.1 m, glass or open rails; a plain handrail beat a full wall between a games room and the stair void. [in-house]
- No slatted "cage" screens or pods; enclose with real walls to the ceiling. [in-house]
- Loose props stand against a wall or beside furniture, never alone mid-floor. Leave standing and walking space; clutter was rejected. [in-house]
- Key views show ≥3 depth planes: a foreground frame, the group, the view. [INFERENCE]
- Greybox signs off layout, scale, flow, sightlines and hierarchy only; don't penalize missing art. [INFERENCE]

### 5.11 Dimension table (metres)

Values are real-world sizes for a **1.6 m eye**. Apply §5.9: shell items and outdoor features ×k (k = eye_ref ÷ 1.6,
≈0.81 at the default 1.3 m eye), built-ins about ×0.9, loose furniture real size, and **never below the Min column** for
ceilings, clear height, door height and width, stair headroom and width, and primary path: collision does
not scale with the avatar. ‡ = approved at small-avatar scale; scale by eye_ref ÷ 1.2. [in-house] [user rule]

| Item | Min | Typical | Generous | Tag |
|---|---|---|---|---|
| Stair riser | 0.15 | 0.17–0.18 | 0.15–0.16 | |
| Stair going | 0.25 | 0.28–0.30 | 0.30–0.35 | |
| Stair width | 0.91 | 1.0–1.2 | 1.5–3.6 (feature) | [in-house] |
| Stair headroom | 2.0 | 2.1 | 2.4+ for tall avatars | [INFERENCE] |
| Ramp slope | — | ≤7° | ≤15° | [INFERENCE] |
| Level change (per §5.5) | 3 risers or a ramp | — | — | [user rule] |
| Door clear, private ‡ | 0.81 | 1.0–1.2 | — | [in-house] |
| Main portal between public rooms ‡ | — | 2.2–2.4 | never ≥4 (reads as a hole) | [in-house] |
| Door height | 2.1 | 2.4 | 3.0 | [INFERENCE] |
| Corridor, private-room front ‡ | 3.1 | 3.1–3.5 | junction hall 4.6 deep | [in-house] |
| Primary path | 2.0 | 2.4–3.0 | — | [INFERENCE] |
| Walkway between furniture | 0.76 | 0.91 | 1.2 | |
| Secondary walkway | 0.9 | — | — | [WORKSPACE RULE] |
| Table height (loose furniture, real size) | 0.72 | 0.72–0.76 | — | [WORKSPACE RULE] |
| Seat height (loose furniture, real size) | 0.42 | 0.42–0.46 | — | [WORKSPACE RULE] |
| Counter height (built-in: ≈0.82 at the default eye) | — | 0.90 | — | [WORKSPACE RULE] |
| Behind a seated diner | 0.81 | 0.91 | 1.12 (walk past) | |
| Bed clearance (open sides) | 0.76 | 0.91 | — | |
| Cuddle platform, 3–4 people | — | 2.4 × 2.4 | — | [INFERENCE] |
| Alcove | — | ≤1.83 × 0.9–1.8 | — | |
| Ceiling, nook / over bed | 1.8 | 2.1–2.3 | — | |
| Ceiling, small room | 2.1 | 2.4–2.7 | — | |
| Ceiling, public room | 3.0 | 3.0–3.7 | 4.5–7 double height | |
| Clear height over paths | 2.3 | — | — | [INFERENCE] |
| Slab edge (visual) | 0.2 | 0.25–0.35 | 0.4–0.6 | [INFERENCE] |
| Balcony / terrace depth | 1.8 | 2.4+ | — | |
| Wing width (daylight) | — | ≤7.6 | — | |
| Rail height | 1.0 | 1.1 | — | [INFERENCE] |
| Facing seats | — | ≤1.07 | 1.5–1.8 tolerated | |
| Seat neighbour spacing | 0.6 | 0.8–1.2 | — | [INFERENCE] |
| Conversation group Ø | 2.4 | 3.0 | 3.6 | [INFERENCE] |
| Bar stool pitch | 0.61 | 0.61–0.76 | — | |
| Cinema row pitch | — | ≈1.4 | — | |
| Prospect from seat | 6 | — | >30 | |
| Group spacing, one room | 6 | 8 | — | [INFERENCE] |
| Voice range | — | 25 | — | |
| Teleport island offset | 200 | 220 (cuddle grid) | inside 256 / 512 radius | [WORKSPACE RULE] [INFERENCE] |
| Runtime near clip, cuddle world | 0.001 | 0.001–0.01 | — | |

---

## 6. Clip planes, precision and world extent

Moved to `.omp/skills/clip-planes/SKILL.md` (section numbers there match the old §6.1–§6.7: facts, near/far/fog per
archetype, float precision and radii, teleport islands, distant scenery, z-fight separation, setup
checklist). The numbers plans must respect: cuddle zones < 256 m and any occupied space < 512 m from
the origin on every axis; teleport islands ≥200 m apart and inside those radii; runtime near
0.001–0.01 m in cuddle worlds.

---

## 7. Penthouse case study: lessons

From `case-studies/luxury-penthouse-layout.md`, a two-storey luxury residence (A2 home with A3 party floor
below and A1 suites as teleport islands). All [in-house].

1. **A single extruded rectangle is rejected** (a 40 × 40 m and a 25 × 25 m square both were). The accepted
   envelope had cut corners, push/pull volumes and an overhang, "not abstract art"; rooms stayed the same.
2. **Junctions make "ugly holes".** Fixed by running one clean 45° line corner to corner.
3. **Section beat footprint tricks.** What survived: a bridge over water, a wing on columns ending in a
   balcony, a raised roof with clerestory, a double-height stair arrival.
4. **Measured reference person.** 1.75 m assumed vs 1.2 m real avatars triggered a full remake: shell
   ×0.625, built-ins ×0.9, loose props ×1.0.
5. **Doors 1.0–2.4 m.** 3.1–4.6 m openings read as holes and collected furniture.
6. **Stairs settled at 3.6 m feature / 1.75 m secondary** after oscillating; 6 m wasted floor and made a
   24 × 5 m blank wall; 2.2 m stopped reading as the feature stair.
7. **Corridors are rooms:** 2.2 m failed; 3.1 m clear plus a furnished 4.6 m junction hall worked; sealed
   rooms were squashed first.
8. **Views end on something designed;** a "floating pier beside a dark hole" was rejected.
9. **No pits or decorative half-steps:** the sunken lounge and half-steps were ordered flat (see §5.5 for
   the one deliberate change now allowed per zone).
10. **Reachability is a hard gate:** "the chairs aren't really reachable" blocked sign-off.
11. **Program follows social exposure:** ground floor party, upper floor lived-in home; private rooms upstairs.
12. **Sealed fake rooms are fine** if their fronts read as real rooms: door bays 6.5–8.25 m, ≥4.75 m
    apparent depth, real doors and lock panels; suites as islands ≥200 m out.
13. **Preserve what was approved;** unsolicited reworks were reverted.
14. **Shotgun with cheap renders, one change-set per version; measure the live scene before redrawing.**
15. **Pitfalls that all occurred:** blank planes >15 m² on a main route; furniture straddling jambs;
    plants floating mid-floor; slatted screens reading as cages; floating ceiling rafts; outdoor stairs;
    an oversized gym; mirrored-copy suites.

---

## 8. Checklists

### 8.1 Architect self-check, per floor-plan variant (B.1)
- [ ] Archetype of every space named (A1–A5) with people per space; areas from §1.1 bands.
- [ ] Header line with all §1.3 axes; organizing idea named; signature space named.
- [ ] Intimacy gradient: entrance → public → semi-private → private; A1 rooms at the end, behind a turn or vestibule, or on islands.
- [ ] Reference eye height stated (default 1.3 m); shell and outdoor features ×eye ÷ 1.6, clamped at the collision minimums; props real size (§5.9). [in-house]
- [ ] Massing: 1 primary + 2–4 secondary + tertiary; primary ≥30% larger; each volume maps to program; ≥3 top heights; finished roof edges. [INFERENCE]
- [ ] Every cut ends on a corner; no dents or pockets; overhangs ≤1/3 backspan or visibly supported; nothing floats. [in-house]
- [ ] Section drawn: ceiling heights per archetype; ≤1 deliberate level change per social zone, ≥3 risers or ramp, none on the entrance → main-area path. [user rule]
- [ ] Seat groups at edges, sociopetal, reachable; every room has a focal point; light pools planned.
- [ ] Openings sized by role; private-room corridor ≥3.1 m; every view ends on something designed. [in-house]
- [ ] Acoustic order: A1 ≥25 m from A3/A4 or audio zone.
- [ ] World extent: occupied space < 512 m, cuddle zones < 256 m, islands placed per clip-planes §4; near/far/fog and backdrop plan per clip-planes §2 and §5. [INFERENCE]
- [ ] Plan rendered as an image with doors drawn. [in-house]

### 8.2 Greybox (B.2) and playability (C.2) checklist
**B.2 greybox** (not playable: no colliders, spawn, stair ramps, teleport doors or clip planes yet):
- [ ] Walls built from the plan JSON; live scene measured before any redraw. [in-house]
- [ ] Floors, interior walls and exterior walls in three neutral tones; reference-person capsules in every room. [in-house]
- [ ] Labelled, true-to-size low-poly placeholders for the big furniture only (couches, beds and cuddle platforms, tables, wardrobes and storage, bar, screen or stage, big rugs as slabs) in every pocket; no small props or wall decoration; placement per §5.1–§5.3, §5.11. [in-house]
- [ ] Placeholder transforms exported from the scene to the plan JSON `furniture` list. [in-house]
- [ ] World size limits planned: the greybox bounds, spawn and island positions satisfy clip-planes §7 items 3–4; near/far/fog and backdrop plan per clip-planes §2 and §5. [in-house, measured] [INFERENCE]
- [ ] Clearance ≥2.3 m over paths. [INFERENCE]
- [ ] One neutral baked-light rig, no realtime lights; ≤3M visible triangles from every main viewpoint. [WORKSPACE RULE]

**C.2 playability** (once the real objects exist):
- [ ] Collision: blocking walls, floors, large solid masses and one ramp per stair flight only; primitive auto-colliders removed from props. [WORKSPACE RULE]
- [ ] Solid colliders: every big table, counter, cabinet, wardrobe, bookcase and appliance-sized piece has a child `SolidCollider` (one always-on BoxCollider, floor to top surface); chairs, stools, couches and coffee/side/bedside tables have none. [WORKSPACE RULE]
- [ ] Lie-down colliders: every bed, couch and lie-on piece has a top-surface child `LieDownCollider` (one non-trigger BoxCollider), disabled by default; one world toggle switches them all. [WORKSPACE RULE]
- [ ] No void covered by a hidden ceiling collider. [in-house]
- [ ] Spawn checks pass (§5.7). [INFERENCE]
- [ ] Reference Camera assigned; runtime near/far script in place; clip-planes §7 items 1–7 pass with the real reach box. [in-house, measured] [INFERENCE]
- [ ] Walked in play mode with gravity and collision, every teleport door both ways, the lie-down toggle on and off. [in-house]

### 8.3 Reviewer protocol (shots and data) [INFERENCE] unless tagged
**Required shots**
1. Silhouette: 4 elevations + 2 three-quarter views, black on white.
2. Exterior three-quarter views of every volume junction (dent and hole check). [in-house]
3. Top-down orthographic per floor, ceilings hidden, rooms labelled with archetype, doors drawn.
4. Two sections: through the signature space and through the main route; one through each A1 bed or nook.
5. Reference eye height (WORLD.md, default 1.3 m), FOV ≈100°: spawn view; the entry threshold facing the
   release; each corridor end; each seat group looking out.
6. Seated from one seat per group (≈1.0 m at the default eye, 1.1–1.2 m for a 1.6 m eye); lying view
   (≈0.4 m) from each A1 bed or mat.
7. Spawn view and one group view repeated at 0.9 m (very small or seated) and 1.6 m (full-size) eye height.
8. Overhang and ceiling-underside shots (floating raft check). [in-house]
9. From the farthest cuddle spot: the view out of the window and the horizon (backdrop parallax, fog, cut). [in-house, measured]

**Required scene data**
- Room bounds w × d × h and archetype per room; m² per person; opening widths; corridor widths; ceiling Y clusters; roof-top clusters; adjacency list with gradient depth from spawn.
- Seat groups: centre, yaw error, spacing, distance to the nearest edge; group-to-group distances; audio ranges vs A1 rooms; any mirror outside a bathroom/gym/dance/dressing room (finding).
- Floor levels per social zone (count deliberate changes; flag half-steps and any change on the entrance → main path). [user rule]
- Downward rays under every volume; overhang length ÷ backspan.
- Collider audit: none on small props; always-on `SolidCollider`s on big furniture; disabled `LieDownCollider`s on lie-on furniture; no MeshColliders on walkable surfaces; one ramp per stair flight. [WORKSPACE RULE]
- World extent: reach box max per-axis |coord|; island bounds; Reference Camera near/far; runtime near/far script; fog mode and density; sightline D vs f_req; skybox backdrop depicted distances. [clip-planes §2, §7]

**Severity**
- **Blocker:** single-box massing; dents or holes at junctions; floating structure; decorative half-step or
  a level change on the entrance → main path; opening ≥4 m; private-room corridor under its scaled §5.11 value
  (3.1 m at the default); any scaled height or width below its collision minimum (§5.9); unreachable seats;
  A1 room on a through-route or within 25 m of a loud room with no audio zone; spawn into a wall or crowd;
  mirrored-copy rooms; out-of-program rooms; cuddle zone ≥256 m or occupied space ≥512 m from the origin;
  island outside the radii; fog not hiding the far cut; dimensions off the scaled §5.11 value by >25%. [in-house] [user rule] [INFERENCE]
- **Major:** >1 deliberate level change in one social zone; no loop through common rooms; path through a
  seat group; groups in the room centre; no focal point; one acoustic space; <3 ceiling or top heights;
  view ending on nothing; backdrop closer than r/θ; terrace <1.8 m. [INFERENCE] [in-house]
- **Minor:** missing alcove or window place; material change mid-plane; weak tertiary detail; room proportions outside 1:1–1:2.5. [INFERENCE]
- Reject any shot from a camera position no person can occupy. User-reported failures override earlier passing checks. [in-house]

Sources: ../SOURCES.md (not needed to use this guide).

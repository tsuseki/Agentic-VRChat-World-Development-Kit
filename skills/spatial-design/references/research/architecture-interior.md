# Architecture & interior design knowledge base for `world-architect` / `layout-reviewer`

Scope: real-world architecture and interior design only, turned into rules for placing walls, rooms, volumes and furniture in Unity (1 unit = 1 m). Each item gives a number, a pass/fail check, and **Verify:** (how a reviewer checks it from screenshots or scene data).

**Citation convention.** Every claim carries a bracketed key that resolves to an entry in `## Sources` at the end, e.g. `[APL 190]`, `[Ching 2015]`, `[Terrapin 2014]`.
- `[INFERENCE]` = my own reasoning or extrapolation. No source states it.
- Imperial source values are converted to metres (1 ft = 0.305 m, 1 in = 25.4 mm). The conversion is mine; the value is the source's.
- `APL nnn` keys: I read the per-pattern summary pages on patternlanguage.cc (Problem / Solution / related patterns), not the 1977 book itself.

Known failure case: a past luxury-residence world ([case study](../case-studies/luxury-penthouse-layout.md)) was first one square box and it was bad. Its second version combines several volumes and works. Sections 1 and 2 explain why, with checks.

---

## 0. Ten rules for the architect (summary; each rule is sourced in the section it points to)

1. **Use more than one volume.** Build the main mass plus 2–4 secondary masses plus small tertiary pieces. Never use one extruded rectangle (§1, §2).
2. **Vary the section.** Use at least 3 ceiling heights, at least 1 floor-level change, and at least 1 tall or double-height space (§3.3).
3. **Order rooms public → private** along the path from the entrance (§3.1).
4. **Make the entrance a sequence:** approach → transition → compressed entry → release. Change at least 3 of light, level, direction, surface and view (§3.2).
5. **Build prospect + refuge pairs.** Back and overhead covered, facing a view of at least 6 m (§3.5).
6. **Give each main room light from two sides,** with a window place, alcoves, and pools of light rather than uniform light (§3.4, §3.6).
7. **Keep circulation short, room-like and looped.** Paths run along the edges of seating groups, never through them (§3.7).
8. **Size everything from the dimension table** (§5).
9. **Make structure read as supported.** Nothing floats (§2.6).
10. **Pass the silhouette, plan, section, arrival and seated tests** (§8).

`[INFERENCE]` The list itself is my synthesis.

---

## 1. Why plain rectangular boxes fail

A single rectangle with one ceiling height, one floor level, windows on one wall and the door mid-wall breaks most of the patterns below at once.

| # | Failure in a box | What breaks | Key |
|---|---|---|---|
| 1 | One ceiling height | "A building in which ceiling heights are all the same is virtually incapable of making people feel comfortable." | [APL 190] |
| 2 | One homogeneous room | "No homogeneous room, of homogeneous height, can serve a group of people well." People need to be alone in ones and twos inside the shared space. | [APL 179] |
| 3 | Uniform light | Uniform illumination "destroys the social nature of space, and makes people feel disoriented and unbounded." | [APL 252]; [APL 135] ("places which make effective settings are defined by light") |
| 4 | Windows on one wall | People "leave the rooms which are lit only from one side unused and empty." | [APL 159] |
| 5 | Fully open or fully closed | Too closed blocks the flow of social life. Too open "will not support the differentiation of events which social life requires." | [APL 193] |
| 6 | One continuous monolith | An undifferentiated mass reads as one oversized object with no human scale. Articulating it (material change, distinct corners, smaller parts) breaks it into people-sized pieces. | [Ching 2015] "Articulation"; `[INFERENCE]` |
| 7 | Large plan, low ceiling | Height affects scale more than width or length. A 12×16 ft (3.7×4.9 m) room with a 9 ft (2.7 m) ceiling "might feel comfortable". A 50×50 ft (15×15 m) space with the same ceiling "would begin to feel oppressive." | [Ching 2015] "Human Scale" |
| 8 | No hierarchy | Real differences in size, shape or placement are needed so that some spaces read as more important. "Hierarchy depends on local contrast and context." | [Ching 2015] "Hierarchy" |
| 9 | Everything visible from the door | No mystery. Terrapin's mystery condition: "at least one edge of the focal subject is obscured, preferably two." | [Terrapin 2014] |
| 10 | Door straight into the room | Houses with a graceful transition between street and inside "are more tranquil than those which open directly off the street." | [APL 112] |
| 11 | Leftover space around the box | Outdoor spaces "merely 'left over' between buildings will, in general, not be used." | [APL 106] |
| 12 | Thin flat walls | Walls of smooth panels "always stay impersonal and dead". Walls can be thick enough to hold usable space. | [APL 197] |
| 13 | Exterior edge is only a line | Treat the edge "as a 'thing', a 'place', a zone with volume to it, not a line or interface which has no thickness." | [APL 160] |

**The rectangle itself is not the problem.** Alexander recommends each indoor space be "a rough rectangle, with roughly straight walls, near right angles in the corners" [APL 191]. The failure is a single undifferentiated volume: uniform section, uniform light, no edges, no sequence. Fix it by composing several rectangles of different heights and roles, not by adding random curves or angles `[INFERENCE]`.

**Box symptoms in a greybox `[INFERENCE]`:**
- The whole interior is visible from the entrance.
- All ceiling renderers share one Y value.
- The floor is a single plane.
- All walls are co-planar with the bounding box.
- The silhouette from every side is a rectangle.
- The furniture is pushed to the walls with an empty centre.
- No space reads as "the important one".

---

## 2. Massing: composing a building from several volumes

User priority: the building must look good and be plausible. It does not need to be structurally or seismically real. A good building combines several shapes into one composition.

### 2.1 Vocabulary (sourced)

- **Massing** is the overall arrangement of a building's volumes. `[INFERENCE]` It should follow the building's program: each major volume houses a recognisable part of the plan.
- **Dimensional transformation:** a form can change one or more dimensions "and still retain its identity as a member of a family of forms" (cube → planar → linear) [Ching 2015].
- **Subtractive form:** regular forms with portions removed still keep their identity "if we perceive them as incomplete wholes". "Spatial volumes may be subtracted from a form to create recessed entrances, positive courtyard spaces, or window openings" [Ching 2015].
- **Additive form:** "relating or physically attaching one or more subordinate forms to its volume" [Ching 2015]. Le Corbusier, as quoted in Ching, calls additive "cumulative composition" "picturesque; full of movement; can be completely disciplined by classification and hierarchy" [Ching 2015].
- **Four ways to join forms** [Ching 2015]:
  - *Spatial tension:* proximity or a shared visual trait.
  - *Edge-to-edge contact.*
  - *Face-to-face contact.*
  - *Interlocking volumes:* the forms "interpenetrate each other's space".
- **Organizations of form** [Ching 2015]:
  - Centralized: "secondary forms clustered about a dominant, central parent-form".
  - Linear.
  - Radial.
  - Clustered.
  - Grid.
- **Articulation** [Ching 2015] can be achieved by "differentiating adjoining planes with a change in material, color, texture, or pattern" or by "developing corners as distinct linear elements". `[INFERENCE]` Articulated parts sized for people make a large building feel smaller.
- **Hierarchy:** Ching lists hierarchy by size, shape and placement [Ching 2015]. `[INFERENCE]` The biggest, most distinctive mass reads as the most important.
- **Contrast levers for a focal mass:** size/height, shape and placement [Ching 2015]. `[INFERENCE]` Orientation is a further lever: one volume angled off the surrounding grid stands out.
- **Readability `[INFERENCE]`:** a building reads clearly when relatively simple volumes form a few distinct groups. Over-broken massing reads as visual noise ("camouflage") with no whole.

### 2.2 Primary / secondary / tertiary hierarchy (actionable)

| Tier | Role | Share of built volume | Count (house / penthouse) | Examples |
|---|---|---|---|---|
| Primary | Main program, tallest or most distinctive | 40–60% | 1 | Double-height great room, hall, tower |
| Secondary | Supporting wings or blocks | 10–25% each | 2–4 | Bedroom wing, kitchen/dining block, stair/elevator core |
| Tertiary | Human-scale accents | <5% each | 4–12 | Bay windows, entrance canopy, chimney, balcony, roof pavilion, planter walls |

`[INFERENCE]` The tier split applies Ching's hierarchy principle [Ching 2015] to building massing. The percentages and counts are my working heuristic, not from any source.

**Volumes per footprint `[INFERENCE]`:**

| Footprint | Primary | Secondary | Tertiary |
|---|---|---|---|
| ≤150 m² | 1 | 1–2 | 3–5 |
| 150–500 m² | 1 | 2–4 | 5–10 |
| >500 m² | 1 | 4–6, grouped into wings | ≥10 |

Never two "equal primaries": if two masses are within ±15% in volume and height, change one `[INFERENCE]`.

### 2.3 Numeric articulation rules from a real design code [DiamondBar ODS]

- **Horizontal articulation:** step part of the façade forward or back by **≥6 ft (1.8 m)** over **≥25 ft (7.6 m)**.
- **Vertical articulation:** step the height up or down by **≥4 ft (1.2 m)** over **≥25 ft**.
- **Projections:** at least one projection (balconies, bay windows, cantilevered rooms, eaves, awnings) **≥2 ft (0.6 m) deep**.
- **Recessions:**
  - Porches, covered passages and balconies recessed **≥6 ft (1.8 m)**.
  - Windows recessed **≥5 in (0.13 m)**.
  - Recessions at **50 ft (15 m)** intervals.
- **Base / middle / top:**
  - Base 10–35% of height.
  - Middle 50–87%.
  - Top 3–10%, which must be less than the base.
  - The top is marked with a cornice, colour or material change.
- **Limits:**
  - Balconies project ≤8 ft (2.4 m) and are ≥6 ft deep.
  - Projecting spaces ≤67% of the façade length they attach to.
  - Covered passages: clear height 2–3× their width.
  - Longer façades must use more articulation techniques.
- **Roof edge:** defined with a parapet, cornice or overhang.

`[INFERENCE]` Translation for greybox:
- A straight unbroken wall run over ~8 m reads as "box".
- The smallest articulation that registers at a distance is about 0.6 m in plan or 1.2 m in height.
- Steps of 0.1–0.3 m read as modelling errors.

### 2.4 Rooflines, heights, setbacks

- **Height cascade.** By the stage of Ceiling Height Variety, each floor is "a cascade of heights, typically highest in the middle where the largest rooms are, lower toward the edge where the small rooms are" [APL 191]. Cascade of Roofs: "place small rooms at the outside and ends of wings, and large rooms in the middle" [APL 116]. The roofline should step down outward from the primary.
- **Setbacks and terraces.** Any balcony, porch, gallery or terrace must be "at least six feet deep", partly recessed and partly enclosed [APL 167]. `[INFERENCE]` For a penthouse, set the top volume back ≥1.8 m from the parapet so the setback is a usable terrace.
- **Finished roof edge:** use a parapet, cornice or overhang [DiamondBar ODS]. `[INFERENCE]` A flat top with no edge treatment reads as unfinished.
- **Height count `[INFERENCE]`:** at least 3 distinct roof or parapet elevations ≥1.2 m apart for a footprint over 150 m². The 1.2 m step comes from [DiamondBar ODS].

### 2.5 Material change per volume

- Ching's articulation by material change [Ching 2015] supports giving each secondary volume a different material from the primary, so the dominant mass contrasts in material as well as shape.
- `[INFERENCE]` Limits:
  - ≤3 façade materials plus 1 accent.
  - Change material only at volume joints or setbacks, never mid-plane.
  - Heavier-looking materials at the base or primary; lighter materials (glass, timber, panels) on upper and cantilevered volumes. This is consistent with [DiamondBar ODS] base distinctness.

### 2.6 Plausibility, not engineering

| Rule | Number | Key |
|---|---|---|
| Cantilever vs backspan | "Cantilevers are typically 1/3 the length of the backspan. Longer cantilevers require deeper, heavier structure" | [AISC 2023] |
| Beam depth | ≈ ½ in per ft of span, i.e. **span/24** (9 m span → ≈0.38 m deep) | [AISC 2023] |
| Truss depth | Rectangular 1–1.5 in/ft (span/12–span/8). Triangular or arched 3–4 in/ft. Space truss 1 in/ft | [AISC 2023] |
| Typical spans | Steel beams 25–45 ft (7.6–13.7 m) at 10–15 ft spacing. Girders 20–40 ft (6–12 m). Trusses 40–300 ft | [AISC 2023] |
| Efficient bay | Proportion 1:1.25–1.5, area 750–1,250 ft² (≈70–115 m²), e.g. ≈8×10 m or 9×12 m | [AISC 2023] |
| Wood floor cantilever | "Floor cantilever spans shall not exceed the nominal depth of the wood floor joist" (with table exceptions) | [IRC 2024 R502.3.3] |
| Perception | Cantilevers make buildings "appear both heavy and light at the same time" and present "safely precarious situations" | [ArchDaily 2021] |
| Risk/peril as a positive | "An identifiable threat coupled with a reliable safeguard". Example: Wright's Taliesin "Birdwalk", a narrow cantilevered balcony | [Terrapin 2014] |

**Plausibility checklist `[INFERENCE]`, derived from the rules above:**
1. Every upper mass sits on a wall, column, core or lower mass, OR cantilevers ≤1/3 of its supported length, with the backspan visibly anchored in a bigger mass [AISC 2023].
2. Slab and roof edges have thickness: slabs ≥0.25–0.35 m, fascias 0.3–0.6 m. Long spans show a deeper edge (≈span/24, [AISC 2023]). A 0.05 m slab spanning 10 m reads as paper.
3. Columns ≥0.25–0.5 m on a 6–12 m grid. Columns align with the walls and mass edges above.
4. Glass does not visibly hold up stone. A fully glazed storey under a solid mass needs visible columns or a deep transfer beam.
5. Nothing floats: no gaps >0.02 m at bearings, and stairs connect landing to landing.
6. Heavy at the bottom and lighter on top, echoing the base/middle/top rule [DiamondBar ODS].
7. Long overhangs show one consistent support language: deep fascia, brackets or struts, tie-rods, or tip columns.
8. Pools and roof gardens sit over the primary mass or the column grid, not on cantilevers.

### 2.7 Silhouette and readability tests for greybox screenshots

- **Silhouette test.** Character designers "use a silhouette to test whether the character's basic design 'reads' to the audience" [WDFM 2020]. `[INFERENCE]` Adaptation to buildings:
  - Render 4 elevations plus 2 three-quarter views flat black on white.
  - **Pass:** ≥3 distinct top heights, ≥1 recess or notch, ≥1 projection, and an obvious dominant mass.
  - **Fail:** any outline fills >90% of its bounding rectangle, or the concept is indistinguishable from the others at 128 px wide.
- **Readability test `[INFERENCE]`, from §2.1 readability:**
  - The primary is identifiable within 2 s.
  - More than 8 "equal" pieces = fragmented ("camouflage").
- **From scene data `[INFERENCE]`:**
  - Count top-level greybox volumes and bucket them by footprint × height into the tiers of §2.2.
  - Cluster roof `renderer.bounds.max.y` to 0.5 m and count clusters (≥3).
  - Cluster interior ceiling Y values the same way (≥3).

### 2.8 Massing pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Single box | Rectangular silhouette from all sides, one roof height | §2.2 tiers `[INFERENCE]`; additive massing [Ching 2015] |
| Equal-weight blocks | No dominant mass | Contrast by size, shape or placement [Ching 2015] |
| Over-fragmentation | "Camouflage", no readable whole `[INFERENCE]` | Merge into fewer masses and keep detail tertiary `[INFERENCE]` |
| Wedding cake | Identical setbacks every floor | Vary setback depth and side `[INFERENCE]` |
| Random rotation | Several arbitrarily rotated volumes | Rotate only the focal mass, with a reason `[INFERENCE]` |
| Floating cantilever | Overhang >1/3 of backspan, thin slab | §2.6 [AISC 2023] |
| Material soup | Change mid-plane, >4 materials | Change at joints [Ching 2015] + `[INFERENCE]` limit |
| Decorative-only volumes | Outside masses don't match inside rooms | Massing follows program `[INFERENCE]` |

---

## 3. Planning principles (interior layout)

### 3.1 Zoning and intimacy gradient

- Lay out spaces as "a sequence which begins with the entrance and the most public parts of the building, then leads into the slightly more private areas, and finally to the most private domains" [APL 127].
- Place bathing rooms and toilets "half-way between the common areas and the private ones" [APL 127].
- A single common area at "the center of gravity of all the spaces the group occupied", with the paths in and out tangent to it [APL 129].
- The couple's realm is "a distinctly separate realm" from the common areas and children's rooms [APL 136].
- Graded sitting spaces [APL 142]:
  - The most formal ones fully enclosed.
  - The least formal ones in corners of other rooms.
  - Intermediate ones partly enclosed.
- `[INFERENCE]` Luxury residential zones:
  - Arrival: lobby → foyer.
  - Public: great room, dining, bar, terrace.
  - Semi-private: family/media, kitchen, study.
  - Private: suites.
  - Service: back-of-house.
- **Verify `[INFERENCE]`:** in the room/door graph, depth from the entrance rises with privacy. Private rooms are at depth ≥3. No bedroom opens off the foyer.

### 3.2 Entrance, approach and compression–release

- **Approach** [Ching 2015]:
  - *Frontal:* "leads directly to the entrance … along a straight, axial path".
  - *Oblique:* "enhances the effect of perspective"; "the path can be redirected one or more times to delay and prolong the sequence".
  - *Spiral:* "prolongs the sequence"; the entrance may be "viewed intermittently … or … hidden until the point of arrival".
- **Entrances** [Ching 2015]:
  - *Flush:* "can be, if desired, deliberately obscured".
  - *Projected:* "forms a transitional space, announces its function … and provides overhead shelter".
  - *Recessed:* "provides shelter and receives a portion of exterior space".
  - A threshold can be an implied plane, "two pillars or an overhead beam", or "even a change in level".
- **Entrance transition:** mark it "with a change of light, a change of sound, a change of direction, a change of surface, a change of level … and above all with a change of view" [APL 112]. Check: ≥3 of these change between the approach and the door `[INFERENCE]`.
- **Entrance room:** "a light-filled room which marks the entrance and straddles the boundary between indoors and outdoors" [APL 130].
- **Main entrance:** visible "immediately from the main avenues of approach", with "a bold, visible shape" [APL 110].
- **Compression and release:** Wright's "compression-and-release style … where a low entryway led to a room with high ceilings" [AD-FLW]. At the Gordon House, a low entry opens into a living room "with its 12 foot ceilings" (3.7 m) [CraftsmanBungalow].
  - `[INFERENCE]` Numbers: entry 2.2–2.4 m, then ≥3.3 m or double height (5–7 m). The compressed zone is 2–5 m long.
- **Zen View:** put view windows "at places of transition — along paths, in hallways, in entry ways, on stairs". The view is "never visible from the places where people stay" [APL 134].
  - `[INFERENCE]` This conflicts with the penthouse wall-of-glass habit. Resolve it by screening the foyer and framing a slot of the view, then revealing it fully in the great room.
- **Verify `[INFERENCE]`:**
  - The main view is ≤30% visible from the entrance.
  - The entry ceiling is ≥1 m lower than the main room ceiling.

### 3.3 Section: ceiling heights and level changes

- **Ceiling heights** [APL 190]:
  - Public or large gatherings: **10–12 ft (3.0–3.7 m)**.
  - Smaller gatherings: **7–9 ft (2.1–2.7 m)**.
  - One or two people: **6–7 ft (1.8–2.1 m)**.
  - Vary heights "especially between rooms which open into each other".
  - Highest ceilings on the ground floor, lowest on the top floor.
- **Height and scale** [Ching 2015]: height "has a greater effect on its scale than either its width or length". Raising a 12×16 ft room's ceiling by 1 ft is more noticeable than widening it by 1 ft.
- **Proportional height** [Ching 2015], Renaissance theories: "the height of a room is equal to the mean … between the two extremes of the width … and length". Japanese ken: ceiling height in shaku = number of mats × 0.3.
- **Refuge ceilings** [Terrapin 2014]: indoor refuge spaces have "lowered ceiling conditions", "approximately 18–24 inches [0.45–0.6 m] below the main ceiling". For ceilings ">14 feet" (4.3 m), "freestanding or vegetative alcoves and mezzanine-like structures are often effective".
- **Level changes** [Ching 2015], elevated base plane. Continuity depends on the scale of the change:
  1. Edge well-defined, visual and spatial continuity maintained, easy access.
  2. Visual continuity maintained, spatial continuity interrupted, stairs or ramps needed.
  3. Visual and spatial continuity interrupted.
  - If the floor surface continues across the edge, the raised field stays part of the surroundings. An articulated edge (form, colour, texture) makes it "a plateau that is separate and distinct".
  - `[INFERENCE]` Metres: (1) 0.15–0.5 m, (2) 0.5–1.4 m, (3) >1.6 m (above eye level).
- **Verify `[INFERENCE]`:**
  - ≥3 ceiling clusters ≥0.4 m apart.
  - ≥1 floor change of ≥0.3 m in the public zone.
  - ≥1 space ≥4.5 m tall in luxury typologies.

### 3.4 Light: two sides, pools, tapestry, depth

- **Two-sided light:** give each room outdoor space on ≥2 sides with windows, "so that natural light falls into every room from more than one direction" [APL 159]. Wings "never more than 25 feet wide" (7.6 m) [APL 107].
- **Daylight depth:** light "penetrates into a room roughly 2.5 times the height of the top of the window" [Autodesk]. The "rule of 2.5" assumes side-lighting can serve depths up to about 2.5× window height [Mansy 2017]. `[INFERENCE]` With a 2.4 m head, about 6 m is daylit; deeper plans need a second source.
- **Tapestry of light and dark:** alternate light and dark so "people naturally walk toward the light, whenever they are going to important places" [APL 135].
- **Pools of light:** "Place the lights low, and apart". "You can't have pools of light without the darker places in between" [APL 252].
- **Window area:** ≥25% of floor area (Bay Area figure), with views "out over life" [APL 192].
- **Deep reveals:** frame "about a foot wide and splayed at about 50 to 60 degrees" [APL 223].
- **Verify `[INFERENCE]`:**
  - Each primary room has openings in ≥2 exterior walls.
  - Depth ≤2.5× head height, or a second source.
  - A lit-screenshot luminance check shows separated pools.

### 3.5 Prospect and refuge (with evidence caveats)

- **Origin:** prospect-refuge theory was proposed by Appleton (1975) for landscapes and applied to architecture by Hildebrand (1991) for Wright's houses. Hildebrand added mystery, complexity, enticement and illumination [D&O 2016]. Appleton and Hildebrand are known here only through this paper.
- **Evidence** (34 quantitative studies) [D&O 2016]:
  - "Urban and interior studies supported the significance of prospect, and were more neutral about refuge."
  - In interiors, 10 of the 19 studies considering prospect confirmed it.
  - "A degree of complexity in interior space is preferred, but … unclear about how much or where."
  - "Results for mystery are less emphatic with the majority being neutral or contrary."
  - `[INFERENCE]` Treat prospect as reliable, and refuge and mystery as heuristics.
- **Terrapin numbers** [Terrapin 2014]:
  - *Prospect:* focal lengths ≥20 ft (6 m). Distant prospect >100 ft (30 m) is preferred. Partition heights ≤42 in (1.07 m).
  - *Refuge:* "protected from behind and overhead".
  - *Mystery:* depth of field ≥20 ft, ideally ≥100 ft; ≥1 obscured edge, preferably 2; "peek-a-boo windows", "curving edges", "winding paths". An obscured view with a shallow depth of field "has shown to lead to unpleasant surprises".
- **Placement `[INFERENCE]`:**
  - Every seating group has its back to a wall, alcove or low ceiling and faces ≥6 m of view.
  - Never seat in a path, and never with the back to the door.
- **Verify `[INFERENCE]`:** from the seated eye point (~1.2 m), raycast forward ≥6 m, check for an obstruction within 1.5 m behind, and a ceiling lower than the room max or an alcove overhead.

### 3.6 Edges: alcoves, window places, thick and half-open walls

- **Alcoves:** "no more than 6 feet wide and 3 to 6 feet deep" (≤1.8 × 0.9–1.8 m), large enough for two to sit or for a table [APL 179].
- **Window place:** in every room where people spend time, make at least one window "into a 'window place'": window seats, bay windows, low sills with chairs [APL 180].
- **Thick walls:** walls "can occupy a substantial volume — even actual usable space" [APL 197].
- **Half-open walls:** "no one room entirely enclosed; and no space totally connected to another". Use columns, half-open walls, indoor windows, sliding doors and low sills [APL 193].
- **Interior windows:** glazed fixed windows between rooms that "tend to be dead" or are unusually dark [APL 194].
- **Susanka:** framed openings, spatial layering, visual weight, diagonal views and ceiling-height variation make a house "feel comfortable and more spacious", with "separation and shelteredness yet interconnection" [Wiki-Susanka].
- **Verify `[INFERENCE]`:** each common room has ≥1 alcove, ≥1 window place, ≥1 partial separation, and ≥1 diagonal view longer than its longest side.

### 3.7 Circulation

- **Path configurations** [Ching 2015]: linear, radial, spiral, grid, network, composite.
- **Path–space relationships** [Ching 2015]:
  - *Pass by:* "the integrity of each space is maintained".
  - *Pass through:* "axially, obliquely, or along its edge", creating "patterns of rest and movement".
  - *Terminate in:* for "functionally or symbolically important spaces".
- **Circulation form** [Ching 2015]:
  - Enclosed, open on one side (balcony or gallery), or open on both sides (colonnade).
  - "A distinction in scale should be established between a public promenade, a more private hall, and a service corridor."
  - "Sections of a path can be widened" for pausing.
- **Flow through rooms:** "avoid the use of corridors". Chain common rooms "to form a chain, or loop", with private rooms off them, and give it "great generosity" [APL 131].
- **Short passages:** "long, sterile corridors set the scene for everything bad about modern architecture". Keep passages short and room-like, ideally with windows along a whole wall [APL 132].
- **Corner doors:** "except in very large rooms, a door only rarely makes sense in the middle of a wall". With two doors, keep both at one end [APL 196].
- **Sitting circle:** seating "not cut by paths or movement", roughly circular, with "a few too many" chairs [APL 185].
- **Staircase as a stage:** the main stair is "central and visible", treated as a room, with a flared bottom of wide steps [APL 133].
- **Enfilade:** doors "aligned … along a single axis, providing a vista through successive rooms". In Baroque palaces, access ran public → intimate by rank. The National Gallery's longest enfilade "traverses fifteen rooms" [Wiki-Enfilade].
  - `[INFERENCE]` Use 3–5 aligned doorways, with the axis offset from seating groups.
- **Verify `[INFERENCE]`:**
  - Circulation ≤20–25% of floor area.
  - No corridor >10 m without a window, widening or turn.
  - ≥1 loop in the public zone.
  - No shortest door-to-door path intersects seating bounds.

### 3.8 Spatial relationships and organizations

- **Relationships** [Ching 2015]:
  - *Space within a space:* "a clear differentiation in size is necessary".
  - *Interlocking:* "the field of a space may overlap the volume of another space".
  - *Adjacent.*
  - *Linked by a common space.*
- **Organizations** [Ching 2015]:

| Type | Description | Use for `[INFERENCE]` |
|---|---|---|
| Centralized | "A central, dominant space about which a number of secondary spaces are grouped"; "stable, concentrated" | Hubs, atrium houses, clubs |
| Linear | "A linear sequence of repetitive spaces"; "each space along the sequence has an exterior exposure" | Wings, galleries, enfilades |
| Radial | Central space with linear arms; "an extroverted plan that reaches out to its context" | Multi-view hubs |
| Clustered | "Spaces grouped by proximity or the sharing of a common visual trait"; accepts dissimilar spaces | Pavilions, villages |
| Grid | "Organized within the field of a structural grid" | Modular kits |

- `[INFERENCE]` In the shotgun stage, each concept should differ in organization type, approach type and primary-mass shape.

### 3.9 Proportion

- **Palladio's seven room shapes** [Ching 2015]: circle, square, 1:√2, 3:4, 2:3, 3:5, 1:2.
- **Villa Foscari:** a 16×16 ft square room sits between 12×16 and 16×24 ft rooms, ratios "3:4, 4:4, and 4:6" (passage quoted in [Ching 2015]).
- **Golden section:** "the lesser of the two is to the greater as the greater is to the sum of both" (≈1:1.618) [Ching 2015].
- `[INFERENCE]` Keep room plans between 1:1 and 1:2.5 unless the room is a declared gallery, which needs a pause point every 5–8 m.

### 3.10 Outdoor rooms, terraces, edges

- **Six-foot balcony:** balconies "less than six feet deep are hardly ever used". Make them ≥1.8 m, partly recessed and partly enclosed [APL 167].
- **Outdoor room:** "so much enclosure round it, that it takes on the feeling of a room". Define the corners with columns, add a partial trellis or canopy roof, and walls of fences, sitting walls or screens [APL 163].
- **Positive outdoor space:** give each outdoor space "some degree of enclosure" so it "does not spill out indefinitely around corners" [APL 106].
- **Connection to the earth:** use paths, terraces and steps around the edge so the boundary is "ambiguous" [APL 168].
- **Building edge:** "crenelate the edge of buildings with places that invite people to stop" [APL 160].
- **Verify `[INFERENCE]`:** terraces ≥1.8 m deep in the usable zone. Each outdoor room enclosed on ≥2 sides plus corner or overhead definition.

---

## 4. Interior design principles (furnishing, focal points, layering)

- **Principle set:** balance, harmony, rhythm, emphasis (focal point), contrast, proportion and scale, functionality, details, variety, movement [DesignFiles].
- **Focal point `[INFERENCE]`:** one primary focal point per room (fireplace, view, art wall, stair, bar). Seating orients to it. Place it opposite or diagonal to the main entry.
- **Conversation distance:** keep face-to-face seating "no more than 8 feet apart" (2.4 m) [BHG].
- **Hall's distances**, as summarized by [Hall 1966 via CReducation]:
  - Intimate 0–18 in (0–0.45 m).
  - Personal 18 in–4 ft (0.45–1.2 m), "interaction of good friends".
  - Social 4–12 ft (1.2–3.7 m), for "casual friends and acquaintances".
  - Public 12–25 ft (3.7–7.6 m).
  - `[INFERENCE]` A conversation group is 2.4–3.6 m across. Larger rooms get several groups.
- **Float furniture `[INFERENCE]`:** in rooms >5 m wide, pull seating into floating groups with circulation around them. The sitting circle should be "protected, not cut by paths" [APL 185].
- **Layering:** "spatial layering" and "framed openings" [Wiki-Susanka]; pools of light [APL 252]. `[INFERENCE]` Key views show ≥3 depth planes: frame, group, view.
- **Sightlines:** keep a clear open trajectory from seats to another space; ≥6 m prospect from seats [Terrapin 2014]. Diagonal views [Wiki-Susanka].
- **Verify `[INFERENCE]`:** seat forward vectors converge on the focal object within 30°. Distances match §5. Paths between groups ≥0.9 m.

---

## 5. Dimension table (metres)

Neufert's *Architects' Data* was **not** accessed. The values below come from the cited codes, guidelines and pattern pages.

| Item | Minimum | Comfortable / typical | Generous / luxury | Key |
|---|---|---|---|---|
| Stair rise | 0.15 (UK private min) | 0.17–0.18 `[INFERENCE]` | 0.15–0.16 grand `[INFERENCE]` | Max 0.196 [IRC 2021 R311.7.5.1]; UK private 0.15–0.22 [ADK] |
| Stair going / tread | 0.22 (UK), 0.254 (IRC) | 0.28–0.30 `[INFERENCE]` | 0.30–0.35 `[INFERENCE]` | [ADK]; [InterNACHI] |
| Stair rule | 2R+G 0.55–0.70 | ≈0.62–0.64 `[INFERENCE]` | — | [ADK] |
| Stair pitch | — | 30–37° `[INFERENCE]` | ≤30° `[INFERENCE]` | UK private max 42° [ADK] |
| Stair width | 0.914 | 1.0–1.2 `[INFERENCE]` | 1.5–2.5; "wide, shallow steps can serve as an invitation" [Ching 2015] | [WhiteBearLake] (IRC R311.7) |
| Stair headroom | 2.0 | 2.1 `[INFERENCE]` | — | [ADK] |
| Ceiling: 1–2 people | 1.8 | 2.1 | — | [APL 190] |
| Ceiling: small rooms | 2.1 | 2.4–2.7 | — | [APL 190] |
| Ceiling: public rooms | 3.0 | 3.0–3.7 | 6.1 double-height great room; 3.05 standard | [APL 190]; [Monad 2019] |
| Refuge soffit drop | 0.45 | 0.45–0.6 | alcove or mezzanine if main >4.3 | [Terrapin 2014] |
| Hall / gallery width | 0.9 `[INFERENCE]` | 1.2 `[INFERENCE]` | 1.8 (Monad gallery 25×6 ft) | [Monad 2019] |
| Door clear opening | 0.81 (32 in) | 0.85–0.9 `[INFERENCE]` | 1.2+ `[INFERENCE]` | [IVO-NKBA] |
| Door height | 2.0 `[INFERENCE]` | 2.1 `[INFERENCE]` | 2.4–3.0 `[INFERENCE]` | — |
| Main walkway | 0.76 (secondary) | 0.91 (36 in) | 1.2 `[INFERENCE]` | [VBU]; [Willis] |
| Sofa → coffee table | 0.36 | 0.36–0.46 (14–18 in) | — | [Willis] |
| Face-to-face seating | — | ≤2.4 | — | [BHG] |
| Proxemic zones | intimate 0–0.45 | personal 0.45–1.2; social 1.2–3.7 | public 3.7–7.6 | [Hall 1966 via CReducation] |
| Conversation group diameter | 2.4 | 3.0 | 3.6, then split | `[INFERENCE]` from [BHG] + [Hall 1966 via CReducation] |
| Kitchen work aisle | 1.07 (one cook) | 1.22 (two cooks) | — | [LilyAnn] (citing NKBA) |
| Kitchen walkway | 0.91 | — | — | [LilyAnn] |
| Clearance behind seating | 0.81 / 0.91 / 1.12 (by traffic type) | — | — | [LilyAnn] |
| Work triangle | each leg 1.2–2.7 | — | sum ≤7.9 | [NKBA 2022] |
| Alcove | — | ≤1.8 wide × 0.9–1.8 deep | — | [APL 179] |
| Balcony / terrace depth | 1.8 | — | Monad roof deck up to 41×11 m | [APL 167]; [Monad 2019] |
| Wing width (daylight) | — | ≤7.6 | — | [APL 107] |
| Daylit depth | — | ≈2.5× window head height | — | [Autodesk]; [Mansy 2017] |
| Window area | — | ≥25% of floor area | — | [APL 192] |
| Window reveal | — | ≈0.3 wide, splayed 50–60° | — | [APL 223] |
| Prospect sightline | 6 | — | >30 preferred | [Terrapin 2014] |
| Prospect-preserving partition | — | ≤1.07 | — | [Terrapin 2014] |
| Beam depth | — | span/24 | — | [AISC 2023] |
| Cantilever | — | ≤1/3 backspan | longer needs deeper structure | [AISC 2023] |
| Column bay | — | 70–115 m², 1:1.25–1.5 | — | [AISC 2023] |
| Slab thickness (visual) | 0.2 | 0.25–0.35 | 0.4–0.6 at long spans | `[INFERENCE]` from [AISC 2023] depth ratios |
| Façade step to articulate | 0.6 projection | 1.8 plan / 1.2 height over 7.6 run | — | [DiamondBar ODS] |
| Level change: continuous / semi / separate | 0.15–0.5 / 0.5–1.4 / >1.6 | — | — | Categories [Ching 2015]; metres `[INFERENCE]` |

**VR note `[INFERENCE]`:** VRChat is 1:1 scale, so these numbers apply directly. Widen social circulation by about 1.2–1.5× where avatars crowd (doors ≥1.2 m, main paths ≥1.5 m). Don't scale ceilings up uniformly; variety matters more than height.

---

## 6. Residential luxury conventions

### 6.1 Penthouse

Monad Terrace by Ateliers Jean Nouvel, Miami Beach [Monad 2019]:
- Duplex PHA: 452 m² interior plus **460 m² exterior**.
- Arrival: **private elevator**, foyer 6′0″×21′9″ (1.8×6.6 m), gallery 25′0″×6′0″ (7.6×1.8 m).
- **Double-height great room 44′0″×24′8″ (13.4×7.5 m) with 20 ft (6.1 m) ceiling**. Standard ceilings are 10 ft (3.05 m).
- Floor-to-ceiling sliding doors.
- Master suite: study, bedroom, dressing room 20′9″×11′0″, master bath. The upper level is "open to below".
- 140 ft (43 m) garden terrace. Private rooftop with lap pool and hot tub, reached by a stair "through a glass pavilion".
- Unit PHB: elevator lobby 20′0″×8′0″ (6.1×2.4 m), media room 23′6″×11′0″, master terrace 15′0″×24′0″, roof deck "up to 116′ × 68′".

Other precedents:
- Four Seasons Doha Royal Suite: a "two-level penthouse" with a "double-height living room" [FourSeasons].
- Foster + Partners VELA: penthouses "split over two levels with generous double-height spaces, private pools, and incredible bay windows" [Archello-VELA].

Conventions `[INFERENCE]`, generalized from the above plus [APL 127], [APL 133], [APL 134]:
1. **Arrival:** elevator → compressed lobby → foyer or gallery with the view screened → double-height great room with the panorama.
2. **Zoning:** public zone (great room, dining, kitchen, bar, terrace). Bedrooms in a wing or upper level reached past the public zone, not through it. Master suite at the end of the gradient. Powder room near the foyer.
3. **Primary volume:** the double-height great room, 5–7 m tall, with a mezzanine overlooking it. The stair as a stage.
4. **Terraces:** wrap ≥2 sides, each ≥1.8 m deep, with ≥1 outdoor room. The top volume is set back.
5. **Roof pavilion:** a small glazed tertiary volume at the roof stair.
6. **Views:** 2–4 exposures framed by piers and reveals.
7. **Service:** clustered by the elevator core on the non-view side. The core is a secondary mass.

### 6.2 Mansion / villa

- **Enfilade** of formal rooms with a processional vista, growing more private along the axis [Wiki-Enfilade].
- **Palladian proportioning:** simple-ratio room suites around a central hall [Ching 2015].
- **Approach:** oblique or spiral, then a projected or recessed entrance [Ching 2015]. Monad lists a porte-cochère [Monad 2019].
- **Grand stair:** "A stairway leading up to a second-story balcony or loft can give us an idea of the vertical dimension of a room as well as suggest a human presence" [Ching 2015].
- **Courtyard** through subtractive form: "positive courtyard spaces" [Ching 2015]. Terraces stepping to the garden [APL 168].
- `[INFERENCE]` Zones (formal, family, private, service, guest) each map to one secondary mass, so massing and plan coincide.

---

## 7. Pitfalls catalogue (with symptoms)

| Pitfall | Symptom | Fix / key |
|---|---|---|
| Single box | §1 symptoms | §2; [Ching 2015]; [APL 190] |
| Uniform ceiling | Same ceiling plane in every shot | [APL 190]; [Terrapin 2014] |
| Flat floor | No steps except the stair | Base-plane changes [Ching 2015] |
| Door mid-wall | Path cuts a small room in half | [APL 196] |
| Path through seating | Route crosses the sofa group | [APL 129]; [APL 185] |
| Long sterile corridor | >10 m, windowless | [APL 131]; [APL 132] |
| All visible from entry | The whole floor is visible from the front door | [APL 134]; [Terrapin 2014] mystery |
| No entrance transition | Door → giant room directly | [APL 112]; [APL 130]; [AD-FLW] |
| Private by front door | Bedroom visible from the foyer | [APL 127] |
| One-sided light | Dark back half of rooms | [APL 159]; [APL 194]; [Autodesk] |
| Uniform lighting | Flat luminance | [APL 252]; [APL 135] |
| Furniture on walls | Empty middle | [APL 185]; [BHG] |
| Thin balconies | <1.8 m ledges | [APL 167] |
| Leftover exterior | Unshaped strip around the box | [APL 106]; [APL 163] |
| Paper-thin glass box | No piers, no reveals | [APL 197]; [APL 223] |
| Over-scaled low room | 15×15 m at 2.7 m feels oppressive | [Ching 2015] |
| Implausible structure | Floating slabs, cantilever > backspan | §2.6; [AISC 2023] |
| Over-fragmented façade | Camouflage, no hierarchy | §2.1 `[INFERENCE]`; [Ching 2015] |
| Non-divergent concepts | Same box at different sizes | §3.8 `[INFERENCE]` |

---

## 8. Checklists

### 8.1 Architect self-check before handing over a greybox

The thresholds below are `[INFERENCE]` unless keyed in the sections they reference.

**Massing (§2)**
- [ ] 1 primary + 2–4 secondary + ≥5 tertiary volumes. The primary is ≥30% bigger or taller than any secondary.
- [ ] ≥3 top heights ≥1.2 m apart; the roofline cascades outward [APL 116].
- [ ] No unbroken façade run >~8 m [DiamondBar ODS].
- [ ] Each volume maps to a program zone and has its own material; ≤3 materials + accent.
- [ ] Overhangs ≤1/3 of backspan or visibly supported [AISC 2023]. Slabs ≥0.25 m. Nothing floats.

**Plan (§3.1, §3.7)**
- [ ] Graph depth rises with privacy [APL 127].
- [ ] Common area at the heart, with paths tangent to it [APL 129].
- [ ] ≥1 loop [APL 131]. No corridor >10 m.
- [ ] Doors near corners [APL 196].
- [ ] Room plans 1:1–1:2.5.

**Section (§3.3)**
- [ ] ≥3 ceiling heights [APL 190].
- [ ] ≥1 level change ≥0.3 m.
- [ ] Entry ≥1 m lower than the main room.

**Sequence (§3.2)**
- [ ] The approach turns [Ching 2015].
- [ ] ≥3 transition changes [APL 112].
- [ ] The view is screened at the entry [APL 134].

**Edges (§3.4–3.6, §3.10)**
- [ ] Each primary room has two-sided light [APL 159], ≥1 alcove [APL 179], ≥1 window place [APL 180], and a half-open separation [APL 193].
- [ ] Seats have refuge plus ≥6 m prospect [Terrapin 2014].
- [ ] Terraces ≥1.8 m [APL 167] with an outdoor room [APL 163].

**Dimensions (§5)**
- [ ] Stairs within [ADK] / [IRC 2021 R311.7.5.1] limits.
- [ ] Doors ≥0.81 m clear [IVO-NKBA].
- [ ] Walkways ≥0.91 m [Willis].
- [ ] Conversation ≤2.4 m [BHG].
- [ ] Kitchen aisle ≥1.07 m [LilyAnn].

### 8.2 Layout-reviewer protocol (screenshots + scene data) `[INFERENCE]` procedure; thresholds keyed above

1. **Silhouette:** 4 elevations + 2 three-quarter views in black-on-white. Fail on a near-rectangle outline (>90% fill) or no identifiable primary within 2 s. Count top heights (≥3). Method adapted from [WDFM 2020].
2. **Plan:** orthographic top view with ceilings hidden.
   - Trace the intimacy gradient [APL 127].
   - Find the loop [APL 131].
   - Test paths against seating bounds [APL 185].
   - Name the organization type [Ching 2015].
3. **Section:** 2 sections through the primary space. Count ceiling heights [APL 190] and level changes [Ching 2015]. Check compression before release [AD-FLW] and slab thickness [AISC 2023].
4. **Arrival:** eye-level shot at the entrance (the WORLD.md reference eye height, default 1.2 m; also 1.6 m for full-size) plus 3 steps forward. The main view is partly hidden [Terrapin 2014], there is a visible goal, and the transition changes are observable [APL 112].
5. **Seated:** first-person shot from each main seat (~1.2 m eye height for a full-size avatar, ~0.9 m at the 1.2 m default). Back covered, ≥6 m view [Terrapin 2014], focal point in view.
6. **Plausibility:** for each overhang, compare length to backspan [AISC 2023]. Raycast down from each volume's bounds for floating gaps.
7. **Dimensions:** sample 10 dimensions against §5. More than 2 out of range = NEEDS WORK.
8. **Divergence (shotgun stage):** concepts must differ in organization, approach, primary shape and section idea.

### 8.3 Severity guide `[INFERENCE]`

- **Blocker:**
  - Single-box massing.
  - One ceiling height.
  - No entrance sequence.
  - Private rooms on the front door.
  - Floating or implausible structure visible from main viewpoints.
  - Stair, door or corridor dimensions off by >25%.
- **Major:**
  - No loop.
  - Path through seating.
  - One-sided light.
  - <3 top heights.
  - Terraces <1.8 m.
  - No focal point.
- **Minor:**
  - Missing alcoves or window places.
  - Material changes mid-plane.
  - Weak tertiary detail.
  - Room proportions outside 1:1–1:2.5.

---

## Sources

Source keys in this file resolve in [SOURCES.md](../../SOURCES.md).

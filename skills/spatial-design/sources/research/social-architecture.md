# Social architecture: designing VRChat worlds as places people live in and gather

Scope: real-world architecture, interior design, hospitality design and urban public-life research, turned into rules for VRChat worlds where **residents, guests and visitors** spend time together. These worlds are homes, bedrooms, lounges, bars, clubs, cinemas and gardens. Units are metres (1 Unity unit = 1 m).

**How to use this file.** Find out which **space archetypes** (§0) the world contains, then read the matching sections (decision table, §8). Shared rules (§1) carry tags that say which archetypes they apply to: `[A1]` intimate retreat, `[A2]` social home, `[A3]` gathering venue, `[A4]` audience space, `[A5]` scenic / walk-and-talk.

**Citation convention.** Every claim carries a source key from `## Sources`.
- `[INFERENCE]` means my own derivation or recommendation. It is a tunable default, not a sourced fact.
- `[X, citing Y]` means I read X, which reports Y. I did not read Y itself.
- Imperial values are the sources' own; the metric conversions are mine.
- Gehl page numbers are the printed pages as recovered from PDF text extraction. Page markers at spread boundaries are ambiguous, so treat them as ±1 page.

**Relation to sibling files.** Some topics are already covered and are not repeated here:
- `architecture-interior.md`: ceiling-height bands [APL 190], refuge soffits, Ching's three kinds of level change, the master dimension table, and penthouse precedents.
- `social-vr.md`: VRChat platform facts, VR proxemics, cluster spacing and capacity. Wherever this file quotes VRChat behaviour, it cites [AWDK social-vr].

---

## 0. The archetypes

| # | Archetype | People | Typical rooms | Design traditions that apply |
|---|---|---|---|---|
| A1 | **Intimate retreat** (primary case, ~90 % of worlds) | 2–8 | bedroom, nook, cozy apartment, cuddle or lying space | residential bedroom and living room; Alexander alcove, bed alcove and window place; hospitality booth |
| A2 | **Social home / hangout** | 8–20 | house, penthouse or lounge with several rooms and conversation groups | residential planning (Alexander, Susanka, luxury plans) |
| A3 | **Gathering venue** | 20–80+ | bar, club, party floor, lounge hall | Gehl, Whyte, bar, lounge, club and restaurant design, occupancy per m² |
| A4 | **Audience space** | any size, everyone faces one focus | cinema, stage, talk or event | cinema sightline and seating standards |
| A5 | **Scenic / walk-and-talk** | small groups on the move | garden, park, promenade, nature | Gehl and Whyte on edges and walking; biophilic patterns |

**Why these five.** I kept the five proposed archetypes because the sources split along the same lines.
- Gehl separates necessary, optional and social activities, and treats walking, standing and sitting as different activities with different conditions [Gehl 2011]. Walking is A5; sitting splits by group size into A1 to A3.
- Alexander grades sitting spaces from fully enclosed to open corners along the intimacy gradient [APL 142]. That gradient is the A1 ↔ A2 ↔ A3 axis.
- Cinema standards are about orientation and sightlines, not group size [UNIC 2020]. So A4 is its own axis, independent of headcount.

One refinement `[INFERENCE]`: A1 has two forms.
- **A1-standalone**: a whole world that is a bedroom or apartment.
- **A1-nested**: an alcove, booth or side room inside an A2 or A3 world.

Both use the A1 rules. The nested form also needs the threshold rules in §7.

---

## 1. Shared principles (each tagged)

### 1.1 Edges, backs and refuge — `[A1][A2][A3][A5]`
- **Edge effect.** People choose to stay "along the facades in a space or in the transitional zone between one space and the next, where it is possible to view both spaces at the same time." Open areas fill only after the edges are taken [Gehl 2011 p. 149, citing de Jonge]. With a protected back, others "can approach only frontally" [Gehl 2011 p. 149].
- **Indoors too.** In restaurants, hotel lobbies and "the first stages of a party", guests place themselves along the walls or near furniture [Gehl 2011 p. 153].
- **Restaurants.** Seats with the back or side to a wall and a view of the room are preferred. Window seats are preferred most. Guests "refuse categorically" mid-room tables when a wall seat is free [Gehl 2011 p. 157, citing de Jonge].
- **Refuge** means protection "overhead and to one's back, preferably on three sides." Its light level should differ from the adjacent space. A "high backed booth" is the textbook example [Terrapin 2014 P12].
- **Supports.** People choose recesses, corners, columns and bollards to stand by. "Good cities for staying out in have irregular facades and a variety of supports" [Gehl 2011 pp. 151–153].
- **Pitfall:** free-floating seat groups in the middle of a big floor. They "look interesting on architectural drawings but are definitely less inviting" [Gehl 2011 p. 156].
- **Verify:** at least 70 % of seats have a wall, rail, high back or plant within 1 m behind them `[INFERENCE]`.

### 1.2 Sociopetal seating geometry — `[A1][A2][A3]`
- Osmond and Sommer's work at Weyburn hospital set out to find the arrangements "that would increase social interaction and those which could increase privacy" [Sommer 1983].
- **Corners beat face-to-face and side-by-side.** Interactions observed at cafeteria tables, by seating position [Sommer 1959]:
  - corner-to-corner: 30 (18.5 expected by chance)
  - side-by-side: 16 (18.5 expected)
  - face-to-face: 5 (13.9 expected)
- **Pairs choose corners.** Pairs asked to talk chose corner seats in most trials (e.g. 8 of 10 and 8 of 9), and groups of three chose corners 9 of 11 times [Sommer 1959].
- **Comfortable conversation distance.** People sat on facing couches up to **3.5 ft (1.07 m)** apart. Beyond that they moved side by side onto one couch. With chairs, they sat across unless the gap exceeded 3.5 ft, or was larger than the side-by-side gap [West 1972, citing Sommer 1961, 1962].
  - A replication in rooms of different sizes found the switch at 5 ft (1.5 m) in larger rooms and 6 ft (1.8 m) in a small room. Room size was not statistically significant [West 1972].
- **Angled benches.** Benches at an angle make it "a bit easier to start a conversation" and easier to leave it. Erskine put benches "two and two, placed at right angles around a table" [Gehl 2011 p. 170].
- **Field evidence.** In a 7×6 m care-home lounge, conversation was seen in 54–66 % of observation intervals with chairs in small facing groups, and in ≤10 % with chairs around the walls [Sharp 2019].
- **Pitfall:** sofas in a row facing a screen or wall (sociofugal), or chairs lining the room's perimeter.
- **Verify:** each group has at least one pair of seats at about 90° (an L or U), and facing seat fronts are no more than 1.1–1.8 m apart `[INFERENCE]` from [West 1972].

### 1.3 Enough seats, of varied kinds — `[A2][A3][A5]`
- "People tend to sit where there are places to sit." Usage correlated most strongly with **sittable space**, not with open area [PPS 2025].
- Whyte's numbers [Whyte 1980 via Han 2012]:
  - People sit on anything 1–3 ft (0.3–0.9 m) high.
  - Ledges two backsides deep (30 in, 0.76 m) seat more people.
  - Target 1 linear ft of seating per 30 ft² of plaza (≈1 m of seat edge per 9 m², my conversion).
  - Movable chairs give people choice.
- **Primary and secondary seating.** Use a modest number of benches and chairs plus many steps, low walls and ledges. "Steps are especially popular" as lookouts. Rows of empty chairs give "the depressing impression that the place has been rejected" [Gehl 2011 p. 161].
- **Never identical chairs.** Mix big and small, soft and hard [APL 251]. A sitting circle needs "a few too many" chairs [APL 185].
- **Verify:** at least 2 seat types in every A2, A3 or A5 space, and secondary ledges make up at least 30 % of the seat edge `[INFERENCE]`.

### 1.4 Something to share: triangulation and third places — `[A2][A3][A5]`
- **Triangulation.** An outside stimulus, such as a performer, sculpture or event, gets strangers talking to each other [Whyte 1980 via Han 2012 p. 94; Gehl 2011 p. 169].
- **Self-congestion.** "What attracts people most … is other people." People held conversations in the middle of the pedestrian flow, not off to the side [Whyte 1980 via Han 2012; PPS-Whyte].
- **Oldenburg's third place** has these traits [PPS-Oldenburg]:
  - neutral ground that levels status
  - conversation as the main activity
  - a playful mood
  - strangers welcome, plus a core of regulars
  - warmth and belonging like a good home
- **Verify:** every A2/A3 room has a shared focus within view of most seats: fire, bar, view, music or game `[INFERENCE]`.

### 1.5 Light: pools, periphery, warmth — all archetypes
- **Pools of light.** Place lights "low, and apart", in pools around chairs and tables: "you can't have pools of light without the darker places in between" [APL 252]. Light and surface colours should be warm [APL 250].
- **Flynn's lighting studies.** Pleasantness tracked the peripheral and non-uniform ends of the scales (r = .92). In a coffee bar, people chose seats in darker areas but faced toward the light. Wall-washing raised spaciousness [Collins 1993, citing Flynn 1973, 1977].
  - **Caveat:** keep the centre of a room lit when clarity matters. Dark centres read as "less clear and distinct" [Collins 1993, citing Flynn 1977].
- **Dim light and intimacy.** A controlled study found no effect of light level (40 vs 372 lux) on self-disclosure and urges caution about the older claim [Mehta 2017]. The older studies found that dim light was *rated* more intimate [Mehta 2017, citing Carr & Dabbs 1974]. Use dimness for mood, not as a promise of intimacy.
- **Glare.** Keep adjacent luminance ratios below about 40:1 [Terrapin 2014 P6].
- **Verify:** the luminance histogram of a seated screenshot shows distinct pools with darker gaps, and no surface is more than 40× brighter than its neighbour.

### 1.6 Sound and voice — all archetypes
- **Real-world thresholds.** Ordinary conversation is nearly impossible above about 60 dB of background noise. Hearing the soft sounds of a social scene needs 45–50 dB [Gehl 2011 p. 167].
- **VRChat thresholds.**
  - Voice is audible to **25 m** by default, and walls do not block it natively [AWDK social-vr].
  - Rule `[INFERENCE]`: any two spaces closer than 25 m are acoustically one room unless an audio zone or occlusion tool separates them.
- **Verify:** for each A1 retreat, the distance to the nearest A3 or A4 source is at least 25 m, or an audio zone covers it.

### 1.7 Level changes: use sparingly — all archetypes
**Rule:** at most one deliberate floor-level change per social zone. Make each one ≥3 risers, or a ramp. Edge it with a contrasting tread, a rail or a ceiling change. Never put a level change on the main path between the entrance and the hub, or between a retreat and the bathroom/exit `[INFERENCE]`, from the evidence below.

**Evidence against overuse:**
- "One of the most prevalent stair accident scenarios involves tripping over or stepping past 1 and 2-riser stairs." 1-riser stairs had "the highest rate of accidents per tread." The guideline is to accentuate any 1–2 steps at a "sunken living room, raised platform, or porch" with rails, light, finish or a ceiling change [NBS 1979 §2.5.6].
- People avoid level changes. 83 % took a 50 m detour rather than 7 % using a stepped tunnel. In houses "generally the lowest floor is used most" [Gehl 2011 pp. 142–143].
- "Activities that one wishes to assemble" should not be stacked on levels. Functions 50–100 m apart along a street relate better than functions 3 m above or below each other [Gehl 2011 p. 99]. Keep indoor and outdoor floors at the same level so that it is "easy for events to flow in and out" [Gehl 2011 p. 187].
- "Unless there is a compelling reason, an open space should never be sunk … sunken plazas are dead spaces" [Gehl 2011 p. 97, citing Whyte].
- Conversation pits were controversial as a tripping hazard from the start. A 1963 piece noted that "the charms of climbing out of and falling into a pit soon wore thin." Many were covered over by the late 1970s, and built-ins cannot be rearranged [AD 2024].
- A designer filled in a 3–4 in sunken room that was "just enough to trip you up". Family members routed through an office to avoid stepping down and back up [Aston 2016].
- Accessibility law treats >½ in (13 mm) as a level change that needs a ramp [ADA 2010 §303].

**Evidence for using them:**
- "Just a step or two's height change can create a significant distinction between places, yet someone in the higher space can still converse easily with another in the lower space" [Susanka Houzz-Level].
- Platforms raised 2–3 steps give overview in Italian squares [Gehl 2011 p. 164].
- A raised bandstand frames dancing [APL 63].

**VR note `[INFERENCE]`:** colliders are ramps under kit rules, so tripping is gone. Avatar head-height jumps, broken sightlines between seated groups and furniture placement problems all remain.

**Verify:** count floor heights per social zone (target ≤2). Every level edge has a contrast or rail. The path from spawn to hub stays on one level.

### 1.8 Clearance table (metres) — tagged

| Item | Value | Applies | Key |
|---|---|---|---|
| Clearance around a king bed (1.93 × 2.03) | min 0.76, comfortable 0.91, on 3 sides | A1 | [Dim-King] |
| Bedroom with a king bed | ≥ 11 m²; 13.1–13.7 m² with closets | A1 | [Dim-King] |
| Facing seats (comfortable talk) | ≤ 1.07 front to front (1.5–1.8 tolerated) | A1 A2 | [West 1972] |
| Behind a seated diner | 0.81 with no traffic; 0.91 to edge past; 1.12 to walk past | A1 A2 A3 | [NKBA 2022] |
| Counter seat width | 0.61 per person (knee depth 0.46 / 0.38 / 0.30 at 30 / 36 / 42 in high) | A2 A3 | [NKBA 2022] |
| Rug to wall | ≈ 0.45 gap; sofa front legs on the rug, ⅓ tucked under | A1 A2 | [HB 2026] |
| Bar stool pitch | 0.61–0.76 | A3 | [Dim-Bar] |
| Behind bar stools | 0.76–0.91 circulation; public zone 1.22–1.52 | A3 | [Dim-Bar] |
| Between chair backs at adjacent tables | 0.46; service aisle 0.91 | A3 | [Cabaret-Seating] |
| Parallel tables for two | ≥ 0.30 apart (35 % still felt crowded at 0.61) | A3 | [Robson 2011] |
| Alcove | ≤ 1.83 wide × 0.9–1.8 deep | A1 A2 A3 | [APL 179] |
| Cinema seat / row | width 0.50–0.75 (shared arms); row pitch ≈ 1.40 | A4 | [UNIC 2020] |
| Screen viewing | 30° field (≈1.6 × diagonal) or 40° (≈1.2 × diagonal) | A1 A2 A4 | [Wiki-HDTV] |

**Verify:** measure the clearances in scene data (renderer bounds of the bed, sofa, table and bar against the walls and each other) and compare them with the table.

---

## 2. A1 Intimate retreat (2–8 people)

**Character.** Shelter, softness, closeness, a view out, and a sense of being away from everyone else. Alexander places the room of one's own, alcoves and bed alcoves at the far, private end of the intimacy gradient [APL 127, APL 141, APL 188].

**People and area.**
- A king bedroom for 2 is 11–13.7 m², about 5.5–7 m² per person [Dim-King].
- `[INFERENCE]` Size A1 rooms at **4–8 m² per expected person**: a 4-person nook 16–25 m², an 8-person cozy lounge 35–50 m².
- Below about 3 m² per person VR users rate a room claustrophobic: 7 people at 2.8 m² felt "crowded" [AWDK social-vr, citing Williamson 2025].

**Room proportions and ceiling.**
- Ceilings for one or two people: 1.8–2.1 m; for small groups: 2.1–2.7 m [APL 190 via architecture-interior].
- Shelter the bed itself:
  - lower the ceiling over it to about 7′6″ (2.29 m) [Susanka Houzz-Shelter]
  - or use a canopy or four-poster, "slightly enclosed, with a low ceiling" [APL 187]
- Knee walls around 4 ft (1.22 m) under a sloped roof accentuate shelter [Susanka Houzz-Shelter].
- A dropped ceiling over the bed "creates a sense of shelter" [Susanka-Bungalow].

**Enclosure.**
- Alcoves off a room: at most 6 ft (1.83 m) wide and 3–6 ft (0.9–1.8 m) deep, "large enough for two people to sit, chat" [APL 179].
- Bed alcoves "so the bed itself becomes a tiny private haven" [APL 188].
- Communal sleeping is legitimate: one large mat in an alcove near the fire, plus bed alcoves for guests [APL 186].
- A refuge works best with three enclosed sides plus overhead cover [Terrapin 2014 P12].

**Lying and seating arrangements.**
- **Clearance.** Keep 0.76–0.91 m on the three open sides of a bed [Dim-King]. `[INFERENCE]` A cuddle bed or mattress platform for 3–4 people needs about 2.4 × 2.4 m, with one long side and the foot open.
- **Seats.** Corner and L arrangements beat facing rows [Sommer 1959]. Facing seats should be ≤1.07 m apart [West 1972]. The least formal sitting spaces go in corners [APL 142].
- **Window place.** Every room where people spend time gets one: a window seat, a bay, or a low sill with chairs [APL 180].
- **The fire.** Put it in a common space where every social space gets a glimpse of it, and give the room another focus for when it is out [APL 181].
- **Built-in seats.** Test the position with an old armchair before building [APL 202]. Built-ins save floor area and "give the room a cozy feel" [Susanka 2000].

**Light.**
- Use low pools, e.g. sconces "pointed both up, to bounce light off the ceiling, and down, to create warm pools of light for reading" [Susanka 2000].
- Refuge light should differ from the adjacent room's [Terrapin 2014 P12].
- A primary suite should have several lighting scenes (Ralston suggests four) [Ralston 2026].

**Sound.** Separate retreats by plan: keep the suite away from the kitchen, family room, mudroom and laundry, with closets and corridors as buffers [Ralston 2026]. In VR, walls do not block voice, so this means distance or audio zones (§1.6).

**Circulation.**
- A dead end is good here: put the retreat at the far end of the intimacy gradient [APL 127, APL 141].
- Arrive by a branch corridor that turns away from the main route, an entry vestibule that compresses the space, or a material or ceiling shift [Ralston 2026].
- Guests should not pass the suite entry [Ralston 2026].

**Feels right when:** the bed or sofa is sheltered, a view out exists, the light is warm and low, and nobody walks past.

**Pitfalls and symptoms.**

| Pitfall | Symptom | Key |
|---|---|---|
| Bed floating mid-room under a tall bare ceiling | Lots of floor area and volume, "very little sense of shelter" | [Susanka Houzz-Shelter] |
| Standard furniture pushed tight against the walls | "tends to suggest that a room is too small" | [Susanka 2000] |
| Oversized room | Over 10 m² per person; voices feel far apart; couples drift onto one couch | [West 1972]; [INFERENCE] |
| Retreat opens straight off the party floor | Party voices carry inside 25 m | [AWDK social-vr] |
| Door opens straight onto the bed | No arrival sequence or second threshold | [Ralston 2026]; [INFERENCE] |

**Verify:** a section through the bed shows a lower ceiling or canopy above it, the room area matches the people count, and there is no path through the room to anywhere else.

---

## 3. A2 Social home / hangout (8–20 people)

**Character.** A house with a heart. One common area where everyone ends up, rooms of different intimacy around it, and loops of movement.

**People and area.**
- `[AWDK social-vr]` gross social floor of **8–14 m² per expected person**.
- Common room precedent: 16 × 24 ft (4.9 × 7.3 m) with a 10 ft (3.05 m) ceiling combines kitchen, dining and living [Susanka 2000].
- Rule: "at least one area that gives a sense of spaciousness" [Susanka 2000].

**Planning rules.**
- **Common area at the heart.** One per social group, "at the center of gravity", with paths "tangent to it" [APL 129]. Food and fire anchor it [APL 129].
- **Farmhouse kitchen.** A big kitchen with a big table at the centre of the commons, and a single warm light over the table [APL 139, APL 182].
  - In open plans, islands, soffits, varied ceilings and stepped floors define the zones [Ralston-Open].
  - Seat island guests at 0.61 m each, with 0.91–1.12 m behind them where people pass [NKBA 2022].
- **Flow through rooms.** Avoid corridors. Chain or loop the common rooms, with the private rooms opening off them [APL 131].
- **Intimacy gradient.** Run entrance → common → private. Put bathrooms halfway along it [APL 127].
- **Couple's realm.** "Distinctly separate" from common rooms, with its own small sitting area [APL 136].
- **Room of one's own.** Anything from an alcove with a desk and a curtain up to a cottage, at the far end of the gradient [APL 141].
- **Sequence of sitting spaces.** Formal sitting fully enclosed. Intermediate sitting partly enclosed and connected. Informal sitting in corners [APL 142].
- **Susanka's Not So Big principles** [Susanka-Principles]:
  - Shelter Around Activity
  - Ceiling Height Variety (varied ceilings define activity places without walls [Susanka Houzz-Ceiling])
  - Interior Views (views lead you on to the next activity place [Susanka Houzz-Views])
  - Place of Your Own
  - Light to Walk Toward
- **Away room.** A small room to retreat to from the noise of the main living area, to read or watch TV; it doubles as a guest room [Susanka-Libertyville]. This is the A1-nested room inside A2.
- **Entry.** Make "a place to stand and catch a glimpse of the living space" [Susanka-Bungalow].
- **Open plan vs broken plan.**
  - Fully open plans are noisy, give nowhere to escape and lack personality [Homebuilding 2026].
  - Broken plan zones the space with shelving, glass partitions, half walls, double-sided fireplaces and "subtle floor level changes" [Homebuilding 2026].
  - Its downsides: clutter, partial divisions that still leak sound, and the cost of level changes [Homebuilding 2026].
  - Alexander's balance: "no one room entirely enclosed; and no space totally connected to another" [APL 193].
- **Luxury layout** [Ralston 2026]:
  - The primary suite sits away from the kitchen, family room and guest routes, with closets and corridors as buffers.
  - The bedroom is at least 16 × 18 ft (4.9 × 5.5 m). Proportion matters: a 14 × 28 ft room feels worse than 18 × 22 ft.
  - The full suite runs 800–1,500 ft² (74–139 m²).
  - The private terrace is enclosed on at least 2 sides.
- **Entry focal point.** A foyer needs a focal point and a "reveal sequence" into the house [Ralston-Entry].

**Seating.**
- Several groups of 3–6, each sociopetal (§1.2), each on its own rug [HB 2026].
- In open plans, use a separate rug per zone. Leave about 45 cm between rug and walls, and put at least the front legs of the sofa on it [HB 2026].

**Light.**
- Pools per group [APL 252].
- Daylight on 2 sides of each room [APL 159 via architecture-interior].

**Sound.** Separate the loud room (music, games) from the quiet groups by about 25 m or an audio zone [AWDK social-vr].

**Feels right when:** arriving guests glimpse the heart but not everything, gravitate to the kitchen or fire, and can slip away to a quieter room.

**Pitfalls.**

| Pitfall | Symptom | Key |
|---|---|---|
| One open box | No retreat, noise everywhere | [Homebuilding 2026]; [APL 193] |
| Corridor house | Long halls; rooms off them never used together | [APL 131] |
| Common area off to one side, cut by paths | People pass through it instead of settling | [APL 129]; [INFERENCE] |
| Bedrooms off the foyer | Guests see private rooms on arrival | [APL 127] |

**Verify:** the door graph has a central hub at depth 1–2 from the entrance, private rooms at depth ≥3, and at least one loop through the common rooms `[INFERENCE]`.

---

## 4. A3 Gathering venue (20–80+ people)

**Character.** Bustle, people-watching, a strong focus (bar, DJ, stage), and pockets where small groups can talk.

**Density.** Real-world codes give *maximum* densities for egress, not comfort targets:

| Space type | IBC factor (ft² / m² per person) | UK factor (m² per person) | Comfort / design figure |
|---|---|---|---|
| Standing / bar | 5 net / 0.46 | 0.3 (standing or bar) | — |
| Chairs only | 7 net / 0.65 | 0.5 (assembly without seating) | — |
| Tables and chairs | 15 net / 1.39 | 1.0 (dining) | Dining 15 ft² (1.4 m²) per person [Cabaret-Seating]; full-service 12–15 ft², fine dining 18–20 ft² (1.7–1.9 m²) per seat, banquet 10–11 ft² [NAFEM via RF.net] |
| Island bar area | — | — | 17 ft² (1.6 m²) per patron; shotgun/L bars ≥30 ft² (2.8 m²) [Cabaret-Capacity] |

Sources for the code columns: [IBC Table 1004.5 via WAC]; [NFRS 2025].

**VR translation.** VR users need much more room than real guests, so do not use code densities. Use **4–8 m² per expected person** on the floor of an A3 space, and never less than 4 m² at Maximum Capacity [AWDK social-vr]; the 4–8 band is `[INFERENCE]`.

**Size of the room.**
- Facial expressions read at 20–25 m; events read at 70–100 m [Gehl 2011 p. 163].
- About 25 m is "immediately comfortable" for a social space, and good city spaces seldom exceed 110 m [Gehl 2011 p. 163, citing Lynch].
- `[INFERENCE]` Keep each A3 room within about 25 m across. Every guest can then read faces across it, and it fits one voice radius.

**Ceiling.** Public rooms 3.0–3.7 m [APL 190 via architecture-interior]. Booths and alcoves under lower soffits give refuge [Terrapin 2014 P12].

**The bar.**
- **Stations.** Plan by bartender stations: 75–100 covers per station [Cabaret-Capacity].
- **Shapes.**
  - An island bar about 27 × 18 ft (8.2 × 5.5 m) seats 28 [Cabaret-Capacity].
  - Island bars need about 17 ft² (1.6 m²) per patron against ≥30 ft² (2.8 m²) for straight or L bars, so islands are the most space-efficient shape [Cabaret-Capacity].
- **Dimensions** [Dim-Bar]:
  - Stools 0.61–0.76 m apart.
  - 0.46–0.61 m customer zone at the bar.
  - 0.76–0.91 m circulation behind it.
  - Back bar 0.91–1.14 m high.
- **Back bar as focal point.** `[INFERENCE]` The back bar is the room's focal point. Light it brighter than the room, and give at least 60 % of seats a sightline to it.
- **Allocation.** Front of house is 60–70 % of the area. Bar and bar dining take about 43 % of front of house but hold about 60 % of the occupants [Cabaret-Plan].

**Booths vs loose seating.**
- Booths had the highest check per person ($14.21). Banquette tables had the lowest spend per minute and the longest stays (51.1 vs 46.7 min) [Kimes 2004].
- Guests object to close parallel tables [Robson 2011]:
  - 70 % would ask to be reseated at 6 in (0.15 m).
  - 35 % felt crowded even at 24 in (0.61 m).
  - Under 12 in (0.30 m) is "inadvisable".
  - Banquettes were disliked.
- Corner tables are preferred for formal occasions; window tables when dining with friends [Robson 2011].
- Lobby practice: booths "with walls that extend to the ceiling … invite guests to stay a little longer" [ShelbyWilliams 2013].

**Zoning loud vs quiet.**
- The zoned hotel lobby has on-the-go, quiet, social, dining, pay-to-meet and technology zones. In the quiet zone, "Loud music and low lights are out"; it uses lounge or wing-back chairs. The social zone uses communal tables at counter or bar height, so that sitters and standers meet at comfortable eye level. Guests feel "alone together" [ShelbyWilliams 2013].
- 42 % of hotel users go to work somewhere quiet; 82 % go to have fun [Gensler 2018].

**Clubs and parties.**
- The dancefloor should be larger than the other areas and separated from the bars, and the DJ booth should sit within the dancefloor. Wood helps the acoustics [Mixmag 2018 Muallem].
- Design "a space that everyone can flow through", with a narrative entry sequence building to the dancefloor. Avoid dark spots and hidden corners, for safety [Mixmag 2018 Geha].
- Long events need "safe spaces to rest and relax" [Mixmag 2018 Aldred].
- A beer hall has "perhaps a half-dozen activities, so that people are continually criss-crossing" [APL 90].

**Small group inside the venue (intermediate case).**
- Give it an edge seat, booth or alcove with a back, a view of the room, its own light pool and a lower soffit [Gehl 2011 p. 157; Terrapin 2014 P12; APL 179].
- `[INFERENCE]` Booth clusters at least 6 m from the dancefloor or speakers. Quiet lounges at least 25 m away, or behind an audio zone [AWDK social-vr].

**Edges and front.** Stops are seven times more frequent in front of active facades than passive ones [Gehl 2006]. `[INFERENCE]` Line the venue's perimeter with active edges: bar, booths, windows, displays.

**Feels right when:** the room is busy but not crushed, the bar or DJ is visible from most places, and booths, edges and a quieter side room exist.

**Pitfalls.**

| Pitfall | Symptom | Key |
|---|---|---|
| Hall too big | >30 m² per person; groups spread thin | [AWDK social-vr] |
| Benches spread "liberally, but randomly" | "only the manufacturers of benches … benefit" | [Gehl 2011 p. 156] |
| One acoustic space | Loud voices dominate; talkers leave | [AWDK social-vr] |
| Dancefloor mixed with bar queue | Collisions and crowding | [Mixmag 2018] |
| Hidden dark corners | Safety concerns | [Mixmag 2018] |

**Verify:** floor area ÷ capacity falls in 4–8 m², ≥40 % of seats are edge or booth seats `[INFERENCE]`, and the focal point is visible from ≥60 % of seats.

---

## 5. A4 Audience space (everyone faces one focus)

**Character.** Clear views for every seat, comfortable neck angles, and social seating at the back or sides for those who come to talk.

**Geometry** [UNIC 2020]:
- First row eye distance D1 ≥ 0.6 × picture width keeps the horizontal field of view under 80°, which is comfortable. The absolute limit is 90° (D1 ≥ 0.5 × W).
- Vertical angle from the first row's eye height (1.2 m) to the screen centre: **< 25°**.
- **Sightline clearance.** Rake each row so its eye line clears the head in front by a constant clearance c. Individual riser heights per row work best.
- To improve sightlines: raise the picture bottom, move row 1 back, increase stadium height, or use fewer rows.
- Each row needs "one deep step" from the aisle.
- Seats are 500–750 mm wide with shared arms and 650–900 mm with double arms or recliners. An example layout uses a 1,400 mm row distance.
- Walls from the first row to the screen should be black. Decorative wall lighting is fine elsewhere.
- Do not put wheelchair places in the first row.

**Home and small rooms.** Seat at 30° screen width (≈1.6 × diagonal) or THX 40° (≈1.2 × diagonal) [Wiki-HDTV].

**Stages in public space.** A slightly raised, covered bandstand with a paved dance surface around it [APL 63]. Raising viewers 2–3 steps gives overview [Gehl 2011 p. 164].

**VR evidence.** A static amphitheatre in a large VR event space was ignored [AWDK social-vr, citing Williamson 2021].

**Mixed use `[INFERENCE]`.** An A4 room in a social world should also work when nothing is playing. Use couches in sociopetal groups that can turn to the screen, plus a social bar or lounge at the back.

**Light.** Dim house light with a focus on the screen or stage. Black or dark surfaces near the screen [UNIC 2020].

**Sound `[INFERENCE]`.** Screen or stage audio Far = room length, so it does not spill into neighbouring retreats [AWDK social-vr].

**Pitfalls.**

| Pitfall | Symptom |
|---|---|
| Flat floor with many rows | Back rows see heads |
| Front row too close | Neck strain above 25° |
| Hall with nothing to do between events | Empty, dead room |
| Screen sound reaches the bedrooms | Retreats lose their quiet |

**Verify:** a side section shows each row's eye line clearing the row in front, the first-row vertical angle is under 25°, and the audio range stays inside the room.

---

## 6. A5 Scenic / walk-and-talk

**Character.** Companions talking "while they walk", stopping where they meet, and lingering at edges with a view [Gehl 2011 p. 168].

**Distances.**
- Acceptable walking distance is 400–500 m, but "experienced distance" matters as much: a straight, dull 500 m feels very long, while the same length feels short "if the route is perceived in stages" [Gehl 2011 pp. 136–137].
- A network of streets alternating with small squares means the trip "is subdivided naturally, in manageable stages" [Gehl 2011 p. 141].
- Benches every 100 m in towns [Gehl 2011 p. 162].
- `[INFERENCE]` VR walking is 2 m/s [AWDK social-vr], and VR worlds are smaller. Scale down: a stop (bench, view, water, pavilion) every 30–60 m, and a full loop of 150–400 m.

**Path width.**
- Small old-city streets, like indoor hallways, are "seldom wider than 1 meter". The upper limit for acceptable two-way density is 10–15 pedestrians per minute per metre of street width [Gehl 2011 p. 134].
- `[INFERENCE]` Main paths 2–3 m wide, so two pairs of avatars pass without breaking step. Side paths 1.2–1.5 m.

**Edges and refuge.**
- At the edge, "one can see, but not be seen too much" [Gehl 2011 p. 149]. Half shade with a view, and niches you can withdraw into, are especially valued [Gehl 2011 p. 151].
- In parks, the preferred refuges are under trees and at vegetation edges [Terrapin 2014 P12].
- Trees in groves, sun, wind shelter and water make plazas comfortable [Whyte 1980 via Han 2012].

**Mystery and stimuli.**
- Curving edges that slowly reveal.
- Views at least 20 ft (6 m) deep, ideally 100 ft (30 m).
- At least one edge of the focal subject hidden, preferably two.
- A shallow obscured view "lead[s] to unpleasant surprises" [Terrapin 2014 P13].
- Non-rhythmic stimuli (breeze, rustling plants, water) "approximately every 20 minutes for about 20 seconds," visible from more than 20 ft [Terrapin 2014 P3].
- Water should be touchable [Whyte 1980 via Han 2012]. A multi-sensory water experience works best [Terrapin 2014 P5].

**Views.** Put the best view at transitions (paths, stairs, entries) rather than gaping at it from every seat [APL 134].

**Conversation.** Background noise below 60 dB (§1.6). `[INFERENCE]` Place ambient sound sources (fountains, music) more than 8 m from benches.

**Pitfalls.**

| Pitfall | Symptom | Key |
|---|---|---|
| Long straight path with no stops | People turn back | [Gehl 2011 p. 137] |
| Sunken plaza or stepped detour | Avoided | [Gehl 2011 pp. 97, 142] |
| Benches back to back, or far apart | Conversation inhibited or impossible | [Gehl 2011 p. 169] |
| Leftover open lawn | Nobody sits on it; there is "nothing to sit next to" | [Gehl 2011 p. 153] |

**Verify:** walk the route in a top-down view. There is a stop every 30–60 m, path widths are ≥2 m on loops, and the benches face the path or the view.

---

## 7. Combining archetypes and the transitions between them

Most worlds mix archetypes:
- a home (A2) with bedrooms (A1)
- a venue (A3) with retreats (A1-nested) and a stage (A4)
- a garden (A5) linking pavilions (A1)

**Order by the intimacy gradient.** Run entrance → public (A3 / A4 / A5) → semi-private (A2 groups) → private (A1) [APL 127]. Put sitting spaces at every step of the gradient, shaped by their position [APL 142].

**Thresholds.**
- **Transitions as lingering zones.** Transition zones where people "view both spaces at the same time" are favourite places to stay [Gehl 2011 p. 149]. Make every threshold a small lingering place, not just a doorway `[INFERENCE]`.
- **Change the senses.** At a threshold, change at least 2 of: ceiling height, floor material, light level, sound, enclosure. Ralston's suite arrival uses a compressing vestibule plus a material or ceiling shift [Ralston 2026]; the count of 2 is `[INFERENCE]`.
- **Turn before private rooms.** Put a branch corridor that turns away, or a vestibule, before an A1 room [Ralston 2026]. Give the couple's realm its own distinct domain [APL 136].
- **Half-open walls.** Columns, interior windows, sitting walls, glass partitions and half walls keep neighbouring archetypes visually linked but separate [APL 193; Homebuilding 2026].
- **Glimpse ahead.** Each entrance offers "a place to stand and catch a glimpse" of the next space [Susanka-Bungalow].
- **Zen view.** Reveal the big view at the transition, not from the room itself [APL 134].

**Acoustics `[INFERENCE]`, from [AWDK social-vr].** Order spaces so voice and music get quieter along the gradient:
- A3 dancefloor → A3 booths: at least 6 m apart.
- A3 or A4 → any A1 room: at least 25 m, or an audio zone.
- Two A1 rooms: at least 25 m, or separate audio zones, so couples do not hear each other.

**Common combinations.**

| Combination | Layout pattern | Key |
|---|---|---|
| Venue + retreats | The busy floor is central; booths line the edges; quiet rooms sit up a stair or down a turning corridor | [AWDK social-vr] Great Pug/Black Cat pattern; [APL 179] |
| Home + audience room | A media room sits off the common area, away from bedrooms; sociopetal sofas can turn to the screen | [Ralston 2026] buffer rule; [INFERENCE] |
| Home + away room | A small A1 room off the A2 heart | [Susanka-Libertyville] |
| Garden + pavilions | A5 loop with stops; A1 refuges at vegetation edges with views back | [Terrapin 2014 P12]; [Gehl 2011 p. 151] |
| Lobby / venue zoning | Distinct on-the-go, social, dining and quiet zones in one space; booths for privacy | [ShelbyWilliams 2013] |

**Pitfalls.**

| Pitfall | Symptom | Key |
|---|---|---|
| Retreat opens straight onto the dancefloor | Intimacy destroyed | [APL 127] |
| All archetypes in one hall | Noise; nobody settles | [Homebuilding 2026]; [AWDK social-vr] |
| Private rooms on the way to public ones | Guests walk through bedrooms | [APL 127] |

**Verify:** label every room with its archetype. Gradient depth from spawn rises toward A1, every A1 room passes the 25 m / audio-zone test, and every threshold changes at least 2 senses.

---

## 8. Decision table: archetype → sections that apply

| Archetype in the world | Read | Key numbers |
|---|---|---|
| A1 Intimate retreat | §1.1, 1.2, 1.5, 1.6, 1.7, 1.8, **§2**, §7 if nested | 4–8 m² per person; bed clearance 0.76–0.91; alcove ≤1.83 × 0.9–1.8; facing seats ≤1.07; ceiling over bed ≈2.3 |
| A2 Social home | §1.1–1.8, **§3**, §2 for its private rooms, §7 | 8–14 m² per person; common room ≈5 × 7 m, ≥3 m ceiling; diner clearance 0.91–1.12 |
| A3 Gathering venue | §1.1, 1.3–1.8, **§4**, §2 for nested retreats, §7 | 4–8 m² per person (VR); room ≤25 m across; stools 0.61–0.76; tables ≥0.30 apart |
| A4 Audience space | §1.5, 1.6, 1.7, 1.8, **§5**, §7 | first row ≥0.6 W; vertical angle <25°; row pitch ≈1.4; 30–40° screen field |
| A5 Scenic / walk-and-talk | §1.1, 1.3, 1.4, 1.5, 1.6, 1.7, **§6**, §7 | stop every 30–60 m; paths 2–3 m; views ≥6 m deep |
| Any mix of the above | **§7** first, then each archetype's section | gradient order; 25 m or an audio zone between loud and quiet spaces |

Intake question `[INFERENCE]`: "Which of these spaces does the world contain, and for how many people each?" Size every room from the m² per person band for its archetype. Then lay them out along the intimacy gradient.

---

## Sources

Source keys in this file resolve in [SOURCES.md](../../SOURCES.md).

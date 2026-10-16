# Social-VR / VRChat space design — knowledge base for `world-architect` and `layout-reviewer`

Research date 2026-10-09. Scope: what makes social (hangout) worlds work spatially, expressed as numbers and
checks an agent can apply when placing walls, rooms, seats and spawns in Unity 2022.3 for VRChat PC.

**Citation convention.** Every claim carries a tag. `[Author Year]` / `[Org Short-title]` = taken from that
source (full entry in **## Sources**). `[X, citing Y]` = I read X, which reports Y's finding; Y itself was not
read. `[INFERENCE]` = my own derivation or recommendation from the cited material — a tunable default, not a
platform fact. `[UNVERIFIED]` = plausible but not confirmed by anything I read. `[WORKSPACE RULE]` = this
workspace's own policy, not an external source.

Relation to existing notes: the note [`.omp/skills/vrchat-world-gotchas/reference/hai-guides-refresh.md`](../../../vrchat-world-gotchas/reference/hai-guides-refresh.md)
[Workspace Haï-refresh 2026] already covers capacity (Maximum vs Recommended), portal blocking, interact reach,
lighting/tech caveats, colourblind/Japanese-font advice and "keep the hangout near the origin". That note records
that Haï's *World Design* page holds only the colourblind and font topics — nothing on spatial or social layout —
so this file adds the missing spatial-social layer and does not repeat those items. (I did not re-read Haï's pages
myself; that statement relies on the workspace note.)

---

## 1. Platform facts that constrain layout (VRChat)

| Fact | Value | Tag |
|---|---|---|
| Player voice Far (audible range) | **25 m** default. Near 0 m, and the docs say to leave it at 0. Voice gain is 15 dB by default (range 0–24). A low-pass filter is applied to distant voices. | [VRChat Player Audio] |
| Avatar audio Far | 40 m default, gain ≤ 10 dB | [VRChat Player Audio] |
| World `VRC_SpatialAudioSource` | Far 40 m default, +10 dB default gain, roughly inverse-square falloff. The docs say "we do not recommend using 2D audio." | [VRChat Spatial Audio Source] |
| Voice occlusion | Popular hangouts (The Black Cat, The Great Pug, Midnight Rooftop, Drinking Night, The Pool Parlor) use UdonVoiceUtils for occlusion, audio zones and voice directionality. AudioManager offers "Fake Audio Occlusion using Trigger Colliders". | [Guribo UdonVoiceUtils], [SylanTroh AudioManager] |
| Walls block voice? | No native wall occlusion. | [INFERENCE], drawn from why the two tools above exist |
| Locomotion defaults | Walk 2 m/s, Run 4 m/s, Strafe 2 m/s. **Jump impulse 0 (off).** The VRCWorld prefab sets jump to 3. Gravity ×1. | [VRChat Player Forces] |
| Jump apex at impulse 3 | ≈ v²/2g = 9/19.6 ≈ **0.46 m** | [INFERENCE] (physics) |
| Avatar scale | Player-controlled eye height runs **0.2 m to 5 m**. Scaling "does **not** affect its collision with the environment". | [VRChat Avatar Scaling] |
| Player capsule (simulator) | In ClientSim's local-player CharacterController: height 1.6 m, radius 0.2 m, slope limit 50°, step offset 0.5 m. ClientSim's default avatar height is 1.9 m. | [VRChat ClientSim prefab], [VRChat ClientSim Player] |
| Does the live client use the same capsule? | Unknown | [UNVERIFIED] |
| Player-to-player collision | Players can walk through each other | [UNVERIFIED] (not stated in docs I read) |
| Spawn | `Spawns[]`; set **Spawn Radius > 0** so players arriving together don't spawn inside one another; Spawn Order First/Sequential/Random/Demo; default orientation = align player with spawn transform | [VRChat First World], [VRChat Scene Descriptor] |
| Capacity | Reaching Recommended Capacity removes a public instance from the public list. Maximum Capacity blocks ordinary joins. | [VRChat First World] |
| Performance gates | "Aim for at least 45 FPS with a single VR user at the spawn." More than one mirror or more than two video players in a room causes "bad things". The docs "STRONGLY SUGGEST" not enabling mirrors by default. | [VRChat Labs Tips] |
| Mirror cost | A mirror reflecting the whole world doubles render cost. Occlusion culling doesn't work in reflections. A mirror facing away from the world's centre renders less. | [VRChat Wiki Mirrors] |
| Mirror docs | Keep mirrors off by default; enable on approach or by button; limit Reflect Layers | [VRChat Mirror Reflection] |
| Common failure | "worlds where you immediately drop out of the portal forever" | [VRChat Labs Tips] |
| Seated play | Meta: expect about half of players to sit. In a Stanford field course, 92.5–95.4 % sat during VR group sessions. | [Meta 2026 Seven Design Decisions], [Han 2024] |

Derived travel times [INFERENCE]: at 2 m/s walking, 10 m = 5 s and 30 m = 15 s. Crossing the 25 m voice radius
takes about 12 s. Anything within one 25 m disc is acoustically one room unless audio zones split it.

---

## 2. Proxemics and group-formation research

| Finding | Number | Tag |
|---|---|---|
| Hall's zones as used in VR studies | intimate < 0.45 m, personal 0.45–1.2 m, social 1.2–3.6 m, public > 3.6 m (public-far > 7.6 m) | [Williamson 2021, citing Hall], [Williamson 2022] |
| Personal space toward avatars | Roughly circular, ~1 m radius, similar to real life | [Williamson 2021, citing Hecht et al.] |
| Approach distance | People keep more distance in front of virtual humans than behind them, and give more space to agents that hold mutual gaze | [Bailenson 2003] |
| HMD vs desktop users | HMD users keep personal-to-social distance and turn their heads to keep the speaker in view. Desktop users crowd into the personal/intimate zone and collide more. | [Williamson 2022] |
| Head-to-head distance in VR groups of 2–4 | Mean **2.0 m** in a private room; **1.8 m** when four other groups share the room | [Han 2024] |
| Effect of background chatter | Groups move closer ("leaning in"). The study tested a "bubble" model that silences voices beyond 8 m. | [Williamson 2022] |
| Conversation size limit | Spontaneous conversation has "an upper limit of about four" people | [Dunbar 1995] |
| Too dense | 7 people at **2.8 m²/person** (5 m-diameter room): rated "too small", "crowded", "claustrophobic"; lower scores for understanding and working together | [Williamson 2025] |
| Too sparse | 26 attendees in a 70 × 40 m space used ~20 × 15 m (16 people). A static amphitheatre was ignored. The large room made small-group formation hard; smaller rooms gave cohesive circles. | [Williamson 2021] |
| Corners | Pilots showed people positioning in corners, creating arbitrary hotspots; the final test rooms were circular | [Williamson 2025] |
| Floor graphics | Hexagonal floor decals deterred people; they "surf[ed] the edge" | [Williamson 2021] |
| Spawn collisions | Intimate-zone collisions happen at spawn points; people then move apart | [Williamson 2021] |
| Seating capacity | "Effective capacity is roughly .9 meters of sitting space per person" | [Williamson 2025, citing Whyte] |
| NYC plaza rules | ≥ 1 linear ft of seating per 30 ft² (≈ 1 m of seat edge per 9.3 m²); ≥ 2 seating types; "social seating" in angled/curved groupings; seats 16–20 in high; circulation paths ≥ 8 ft | [NYC DCP 2021] |
| Mirror behaviour | Users gather in front of mirrors en masse, sit in a circle there, wait there to be approached, and use the mirror to see behind them. Mirrors improve self-perception but may hurt conversational performance. | [Fu 2023] |
| Virtual "third places" (MMO cantinas) | One shared conversational space lets the loudest dominate. With no quieter alcove, people retreat to private chat. Player venues far from transport hubs died for lack of foot traffic. Median stay was 7–8 min. Regulars (≥ 14 days present) were 5.9–8.6 % of visitors. | [Ducheneaut 2007] |
| Moore's success factors | Accessibility, social density, activity resources and hosts; expansive or complex spaces "often make poor virtual places" | [Williamson 2022, citing Moore et al.] |

Practical translation [INFERENCE]: for HMD users, plan **1.0–1.2 m** neighbour spacing and **~2 m across** a
3–4-person group. Never force adjacency under 0.6 m. Leave ≥ 1 m behind each person before a wall or a path.

---

## 3. Principles and good practice

Each item gives the rule, then numbers, then **Verify:** — how a reviewer checks it from screenshots or scene data.

### 3.1 Spawn and arrival

**S1. Spawn into a vestibule or overlook, one threshold from the main room.**
- The Black Cat spawns you in a vestibule with community posters, leading to a hallway and then the main concourse [VRChat Wiki Black Cat].
- The Great Pug has posters next to spawn [VRChat Wiki Great Pug].
- Rec Room recommends letting players "get a sneak peek" before they join [Rec Room 2024 Layout].
- [INFERENCE] Put the spawn pad 5–10 m walk from the nearest conversation cluster and ≤ 25 m from the main gathering point, with that point visible from the pad.

**Verify:** line of sight from spawn at the reference eye height (WORLD.md, default 1.2 m) to the hub centre; path length from spawn to the nearest cluster in 5–25 m.

**S2. Face arrivals toward the room.**
- The default spawn orientation aligns the player with the spawn transform [VRChat Scene Descriptor].
- [INFERENCE] Point the transform's forward axis at the hub or a landmark. Never face a wall within 3 m.

**Verify:** a forward ray from spawn hits nothing within 3 m, and the hub sits within ±30° of forward.

**S3. Keep the spawn pad clear.**
- Spawn Radius must be > 0 [VRChat First World]. [INFERENCE] Use 0.5–1.5 m.
- People collide at spawn points [Williamson 2021].
- [INFERENCE] Keep a ≥ 3 m clear disc with no seats, props, mirror, colliders or triggers, and ≥ 4 m of clear height. The spawn must not sit inside any cluster's ring.

**Verify:** `OverlapSphere(3 m)` at each spawn returns only the floor; an upward raycast clears ≥ 4 m.

**S4. Make the exit wide and obvious.**
- Horizon's onboarding guidance uses clear landmarks and consistent colour cues, and warns that lighting cues are weak in bright daytime worlds [Meta Horizon Onboarding].
- [INFERENCE] Give the vestibule a ≥ 2 m opening, or two exits.

**Verify:** measure opening width between collider faces; the exit sits within the central 60° of the spawn view.

**S5. Keep the spawn cheap and calm.**
- Target ≥ 45 FPS at spawn with one VR user; mirrors off by default [VRChat Labs Tips].
- [INFERENCE] No loud source reaching spawn; set each world source's Far to its room size rather than the 40 m default [VRChat Spatial Audio Source].

**Verify:** no `VRC_MirrorReflection` is active in the saved scene; list AudioSource ranges that reach spawn.

**S6. Spawn on solid, static ground.**
- Avoid the "drop out of the portal forever" failure [VRChat Labs Tips].
- [INFERENCE] Spawn on a static floor sloped ≤ 5°, and set Respawn Height ≥ 5 m below the lowest floor.

**Verify:** a down-ray from each spawn hits a static collider within 0.3 m; `RespawnHeightY` < lowest floor − 5.

**S7. Let late joiners rejoin the flow.**
- "Check whether late joiners can re-enter the social flow without confusion" [VRCreators 2026].
- [INFERENCE] The arrival path must not cross a cluster or a stage.

**Verify:** path polyline from spawn to hub avoids the cluster discs and the stage footprint.

**S8. Onboard first-time visitors without blocking regulars (optional).**
- Horizon recommends a small, isolated area where first-time players learn the core loop, with returning players spawned elsewhere and a way to re-onboard [Meta Horizon Onboarding].
- [INFERENCE] In a hangout, the vestibule/poster wall plays this role.

### 3.2 Gathering points and conversation clusters

**C1. Many small clusters, few big ones.**
- Spontaneous conversation caps at about four people [Dunbar 1995].
- The Great Pug's top floor has a fireplace with four seats and a sofa; its ground floor has 11 booths and 5 tables [VRChat Wiki Great Pug].
- [INFERENCE] Default cluster = 3–5 seats. Add 2-seat pockets and **one** 6–10-seat "big table / fireplace" group.

**Verify:** count seat groups; cluster sizes should mostly be 3–5, none above 10.

**C2. Seats face a shared centre.**
- In breakout rooms, standing in a circle made it "easy to immediately identify the speaker" [Williamson 2021].
- Group orientation (F-formations) matters as well as distance [Williamson 2022, citing Kendon].
- NYC asks for angled or curved "social seating" [NYC DCP 2021].
- Quest 2 horizontal FOV is 104° [Han 2024].
- [INFERENCE] Seat-front radius 0.9–1.6 m from the cluster centre; each seat's yaw within ±25° of the centre; rows of sofas facing a wall or TV are not conversation seating.

**Verify:** per seat, the angle between seat-forward and the direction to centre ≤ 25°; all other members fall within a 100° cone from each seat.

**C3. Space seats in the personal-to-social band.**
- Basis: [Han 2024] (1.8–2.0 m head-to-head) and [Williamson 2022] (HMD users avoid the intimate zone).
- [INFERENCE] Neighbour seat centres 0.8–1.2 m apart; across the group 1.8–3.0 m.

**Verify:** all pairwise seat distances inside a cluster fall within 0.6–3.2 m.

**C4. Route circulation behind backs, never through the middle.**
- People keep more distance from fronts than from backs [Bailenson 2003].
- [INFERENCE] Leave a ≥ 1 m ring behind seats; main paths run tangent to clusters, not through them.

**Verify:** paths don't intersect the disc defined by the cluster centre and its seat radius.

**C5. Put clusters on edges and in pockets.**
- People hug edges and use corners [Williamson 2021], [Williamson 2025].
- NYC allows alcoves and niches as "minor portions" of plazas, visible from the main area [NYC DCP 2021].
- [INFERENCE] Each cluster within 3 m of a wall, rail, window or planter edge; keep room centres for movement and activity.

**Verify:** distance from each cluster centre to the nearest vertical boundary ≤ 3 m.

**C6. Give every cluster a focal object.**
- MMO cantina activity provides "triangulation" that bootstraps interaction [Ducheneaut 2007, citing Whyte].
- Rec Room's list of hangout features: fire pits, pools, hot tubs, mirrors, videos, food, drawing boards, icebreaker games, small social games, trampolines [Rec Room 2024 Social].
- Jumping into a virtual ocean together broke the ice at a workshop [Williamson 2021].

**Verify:** each cluster has ≥ 1 non-seat feature within 2 m of its centre.

**C7. Vary the clusters' character.**
- NYC requires ≥ 2 seating types "to accommodate small groups socializing as well as individuals engaged in solitary activities" [NYC DCP 2021].
- [INFERENCE] Across a world, vary at least two of: ceiling height, light, floor, enclosure, view.

**Verify:** screenshots of three clusters are distinguishable without labels.

### 3.3 Quiet vs loud zones and acoustic separation

**A1. Zone the plan by noise level.**
- With no quieter alcove or backroom, the loudest users dominate and conversation moves into private chat [Ducheneaut 2007].
- The Great Pug's floors run from bar (ground) → stage and billiards (floor 2) → fireplace and beds up in "The Roost", reached by six flights [VRChat Wiki Great Pug].
- [INFERENCE] Order zones loud (stage, music, video, games) → medium (bar, lounge) → quiet (alcoves, balcony, top floor, sleep loft).

**A2. Budget distance and occlusion.**
- Voice reaches 25 m [VRChat Player Audio] and walls don't occlude it [INFERENCE].
- The bubble audio model silences voices beyond 8 m [Williamson 2022].
- In a shared room, people could hear other groups but not make out details, and groups stood closer [Han 2024].
- [INFERENCE] Cluster centres in one open room ≥ 6 m apart, ≥ 8 m preferred.
- [INFERENCE] Quiet zones ≥ 15 m path distance from loud sources, or inside an audio zone using the existing community tools [Guribo UdonVoiceUtils], [SylanTroh AudioManager].
- Music sources: set Far to room scale and avoid 2D audio [VRChat Spatial Audio Source].
- Don't overdo separation in activity areas: "If the sound falloff is too sharp, you risk transforming a fantastic multiplayer game into a single-player experience." [Rec Room 2024 Social].

**Verify:** distances between cluster centres; intersect AudioSource range spheres with quiet-zone bounds.

**A3. Put a threshold between loud and quiet.**
- [INFERENCE] Use a doorway, a corridor ≥ 5 m, a level change or a 90° turn.

**Verify:** no quiet cluster has a direct line of sight to a stage or speaker within 15 m.

### 3.4 Mirrors (research background, not a default)

> **Kit rule [user rule]:** VRChat now has personal mirrors, so worlds get **no** mirror zone and no mirror toggle. A mirror is placed only as a real object where the room type actually has one (bathroom, gym, dance or dressing room). M1–M2 below are background on how people use world mirrors and apply only to such diegetic mirrors.

**M1. People cluster at mirrors.**
- In one popular world, "almost all the people … are in the big mirror area" [Fu 2023].
- Users sit in a circle in front of mirrors and wait there to be approached [Fu 2023].
- [INFERENCE] A diegetic mirror at a gym or dance wall draws a crowd; leave standing room in front of it.

**M2. Place mirrors at an edge, facing outward.**
- Facing away from the world's centre is cheaper [VRChat Wiki Mirrors].
- No more than one mirror per room, off by default [VRChat Labs Tips].
- Enable on approach and disable on exit; HQ, LQ and transparent variants are common setups [VRChat Mirror Reflection], [VRChat Wiki Mirrors].
- [INFERENCE] Keep mirrors ≥ 8 m from spawn and off the arrival path.

**Verify:** the dot product of the mirror normal with (world centre − mirror position) is < 0; the mirror is inactive in the saved scene; one mirror per room.

**M3. Keep talk clusters that don't face a mirror.**
- Mirrors may impair conversation [Fu 2023].
- [INFERENCE] Quiet and talk clusters face each other, not a mirror.

### 3.5 Density and capacity

**D1. Size the floor by social density.**
- 2.8 m²/person was rated claustrophobic [Williamson 2025].
- At very low density, people used only ~11 % of the space [Williamson 2021].
- [INFERENCE] Target **8–14 m² per player** gross at Recommended Capacity, never below **4 m²/player** at Maximum Capacity. More than ~30 m² per expected player in one open room feels dead.

**Verify:** walkable social floor area ÷ Recommended Capacity.

**D2. Split large capacities across rooms and floors.**
- Rec Room: "Instead of creating a large experience, make it smaller with verticality, keeping players together" [Rec Room 2024 Layout].
- [INFERENCE] Hold ≤ ~24–30 people per room.

**D3. Supply enough seats.**
- About half of players sit [Meta 2026 Seven Design Decisions].
- NYC requires ≥ 1 ft of seating per 30 ft² [NYC DCP 2021].
- [INFERENCE] Seats (including ledges and stools) ≥ 0.6 × Recommended Capacity; seating edge ≥ 1 m per 9 m² of plaza-like floor.

**Verify:** seat count ÷ capacity.

### 3.6 Sightlines and orientation

**V1. Let people see who arrives.**
- Social cues such as noticing who leaves or enters support "social translucence" [Williamson 2021].
- [INFERENCE] At least one seat per cluster sees the room entrance; cluster backs go to walls, not to traffic.

**Verify:** line of sight from each cluster centre to the main entry.

**V2. Provide an overlook.**
- Rec Room: sneak-peek platforms and spectate areas; players "enjoy watching others having fun from the hub platforms" [Rec Room 2024 Layout].
- The Black Cat has a balcony overlooking its second storey [VRChat Wiki Black Cat].
- [INFERENCE] At least one elevated vantage per main room.

**V3. Use landmarks and consistent cues.**
- Rec Room: "beacons, highlights, lights" [Rec Room 2024 Layout].
- Horizon: clear landmarks; reuse the tutorial colour cue in the main world [Meta Horizon Onboarding].

**Verify:** each zone has one obvious focal element in screenshots.

**V4. Keep visibility across the space.**
- NYC requires plazas to be fully visible from the street and caps planter walls at 18 in to keep visibility [NYC DCP 2021].
- [INFERENCE] Between same-noise zones, use partitions ≤ 0.9–1.1 m, glass or open rails rather than full walls.

### 3.7 Avatar-scale variety and seated players

**H1. Collision size is fixed; visible avatar size is not.**
- Eye height ranges 0.2–5 m, and scaling doesn't change collision [VRChat Avatar Scaling].
- [INFERENCE] Clear heights: spawn and main hall ≥ 4 m, rooms ≥ 3 m, door heads ≥ 2.4 m, nothing below 2.3 m over a path. Mirror top ≥ 2.8 m.

**Verify:** upward raycasts on a 1 m grid over walkable floor.

**H2. Small and seated avatars must be able to see.**
- About half of players sit [Meta 2026 Seven Design Decisions].
- [INFERENCE] Counters and rails in conversation sightlines ≤ 1.0 m or transparent; table centrepieces ≤ 0.3 m; assume seated eye level ≈ 1.1–1.2 m.

**Verify:** line of sight between seat eye points at 1.1 m is unobstructed.

**H3. Place interactables within reach.**
- Make sure "buttons are not too high or too low" [Lee 2022].
- ClientSim scales interact distance with tracking scale [VRChat ClientSim Player].
- [INFERENCE] Put buttons at 0.9–1.3 m, not behind seats or across tables.

**Verify:** heights of Interact colliders.

**H4. Don't require turning around.**
- A disabled participant could not turn to face someone speaking behind him [Maloney 2020].
- [INFERENCE] Satisfied by C2.

### 3.8 Locomotion and comfort

**L1. No ladders, required jumps or climbing.**
- Meta: teleport across gaps; teleport players to the top or bottom of climbing surfaces [Meta 2025 Locomotion Environments].
- VRChat jumping is off by default [VRChat Player Forces].

**L2. Stairs as gentle, straight ramps.**
- Meta: "limit movement to flat surfaces and avoid slopes and stairs when possible"; use gentle slopes instead of stairs, minimise steps, avoid spiral staircases [Meta 2025 Locomotion Environments].
- One smooth ramp collider per flight [WORKSPACE RULE].
- [INFERENCE] Slopes ≤ 7° preferred, ≤ 15° maximum; landings every ≤ 1.5 m of rise.

**Verify:** collider slope angles; no helical stairs on main routes.

**L3. Keep walls at a distance.**
- Nearby textured walls increase optic flow and motion-sickness risk [Meta 2025 Locomotion Environments].
- NYC requires circulation paths ≥ 8 ft (2.4 m) [NYC DCP 2021].
- [INFERENCE] Main corridors ≥ 2.5 m; spawn exit ≥ 2 m; other doors ≥ 1.2 m; no corridor longer than 15 m; no fine high-contrast stripes along paths.

**L4. No forced motion.**
- [INFERENCE from Meta 2025 Locomotion Environments] No moving floors, auto-rotation or camera shake at spawn or in social areas; elevators as fade-teleports.

**L5. Keep walks short.**
- Venues far from foot traffic died [Ducheneaut 2007].
- [INFERENCE] Spawn to hub ≤ 25 m; hub to any cluster ≤ 30 m; the whole social core within ~50 m.

### 3.9 The loop: reasons to stay and to return

Oldenburg's third-place criteria, as quoted and tested in [Ducheneaut 2007], with spatial moves [INFERENCE]:

| Criterion | What the source says | Spatial move [INFERENCE] |
|---|---|---|
| Neutral ground | Individuals "may come and go as they please"; cantinas became "drive-thrus" when visits were purely functional | Clusters joinable from their open side; exits visible from every cluster |
| Leveler and mixer | Each visitor "knows" only 1.2–1.9 % of daily visitors | Mixed seat sizes; one big table where strangers mingle |
| Conversation is the main activity | Talk quality signals a third place; noise dominates in a single shared space | Talk clusters outnumber activity stations; separate them acoustically (A1–A3) |
| Regulars | "It is the regulars who give the place its character"; they interact with far more people | A regulars' corner (bar, fireplace) with a view of the entry |

Other retention patterns, each from its source:
- Community poster boards at spawn [VRChat Wiki Black Cat], [VRChat Wiki Great Pug].
- Seasonal decorations [VRChat Wiki Black Cat], plus annual holidays with a 'hunt' for hidden objects [VRChat Wiki Great Pug].
- Secret or unlockable areas — vents and secret doors [VRChat Wiki Black Cat].
- A stage for concerts [VRChat Wiki Great Pug].
- Photo booths and spectator areas [Rec Room 2024 Social], [Rec Room 2024 Layout].
- Selfies helped people bond [Williamson 2021].
- Sleep worlds and recurring events as meaningful activities [Maloney 2020].
- Short daily quests [Meta Horizon Retention].
- "Shorten the time to fun" [Meta 2026 Seven Design Decisions].

Per-hangout minimum [INFERENCE]: ≥ 3 activity resources of different intensity, ≥ 1 secret, ≥ 1 event-capable focal area acoustically separated from the quiet zone, and ≥ 1 photo spot.

### 3.10 Exemplar layouts

- **The Black Cat** [VRChat Wiki Black Cat]
  - Spawn: a vestibule with posters, then a hallway with couches and a kiosk.
  - Main concourse: bar, stage, booths, tables and mirrors; restrooms off it.
  - Upstairs: a second lounge with a bar, stage and mirror.
  - Side rooms: kitchen and stairwell.
  - Extras: vents connecting rooms above the main floor; a locked balcony overlooking the second storey.
  - It uses UdonVoiceUtils voice directionality and occlusion [Guribo UdonVoiceUtils].
- **The Great Pug** [VRChat Wiki Great Pug]
  - Four floors.
  - Ground floor: a double-sided bar, 11 booths, 5 tables, bathrooms and a back-alley exterior.
  - "Night View Hall": bar, stage, billiards and tables.
  - "The Roost": a fireplace cluster with round tables, and a loft with 5 beds.
  - Spawn sits beside a poster wall.
  - It uses occlusion and voice directionality [Guribo UdonVoiceUtils].
- Pattern common to both [INFERENCE]: threshold spawn → busy central floor with many booths → vertical progression to quieter, smaller rooms → hidden extras. Neither is ever one room.

---

## 4. Capacity planning table [INFERENCE]

**Assumptions:**
- Cluster footprint ≈ π(r + 1 m)², with seat radius r ≈ 1.1–1.6 m. That gives **15–20 m² per 3–6-seat cluster** (spacing from [Han 2024] and [Williamson 2022]).
- Conversation zones ≈ ⌈N/4⌉ + 1. The /4 follows [Dunbar 1995]; the +1 keeps a free spot for newcomers.
- Circulation and amenities multiply cluster area by 1.6–2.0.
- Results were checked against D1.

| Recommended capacity N | Social floor (walkable m²) | m²/player | Conversation zones (3–5 seats) | Quiet / separated zones | Mirror zones (≤ 1 active per room) | Big focal area (stage/screen/fire) | Rooms/levels | Seats (≥ 0.6 N) |
|---|---|---|---|---|---|---|---|---|
| 2–4 (private home) | 30–60 | 10–15 | 2 (one 2-seat nook) | 1 | 1 small | 0–1 | 1–2 spaces | 4–6 |
| 8 | 70–110 | 9–14 | 3 | 1 | 1 | 1 | 2 | 6–8 |
| 16 | 140–220 | 9–14 | 5 | 2 | 1 | 1 | 2–3 | 10–14 |
| 24 | 200–320 | 8–13 | 7 | 2 | 1–2 | 1 | 3 | 15–20 |
| 32 | 260–420 | 8–13 | 9 | 3 | 2 (different rooms) | 1–2 | 3–4 | 20–26 |
| 40 | 320–520 | 8–13 | 11 | 3–4 | 2 | 2 | 4 | 24–32 |
| 64–80 (events) | 500–900 | 7–12 | 17–21 | 4–5 | 2–3 | 2 (one event hall) | ≥ 4 + separately sized event hall | 40–55 |

**Hard limits [INFERENCE]:**
- ≤ ~30 expected players in any single open room.
- ≥ 4 m²/player at Maximum Capacity. The ~2 × figure follows the legacy doubling rule in [VRChat First World]; check the actual setting.
- No room wider than ~35 m without audio zones, because voice reaches 25 m [VRChat Player Audio].

---

## 5. Pitfalls (symptom → cause → fix)

| # | Pitfall | Symptom (screenshot / scene data / playtest) | Fix | Basis |
|---|---|---|---|---|
| P1 | **Literal box** (a past luxury-residence world's first layout, [case study](../case-studies/luxury-penthouse-layout.md)) | One rectangle with furniture lining the walls, an empty centre and uniform ceiling and light; everyone piles at one spot | ≥ 3 zones differing in enclosure, ceiling or light; clusters in pockets | [INFERENCE] from [Williamson 2021], [Ducheneaut 2007] |
| P2 | Spawning into the crowd | Arrivals overlap seated players; clusters within 3 m of spawn | Vestibule spawn, 3 m clear disc, radius > 0 | [Williamson 2021], [VRChat First World] |
| P3 | Spawn faces a wall or a dark void | The first spawn screenshot shows a wall or black | Rotate the spawn toward the hub | [INFERENCE] |
| P4 | Spawn far from the social core | > 30 m or > 15 s before seeing anyone | Move the hub to the spawn, or the spawn to the hub | [Ducheneaut 2007] |
| P5 | Oversized hall | > 30 m² per player in one room; groups use a fraction of it; unused amphitheatre | Shrink, split, add verticality | [Williamson 2021], [Rec Room 2024 Layout] |
| P6 | Over-dense room | < 4 m² per player at max; people lining the walls | Enlarge, or add rooms | [Williamson 2025] |
| P7 | One acoustic space | Clusters < 6 m apart with no audio zones; loud users dominate | Spacing, audio zones, a quiet floor | [Ducheneaut 2007], [INFERENCE] |
| P8 | Mirror as the only gathering point, or a mirror at spawn | All players at one wall; FPS drop at spawn | Separate mirror zone plus talk clusters | [Fu 2023], [VRChat Labs Tips] |
| P9 | Theatre-row seating for chat | Sofas in a row facing a wall or TV | Arc or circle seating | [Williamson 2021], [NYC DCP 2021] |
| P10 | Path through the middle of a group | The path crosses a cluster centre | Route paths behind seat backs | [Bailenson 2003], [INFERENCE] |
| P11 | Accidental floor graphics | Decals nobody stands on; people walking the edges | Put rugs under clusters, not across paths | [Williamson 2021] |
| P12 | Low ceilings or beams | Tall avatars' heads clip into geometry | Meet H1 clearances | [VRChat Avatar Scaling], [INFERENCE] |
| P13 | Tall counters or rails in sightlines | Small or seated avatars can't see the group | H2 heights, or glass | [Meta 2026 Seven Design Decisions], [INFERENCE] |
| P14 | Ladders, spiral stairs, required jumps | Players get stuck; complaints of discomfort | Ramps or teleports | [Meta 2025 Locomotion Environments], [VRChat Player Forces] |
| P15 | Narrow corridors or doors near spawn | 1 m corridors, long tubes, striped textures | L3 widths | [Meta 2025 Locomotion Environments], [INFERENCE] |
| P16 | Dead space | A room with no seat, focal object or activity | Add a cluster and a focal object, or cut the room | [Williamson 2021], [Williamson 2022, citing Moore et al.] |
| P17 | Music bleeds everywhere | 40 m-Far sources reach the quiet zone | Set Far to room size; add zones | [VRChat Spatial Audio Source] |
| P18 | Several mirrors, or > 2 video players | FPS < 45 | One mirror per room, off by default | [VRChat Labs Tips] |
| P19 | Interactables out of reach | Buttons at 1.8 m, behind sofas or across tables | H3 placement | [Lee 2022] |
| P20 | Pretty but nothing to do | < 3 activity resources, no secrets | Meet the 3.9 minimums | [Rec Room 2024 Social], [VRChat Wiki Black Cat] |
| P21 | Accidental hotspot corners | Groups form in corners and ignore the designed seating | Put clusters at the edges, or chamfer the corners | [Williamson 2025] |

---

## 6. Checklists

### 6.1 Spawn-area checklist (layout-reviewer must pass all)

- [ ] ≥ 1 spawn transform; Spawn Radius 0.5–1.5 m [VRChat First World] [INFERENCE for the range].
- [ ] For events, ≥ 2 spawns or Random order [INFERENCE].
- [ ] The spawn's forward axis points at the hub within ±30°, with no wall within 3 m in front [INFERENCE].
- [ ] A 3 m-radius clear disc around each spawn: no seats, props, colliders, triggers or mirrors [INFERENCE; collisions at spawn per Williamson 2021].
- [ ] ≥ 4 m clear height above every spawn [INFERENCE from VRChat Avatar Scaling].
- [ ] A static, flat (≤ 5°) collider directly under each spawn [INFERENCE].
- [ ] `RespawnHeightY` ≥ 5 m below the lowest floor [INFERENCE; drop-out warning in VRChat Labs Tips].
- [ ] The hub is visible from spawn at the reference eye height (default 1.2 m) and is 5–25 m away [INFERENCE].
- [ ] The spawn lies outside every cluster ring, stage and mirror zone [INFERENCE].
- [ ] Exits are ≥ 2 m wide, lit, and inside the central 60° of the spawn view [INFERENCE; Meta Horizon Onboarding].
- [ ] At spawn: mirrors and video off; no loud AudioSource range reaching it [VRChat Labs Tips], [VRChat Spatial Audio Source].
- [ ] ≥ 45 FPS at spawn with a single VR user, tested in the client [VRChat Labs Tips].
- [ ] An information surface or poster wall at or near spawn [VRChat Wiki Black Cat], [VRChat Wiki Great Pug].
- [ ] No forced motion, strobe or pitch-black at spawn [INFERENCE from Meta 2025 Locomotion Environments].
- [ ] The arrival path avoids cluster centres and stages [VRCreators 2026], [INFERENCE].

### 6.2 Social-layout checklist (per world)

- [ ] Floor m² ÷ Recommended Capacity is 8–14, and ≥ 4 at Maximum (Section 4).
- [ ] Conversation zones ≥ ⌈N/4⌉ + 1; mostly 3–5 seats; ≤ 1–2 big clusters.
- [ ] Seat yaw within ≤ 25° of the cluster centre; spacing 0.6–3.2 m; a ≥ 1 m ring behind seats.
- [ ] Cluster centres ≥ 6 m apart in shared rooms, or separated by walls plus audio zones.
- [ ] ≥ 1 quiet zone, either ≥ 15 m from loud sources or in an audio zone; ≥ 1 loud or event zone; thresholds between them.
- [ ] Mirror zone at an edge, facing outward, off by default; ≤ 1 mirror per room.
- [ ] Each cluster has a focal object; each zone has a landmark; ≥ 1 overlook per main room; ≥ 1 seat per cluster sees the entry.
- [ ] Clear height ≥ 2.3 m over paths, ≥ 4 m in halls and at spawn, ≥ 2.4 m at door heads; sightline obstacles ≤ 1.0 m.
- [ ] No ladders, spiral stairs or jump-only access; ramps ≤ 15°; main corridors ≥ 2.5 m.
- [ ] Social core within ~50 m; every social room ≤ 30 m from the hub.
- [ ] ≥ 3 activity resources, ≥ 1 secret, ≥ 1 photo spot, ≥ 1 event-capable focal area.
- [ ] Seats ≥ 0.6 × Recommended Capacity.
- [ ] Not a single box: ≥ 3 distinguishable spaces.

(All thresholds in 6.2 are the [INFERENCE] defaults from Sections 3–4, each grounded in the sources cited there.)

### 6.3 How to measure from scene data [INFERENCE]

Run these via the Unity MCP `execute_code` tool.

1. **Floor area:** sum the XZ area of walkable floor colliders in the social rooms, or the baked NavMesh area. Divide by capacity.
2. **Spawn checks:** for each `VRC_SceneDescriptor.spawns[i]`:
   - `OverlapSphere(pos + up*1, 3)` for the clear disc;
   - an upward ray of 4 m for clear height;
   - a forward ray from the reference eye height (default 1.2 m), 3 m long;
   - line of sight to the hub;
   - a downward ray ≤ 0.3 m to the floor.
3. **Clusters:** group seats (by parent, or by a 3 m proximity threshold). For each cluster, record its centre, radius, seat-yaw error, pairwise distances and nearest-neighbour cluster distance.
4. **Clearance grid:** upward rays on a 1 m grid over walkable floor. Flag < 2.3 m on paths and < 4 m at spawn.
5. **Audio:** list `AudioSource` and `VRC_SpatialAudioSource` ranges and positions; intersect them with quiet-zone bounds.
6. **Mirrors:** list each mirror's active state, facing relative to the world centre, and the count per room.
7. **Screenshots:**
   - from each spawn at the reference eye height (default 1.2 m), facing forward;
   - a top-down orthographic view of each floor;
   - one shot per cluster from a seat at seated eye height (≈1.1 m full-size, ≈0.9 m at the 1.2 m default).

---

## 7. Confidence notes

- **VRChat creator docs** were read from the official `vrchat-community/creator-docs` GitHub source; creators.vrchat.com returned HTTP 403 to the fetcher.
- **VRChat wiki pages** were read via `index.php?action=raw`. The Mirrors page carries the wiki's "Official" notice; the Black Cat and Great Pug pages are marked community-written.
- **ClientSim capsule values** are the simulator's settings, not a statement about the live client.
- **Rec Room guidance** was read from recroom.network, which labels itself "a community tribute to Rec Room built by Studio 87" and hosts copies of the creator-hub pages (dated May 17, 2024). The official rec.net and blog pages were not readable (HTTP 401), so I cite the tribute copy.
- **Academic results** come from Mozilla Hubs and ENGAGE studies with small samples (24–104 participants): directionally strong, numerically approximate.
- **No Resonite layout-specific guidance was read**, so none is cited.
- **Dropped:** building-code occupant-load factors (IBC). The ICC page was captcha-blocked, so no IBC numbers are used.
- **Tuning:** all [INFERENCE] numbers are defaults for the architect to propose and the reviewer to check. Tune them per brief: an intimate home can be denser, and an event world needs a separately sized hall.

---

## Sources

Source keys in this file resolve in [SOURCES.md](../../SOURCES.md).

# Information gathering (A.2) and the design rounds (A.3–A.4)

Goal: enough context that phases B–D never have to ask. **There is no fixed interview.** You work
from whatever the user supplies — a description, a design doc, reference images, an existing
`WORLD.md` — extract every fact on the checklist below from it, and ask only about what is missing
or ambiguous. The concept rounds that follow (shell layouts with concept art, then style rounds) turn the brief into geometry and images the user picks
and approves, and end in the **Design Lock** (pipeline skill "Design Lock").

## How to gather

1. **Read everything the user supplied first**, and never ask what you can read from the project
   (an existing WORLD.md, the project's AGENTS.md, owned packages on disk).
2. **Fill the checklist** below: for every fact, write your extracted or inferred value with its
   source (`user`, `doc`, `reference image`, `inferred`, `default`) and a confidence level.
3. **Ask only about gaps**: facts that are missing, ambiguous or low-confidence, plus the ones
   marked **always confirm** when the material doesn't state them. Ask in **batches with options and
   a recommended default** (your host's multiple-choice question tool if it has one, 2–5 options
   each, plus "Other"); one batch per checklist group at most, the smallest number of batches you
   can. One good reference picture answers several questions: infer from it before asking.
4. **Show the inferred values** in the closing summary so the user can correct them.

## Checklist of required facts

### Purpose and people

- **World kind** (always confirm unless the material says): a **living space** (a place people live
  in and hang out in: archetype-based real architecture; a private VIP island is optional, off unless the brief asks for it) or an **event
  world** (built for one community event's function: a talk, a race, an auction; function-first,
  anything goes, game and level design allowed, no VIP area unless asked). world-architect reads
  this first.
- **Event type and function** (event worlds): the type (talk, race, auction, party, show, game
  night, ...) and what happens in what order, who takes part and who watches, how many of each,
  and how people move between phases. For an event world the archetype facts become optional, and
  game and level-design references (tracks, arenas, stages, game screenshots) are welcome.
- **Purpose**: hangout / party-club / roleplay / game / showcase-exploration / chill-sleep / event
  venue. Drives everything else.
- **Capacity**, typical and peak (1–4 / 5–12 / 13–30 / 30–80). Sizes floor area and the number of
  conversation zones (spatial-design capacity table).
- **Space archetypes and people each** (spatial-design §1): **A1 intimate retreat** (2–8 people:
  bedroom, nook, cozy apartment, a place to cuddle or lie together; the default, most worlds are
  this), A2 social home or hangout (8–20, a house with several rooms), A3 gathering venue (bar, club,
  party floor, 20–80+), A4 audience space (cinema, stage), A5 scenic or walk-and-talk (garden,
  promenade). Mixes are normal (a home with bedrooms; a venue with quiet booths). Drives sizes,
  light, seating and sound.
- **Cuddling or lying close** (always confirm unless stated): yes (the usual answer for A1) sets the
  runtime near clip to 0.001–0.01 m so faces and hands aren't cut away, keeps cuddle spaces within
  256 m of the origin, and adds a near/far Udon script (`.omp/skills/clip-planes/SKILL.md`). It also means the
  lie-on furniture gets lie-down colliders behind the world toggle (pipeline skill "Lie-down
  colliders").
- **Reference eye height** (always confirm): the group's typical avatar eye height. Offer **1.3 m**
  (avatar about 1.4 m) as the default; full-size groups use 1.6 m. It sets the shell scale (eye ÷ 1.6,
  clamped at the collision minimums; spatial-design §5.9); size the world for the wrong height and it
  feels empty or cramped.
- **Platform** (always confirm unless the material says): **PC is the primary target**; every stage
  builds, reviews and ships the PC world first. An **Android version** (Meta Quest, Android phones
  and tablets) is an optional secondary target, ported from the same scene after D.3; iOS gets its
  own build or loads the Android one (VRChat's experimental fallback). Ask: Android yes / later / no
  (default: later), and for yes, whether its build may use `VRChat/Mobile` shaders (a shader change
  the user approves). Record `Platform: PC; Android: …; iOS: Android fallback / own build / no` in
  WORLD.md's Brief. A yes adds the cheap-port design choices from A.3 on and the port after D.3
  (`.omp/skills/vrchat-android-worlds/SKILL.md`).

### Place and mood

- **Setting / theme** in one line, plus any reference worlds, games, films or photos.
- **Mood**: cozy / grand / mysterious / energetic / serene / eerie; plus time of day and weather
  (rain, night, golden hour).
- **Darkness level** for interiors: bright and airy / balanced / dim and cozy (AWDK default for cozy
  and night: darker than instinct).
- **Realism**: photoreal / stylised-realistic / low-poly / toon. Sets the asset and shader pool.
- **Scale and shape of the place**: single room / house or apartment / large building / outdoor area /
  multi-area; the indoor-outdoor mix, and how far the view out reaches (city skyline, mountains,
  sea): this sets the far clip, fog and whether distant scenery is baked into the skybox.

### Style (these seed the A.3 concept art and style rounds)

Each fact becomes the prompt seed of a board, so get it concretely:

- **Palette**: warm / cool / neutral; saturated or muted; colours they love and colours to avoid;
  one accent colour or none.
- **Materials**: dominant floor and wall materials per kind of space (wood, stone, plaster, concrete,
  tile, carpet, fabric); new and crisp or worn and lived-in; window frames, trims and metal finish
  (brass, black steel, chrome, wood).
- **Lighting and time of day**: time of day and weather, the light sources they picture (lamps,
  candles, fairy lights, neon, daylight through windows, a fire), warm or cool light, and how dark.
- **Era and place**: a real place, decade or culture the world belongs to (1970s Tokyo apartment,
  Nordic cabin, Art Deco hotel).
- **Exterior**: what people see from outside or on arrival, if anything (a façade, a garden, a
  floating island, nothing: interior only).
- **Furnishing feel**: sparse or full; built-in or loose furniture; low (floor cushions, futons) or
  standard height; one signature piece they want (a huge sofa, a canopy bed, a bar).

### Content

- **Must-have spaces and features**: video/cinema, bar, pool/jacuzzi, games (pool table,
  cards), dance floor, beds, private rooms (built as teleport islands), quiet room, outdoor terrace,
  photo spots.
- **Interactions list** (built in C.2): video player, light toggles, pickups (only if
  requested), seats (**never added unless the user explicitly asks**), music. The lie-down collider
  toggle is added automatically wherever there is lie-on furniture.
- No mirror is asked about or added by default (VRChat has personal mirrors); a mirror appears only
  as a real object in a room type that has one (bathroom, gym, dance or dressing room).
- **Dislikes**: things they don't want, past worlds they didn't enjoy, and why.
- **Assets and tools**: owned packs they want used; paid tools available (Bakery?).

### Reference images (accepted at any time)

Invite **reference pictures** and accept them throughout the whole pipeline: screenshots of worlds
or games they like, photos of real places, mood boards, palettes, a specific chair or lamp, or
things they **don't** want. Pasted images, file paths and URLs all count. For each image:

1. Save a copy to `<project>/Design/references/NN_<slug>.<ext>` (download URLs; never hotlink). Note
   the source URL or "user-supplied" for credit. Shared images may be copyrighted: use them as
   reference only, never as textures or assets in the world.
2. Infer, then confirm, **what it is a reference for**, one or more tags (the same list as WORLD.md's
   References table): `mood`, `lighting`, `palette`, `materials`, `massing` (building form,
   architecture), `layout`, `object` (a specific prop or piece), `sky` (atmosphere, sky, weather),
   `avoid`. "I like the light in this, not the building" is the most common correction.
3. Write a one-line caption of what you take from it, and show the captions in the closing summary
   so the user can correct your reading.

Record them in WORLD.md's **References** table. Downstream use is mandatory: concept mood images
and boards are generated *from* the tagged references, `world-architect` reads `massing`/`layout`
refs, `asset-finder` searches `object` refs first, and `avoid` refs become explicit "do not" lines
in the brief.

**Images are feel references, never blueprints**, user-supplied ones included: they set mood,
palette, materials, lighting character and density. A floor-plan sketch or layout photo informs
the B.1 floor-plan program as a stated wish, but geometry is decided by the shell layout, the floor plan, the greybox and
spatial-design (review-protocol "Images are feel references").

### Involvement (always confirm, last)

Offer the presets from the pipeline skill: **Design lock, then autopilot** (default: they answer the
gaps, pick the concept (layout + look) and every style round, approve the lock once; the build then runs to the
upload decision, which is always theirs), **Every step** (also a checkpoint after every stage,
including a review of the floor plan and greybox; used for trials and calibration), **Custom** (the
default plus the stops they name). Say plainly that they can change it later ("just go from here" /
"stop and ask me before X").

## Suggest, don't only ask

Once the purpose and mood are clear, offer **2–3 short twists** that fit the brief and make the
world more memorable (a landmark, a view, a signature room, an unusual vertical feature). Let the
user accept, reject or mix. The aim is a world with an identity, not a generic version of the theme.

## Closing summary (gate for A.2)

Write a one-paragraph pitch plus the checklist as WORLD.md's Brief table (each value with its
source), show it with the inferred values marked, and get an explicit OK. Then run A.3.

## Concept rounds (A.3)

**Round 1: concepts, two tracks.** The style track and the layout track are separate; the user
picks on each.

- **Style track (text → image only).** Text-only `image-gen` concept art from the brief and tagged
  references, generated in parallel; short subject prompts with the style line first and last.
  Images show the lived-in, furnished world, never empty spaces. Refining changes the prompt
  text; a picked image is never passed as input. No reviewer.
- **Layout track (3D shell blockouts).** world-architect blocks out 2–3 divergent shell layouts
  in a scratch area of the open scene (massing only: building and tree volumes, multi-level house
  volumes, bridges and paths, ground/water plane, sky; no interiors, no furniture) and captures
  fixed shots per layout (eye-height arrival view at the reference eye height, an overview, one
  intimate view) as plain Unity captures, no paint-overs. layout-reviewer ranks and scores the
  shell layouts. A text image never defines geometry: if the user wants a layout like a text
  image, world-architect builds a matching blockout and shows its captures.

Each concept carries a pitch in words: the idea and feel, signature feature, how it feels to
arrive and settle, strengths and tradeoffs. Images go to one folder per generation,
`Design/concepts/genNN-<route>/` (`<letter>_<view>.png`);
prompts and pitches go to `Design/_prompts/genNN-<route>/` and are for the agents only. Show the user
the images and summarise the pitches in chat, with layout-reviewer's scores with their reasons and
your recommendation; the user picks the look and the layout (or picks with changes, which starts
another round).

**Style rounds on the picked look.** A handful of `image-edit` images conditioned on
the approved lock images: palette, materials, lighting and time of day. **Never a picture per room.** No
reviewer: the user picks directly. world-architect generates them with the `image-edit` tool (`image-gen` for text-only images) through
`python .omp/scripts/tool.py` (`.omp/docs/tools.md`); run `tool.py check image-gen image-edit` once per session. Per round:

1. **Prompt** one file per image in `Design/_prompts/genNN-style/<letter>_<view>.prompt.txt` (images to `Design/concepts/genNN-style/`): what the image fixes
   (palette, materials, light, overall view), the brief's mood, realism and darkness, the style facts
   for it, and the role of every reference image passed (`--reference`): tagged references for their
   tag only, and **every lock image already approved** as the style it must stay
   consistent with.
2. **Images**: where an item offers alternatives, they differ on its main axis (a warm and a cool
   palette, a stone and a timber material set), not near-duplicates; `--quality medium`, landscape.
   Inspect each image before showing it, and caption it in one line.
3. **Ask**: which ones; what exactly they like in each (this becomes the `caption` and `feel`); what
   to change; what in it does **not** bind (`free`: positions, proportions, layout, scale). "Pick with
   changes" or "none" starts the next round, which changes only what their feedback names.
4. **Approve**: when the user says the set is right, it goes to `Design/lock/` (pipeline skill
   "Saving").

Sheets: **palette** (swatches with names and hex values next to a view of the world in those
colours), **materials** (a swatch sheet of every surface with its name, next to a view of the
world), **lighting and time of day** (the signature view at the chosen time of day and darkness,
the light sources visible).

## A.4 Design Lock

Show the lock sheet (pipeline skill "Design Lock"): the brief summary with the interactions list,
the lock images with their `feel` lines (style track), the `SHELL_PICK` captures (layout track), and the involvement preset. The
user approves it once; record the date and their exact words in WORLD.md Decisions. After that,
agents build to the end; a lock item changes only when the user reopens it.

## Defaults when the user says "you decide"

| Field | Default |
|---|---|
| World kind | living space (event world only when the material names an event) |
| Archetypes | A1 intimate retreat (with A2 home if several rooms are asked for) |
| Cuddling / lying close | yes: runtime near 0.001–0.003 m; lie-down colliders on lie-on furniture |
| Capacity | 2–8 for A1; 8–16 for A2 |
| Reference avatar | eye 1.3 m (avatar about 1.4 m); full-size groups 1.6 m |
| Platform | PC; Android: later (offered as a port after D.3) |
| Realism | stylised-realistic |
| Interior darkness | balanced; cozy/night themes → dim |
| Interactions | one video player if a lounge exists, light toggles, the lie-down toggle (no mirror) |
| Seats / pickups | none |
| Involvement | Design lock, then autopilot |


## Lock-gap questions

Each lock gap a world or trial logged becomes a line here at its D.4 retro, and information
gathering checks it from then on (in the checklist group it belongs to). Format:
`- <question> (group: palette / materials / lighting / exterior / furnishing / content) — from <world or trial>, <date>`

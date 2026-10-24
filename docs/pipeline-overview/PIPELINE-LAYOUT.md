# Pipeline layout: agreed design (draft for review)

Status: **approved and applied 2026-10-10** (commit c8039a7): `skills/world-pipeline`, the agents,
the information-gathering guide, the WORLD template, the trial skill and WorldAudit 0.2.0 follow this
layout. The HTML/PDF in this folder visualise it.

## Goal

Thorough information gathering plus the concept (text → image style art and style rounds, and
shell-layout blockouts shown as plain captures) lock the world's style, shells, purpose and targets. After that, **agents
build the whole world automatically to the end**. The user decides only the concept and style (up
front) and the final upload. Trial runs calibrate the reviewers until the user agrees with them,
so no stops or corrections are needed.

## Four phases

### A · Concept: the user decides
- **A.1 Setup**: project, MCP, packages, WORLD.md.
- **A.2 Information gathering**: the model collects what it needs from whatever the user
  supplies (a description, a design doc, reference images, an existing WORLD.md). **There is no
  fixed interview**: the model asks follow-up questions only for what's missing or ambiguous. It
  needs:
  - world kind (living space / event world) and the event function;
  - purpose; capacity; reference eye height (default 1.3 m); cuddling → near clip;
  - space archetypes; mood;
  - style: palette, materials, lighting and time of day, era/place, exterior, furnishing feel;
  - reference images, saved and tagged.
- **A.3 Concept: style track + layout track**, decided separately by the user:
  - **Style track (text → image only)**: text-to-image concept art from the brief and
    tagged references, showing the lived-in, furnished world (never empty spaces); refined by
    changing the prompt text. No reviewer; the user picks.
  - **Layout track**: world-architect blocks out 2–3 shell layouts in the open Unity scene
    (massing only: building and tree volumes, multi-level houses, bridges and paths, ground/water,
    sky; no interiors, no furniture) and captures fixed shots (eye-height arrival, overview, one
    intimate view) as plain captures, no paint-overs. layout-reviewer ranks; the user's pick is
    `SHELL_PICK`. A text image never defines geometry; a layout like it is built and captured.
  - Style rounds then produce palette, materials and lighting sheets text → image, conditioned
    on the lock images, until approved.
- **A.4 Design Lock**: the brief, the lock images (style track) and the `SHELL_PICK` captures
  (layout track), approved once. This is the user's last decision before final sign-off.

### B · Blueprint: agents decide (one optional user review, on in trials)
- **B.1 Floor plan (2D, zoning only)**: inside the locked shells (`SHELL_PICK`): which room is which.
  Room purposes, archetypes, rough sizes, intimacy gradient, adjacencies, public → private zones,
  door positions, circulation, rough furniture zones; variants on different plan organisations.
  **No furniture in the 2D plan.**
- **B.2 Greybox (= massing, with rough furniture zones)**:
  - 3–4 variant blockouts in 3D: building volumes, walls, heights, roof forms and level
    changes, **plus at most rough furniture zones**: flat labelled floor patches ("seating for
    5", "bed"), never true-to-size furniture placeholders. No small props or wall decoration.
  - layout-reviewer ranks and scores them in 3D from eye height. **One variant is picked** and
    refined in 3D; it is the blueprint for C.
  - **Not playable**: no colliders, spawn, stair ramps, teleport doors or clip planes yet. Those
    need the real objects and are built in C.2.
  - No furniture transforms are exported. Once the user confirms a 3D blockout, changes happen
    in 3D, never in new 2D plan rounds.
- Optional user review of the plan and greybox: off by default, on in trials.

### C · Build: the main build loop
- **C.1 Build-out**, the main loop, runs area by area. Each pass does what the area needs:
  - **shell finish**: real walls, floors, roofs, windows, doors, trims and materials replacing the greybox geometry;
  - **furniture, placed in 3D**: real models sourced and placed directly in the room, composed
    by the seating and layout rules (replace whole groups, nothing alone in open floor, door
    zones clear, group spacing), judged in 3D by dressing-reviewer; the plan JSON furniture list
    and the prop schedule are written afterwards from what was placed;
  - **dressing**: secondary pieces and decor, added by rule.
  - Assets are sourced as each pass needs them; there is no separate asset stage.
- **C.2 Interactions and playability**, once the real objects exist:
  - **Colliders**: walls and floors; big objects people mustn't walk through (e.g. trees,
    large solid masses).
  - **Furniture colliders for lying down**: beds and couches (and other lie-on furniture such
    as cuddle platforms) get colliders that are **off by default** and switched on by the world's
    **furniture-collider toggle**. Non-full-body players turn them on so their avatar can lie on
    the bed or couch surface. Full-body players leave them off, because they set their own height
    and pose freely and a collider would get in the way. These colliders follow the furniture's
    top surface (seat and mattress height), and there is one toggle for the whole world.
  - This replaces the old blanket "no colliders on furniture" rule for beds and couches only. All
    other props still get no colliders.
  - Stair ramps, spawn, walk test.
  - **Udon scripting**: clickable teleport doors on the real doors, teleport islands, toggles
    (including the furniture-collider toggle), video, pickups, the VIP gate. No world mirrors
    (VRChat has personal mirrors); only real ones in bathrooms, gyms or dance rooms.
  - Clip planes and fog.
- C ends when every area has SHIP IT with nothing left on its plan.

### D · Finish: loops back to C
- **D.1 Lighting**: draft bake → mood check against the boards → final bake → reflection probes
  immediately.
- **D.2 Performance**: measure, attribute, reversible fixes.
- **D.3 Ship**: sweep the helpers, build and test → **the user uploads** (final sign-off).
- **D.4 Retro**: lessons, and lock gaps → new information-gathering questions.
- **Any needed change goes back to C** (a lighting or perf review exposes a build issue, or the
  user wants a change). After the fix, the affected D steps are redone: rebake the area, rebake
  the probes, re-measure, rerun the final review.

## Plan → Build → Review loop (every build stage)
1. **Plan**: a short pass plan (area, goal, changes, assets, expected review criteria), logged.
2. **Build**: execute that plan only.
3. **Review**: the stage reviewer's verdict, **with a score out of 10** and the reasons for it.
   Its findings plus the area's unfinished work become the next pass plan.

The loop ends on SHIP IT with nothing left on the plan. Three rounds with no improvement on the
same finding → change approach or report blocked. Nobody waives a finding.

## Reviewers (no separate style reviewer)
The style reviewer is dropped; its work is split:
- **A.3**: world-architect pitches each concept; layout-reviewer ranks only the shell geometry;
  the user is the style judge.
- **C**: dressing-reviewer judges "matches the boards" (palette, materials, density, mood) as a
  separate criterion and scores **style** and **build quality** separately, so trials can show
  which half the user disagrees with. It also decides lock gaps.
- **D.1**: final-reviewer checks the lighting mood against the boards.

Reviewers: layout-reviewer (A.3 shell layouts, B), dressing-reviewer (C), final-reviewer (D).

## Reviewer scores
Every review (and every ranking of variants) gives a **score out of 10** per item, alongside the
verdict and the reasons (dressing-reviewer: separate style and build-quality scores). Scores make rankings comparable, show progress across passes, and let
trials compare the user's own score with the reviewer's. The score/verdict mapping is defined when
the reviewers are designed.

## Images are feel references, never blueprints
AI images don't translate into 3D: perspective and parallax lines don't line up, scale is
ambiguous and layouts are impossible. Builders and reviewers match **mood, palette, materials,
lighting character and density** from images, never positions, proportions or layout. Geometry
is judged only against the approved greybox and spatial-design.

## Lock gaps
A stylistic decision during B–D that the lock doesn't cover: dressing-reviewer decides it
provisionally against the boards, logs it, and lists it in the upload report. At the retro it becomes
a new information-gathering question.

## Involvement presets
| Preset | User decides |
|---|---|
| **Design lock, then autopilot** (default) | information gathering, concept (layout + look), style rounds → lock; final upload |
| **Every step** (trials and calibration) | default + a checkpoint after every stage, incl. the Blueprint review |
| **Custom** | default + named stops |

## Trials
- A checkpoint after every stage. Each checkpoint logs every decision, failed attempt and reviewer
  verdict, and every pass with its reasons, with screenshots (`Trial/log.jsonl` → HTML/PDF report
  via `skills/pipeline-trial/scripts/trial_report.py`).
- The user marks each reviewer call agree or disagree (and may give their own score out of 10),
  says what to change and what worked well. Every disagreement becomes a fix.
- **Calibrated** = at least 95 % agreement with no lock gaps for 3 trials in a row; then the
  pipeline runs unattended.
- Trial worlds: the user defines them.

## World kinds and the VIP room
- **Living space** (hangout or home): archetype-based real architecture; a VIP supporter
  teleport room on an island is optional (off unless the brief asks for it).
- **Event world** (e.g. a talk event, a race, an RP auction): function-first, anything goes,
  game/level design allowed, no VIP room unless requested.
- Both are decided at the Concept phase by world-architect.

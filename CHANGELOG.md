# Changelog

Semantic versioning, one git tag `vX.Y.Z` per release; the current version is in `VERSION`.

## 0.3.0 — 2026-11-05

### User decisions and picked art (new)

Agents forgot picked concept art and earlier user decisions; in one world a skill default
(pickups with gravity) silently undid the user's "fumos should not be affected by gravity".

- **Decision database per project** (`<project>/STEER.jsonl`, written only through
  `scripts/steer.py`): every user decision, pick and rejection in the user's exact words, with a
  timestamp and labels. Labels: `affects` (world part, from `steer_parts.txt`), `aspect` (size,
  layout, design, style, materials, lighting, behaviour, audio, script, performance, process; new
  `templates/steer_aspects.txt`), `targets` (objects, scripts, scene paths, globs) and `aliases`.
  The newest record on a topic, by timestamp, holds; backfilled old records never override newer ones.
- **Picked art is kept:** `steer.py pick` copies liked images to `<project>/Design/picks/`,
  `pick --reject` to `Design/picks/rejected/`. Only an explicit like is a pick, only an explicit
  dislike a rejection; uncommented art is no signal.
- **Generated digest** `DECISIONS.md` (+ `DECISIONS.json`, `STEER.md`): picked and rejected art with
  absolute paths, the design lock, decisions in force by part.
- **Soft search:** `steer.py find --like "<free text>"` ranks by stemmed words (BM25), meaning (optional
  local embeddings, `pip install fastembed`) and alias/target hits (`scripts/steer_rank.py`). New
  commands `tag` (labels and aliases on existing records) and `serve` (ranking server).
- **Hard rule 12:** decisions beat workspace defaults, skill defaults and briefs. The orchestrator
  holds them, records new ones on the spot and feeds the relevant ones into every subagent brief
  under "## User decisions (binding)". New `AGENTS.md` section "User decisions and picked art".
- **`world-decisions` omp extension** (`extensions/world-decisions/`, main session only): injects the
  relevant decisions when a project comes up, appends ranked decisions to each `task` brief, and
  reminds the orchestrator when a tool call names a decision's target or alias.
- All nine agents take their decisions from the brief; for reviewers, a contradiction is a blocker.
  Pipeline skill, review protocol, WORLD template and `bootstrap.md` / `hosts.md` updated; the
  fumo skill's gravity-on pickup is now only a default under the project's decision.
  `unity-world.gitignore` ignores the embedding cache `STEER.emb.npz`.

### Rules

- **Hard rule 10: code builds boxes only.** Every other shape comes from asset-finder, then
  blender-modeler, then Tripo; a faceted lathe, tube or lattice built in Unity is a review blocker.
- **Hard rule 11: test bakes are QUICK and capped at 10 minutes.** Re-bakes are allowed; only the
  final bake the user asks for may be slow. Cancel procedure in the Bakery skill; mesh-light count is
  the quick-bake lever.
- **Reachability:** everything that looks walkable is reachable, with ≥ 2 connections per level pair,
  proven by a flood-fill check.
- Traceability (every visible element traces to a picked image), interior illumination coverage, and
  the far-ring skybox as a one-off render source.

### Skills and agents

- blender-modeler: soft goods (pillows, cloth, bedding) are out of scope; face-orientation check per
  connected part before export.
- unity-mcp-scripting: never render through `PreviewRenderUtility` (fatal LightmapSettings modal).
- Light Volumes lessons: crop volumes to rooms, Shadows lift 0, island bits in LV Manager bitmasks.
- lowpoly-tree-generation: composed single-leaf atlas for plate-like leaves, hanging/ledge recipe,
  opt-in bark fixes in `tree_family_build` (collar, stride, blunt, relax).

## 0.2.1 — 2026-11-03

- The 0.2.0 notes below now cover every change since 0.1.0, not only the last push.

## 0.2.0 — 2026-11-03

First versioned release. It covers everything since the initial public release (tagged `v0.1.0`,
2026-10-16).

### Kit structure and generation tools

- The kit is named **Agentic VRChat World Development Kit (AWDK)**.
- **Knowledge notes are compiled into skills.** Each skill has a lessons checklist (one line per
  note, no links). Sources live only in `SOURCES.md` and `CREDITS.md`, and `check_kit.py` enforces
  both. A knowledge audit merged duplicate notes and fixed about 25 stale or contradicting ones.
- **Generation tools have fixed names** (`image-gen`, `image-edit`, `image-to-3d`, `blender`),
  all called through `scripts/tool.py`. Each user chooses the backends: paid services first, free
  local ones as fallbacks.
  - ComfyUI backend: starts automatically, takes numbered reference inputs, and ships Qwen-Image
    text-to-image and edit workflows. A TRELLIS.2 wrapper is included too.
  - `tool.py blender` has a machine-wide limit on parallel Blender processes (default 2) and on
    threads, and runs Blender at below-normal priority.
- New docs: a beginner guide, project creation by the agent with ALCOM registration, a package
  update routine, and a recipe for the modal dialogs on a project's first open.
- Knowledge was extracted from long-running agent transcripts: 38 new notes, plus script
  templates (GroundCells, LightmappedProbes, perf_tour, bundle_size, marker_profile).

### Scale and pipeline

- **One scale for every world:** the reference person is 1.4 m tall (eye height 1.3 m), and
  everything new is ×0.8 of real-world size (furniture, props, pickups, outdoor features, trees).
  Collision minimums never shrink. Hard rule 8.
- **Pipeline stages redrawn:** B.1 is zoning only, and B.2 is massing plus rough furniture zones.
  In C.1, furniture is placed in 3D and recorded from the scene.
  - Hard rule 9: once the user confirms a 3D blockout, no more 2D plan rounds.
  - New seating and layout rules.
- **New world defaults (hard rule 2):**
  - No barrier colliders: no invisible walls, shore or sea gates, and nothing on fences or
    railings.
  - A fitted capsule collider on every tree trunk.
  - Every building can be entered from the path that leads to it.
  - Jumping is on in every world (`SetJumpImpulse(3)`), using the shipped
    `PlayerMovementSettings` template. A new `NO_JUMPING` check in WorldAudit catches worlds
    without it.
- **Paths never end in nothing.** This is a builder step, and the reviewer raises a should-fix
  when a path does.
- **NAV empties** for each floor, site and room (EditorOnly), so agents can navigate the scene.
- **Progress log:** an append-only visual HTML log per world, with thumbnails embedded as data
  URIs. It records the user's steering quotes and keeps blog notes and drafts.

### Lighting and lightmaps

- **New `lightmap-allocation` skill:**
  - Which renderers are lightmapped, lit by Light Volumes, or dynamic.
  - Texel density, Scale In Lightmap and lightmap groups.
  - UV2 quality, with a measured pre-bake UV2 audit (adds a `negSO` column and a `NEG_SO` flag).
  - Post-bake allocation and near-reach checks.
- **VRC Light Volumes are the kit-wide default for everything not lightmapped.** Light probes are
  only a coarse fallback, and nothing static is lit by probes. Small props whose UV2 fails the
  audit may be lit by Light Volumes instead.
- **GLIM is the free lightmapper.** The skill now covers GLIM trial findings (black bounce from
  double-sided GI, skybox-only ambient, dialogs in scripted bakes) and Bakery traps (a stale
  `__ExportTerrain` breaks exports, the registry trap, negative chart rects at cm scale).
- New notes: unbaked Baked lights render as realtime, small flush wall fittings should be
  probe-lit, grass shadow casters print texel smudges.

### Reviewers

- `final-reviewer` was rewritten with DRAFT MOOD, FINAL and PERF REGRESSION modes. New checks:
  - A near-reach bake check on every new lightmapped piece.
  - A pass per object with lightmap-only renders, plus a check of merged pieces against the
    originals.
  - Parts of the same object that are lit differently.
  - A mandatory measured UV2 audit.
- `dressing-reviewer` gained a contact sweep per object, close-ups of fixtures, beds and counters,
  checks of the source config for copied models, material red flags, a measured mid-floor clearance
  check, and a backface check that looks into open objects.

### Performance

- **LODs:** levels are bounded by error, and switch distances are derived from that error. There is
  a billboard LOD3 tool per object, and `blender-optimizer` is limited to LOD0.
- `perf-optimizer` reduces textures selectively and never reduces a visible skybox.
- Ground cover built as a continuous density field: light weighting (open sun gets the densest
  grass), an exclusion map, an A/B test with shadow casting off, and the cost per clump.
- `bundle_size` refreshes the descriptor's DynamicMaterials before measuring (a stale list
  inflated one A/B by 26 MB).

### Trees (`lowpoly-tree-generation`)

- **Fuller crowns:** bigger cards with open, small-leaved sprays, and a full-crown standard checked
  by a fullness metric. Every leaf atlas cell must be an open spray, and `branch_atlas.py`
  SPRAYCHECK enforces it. Texture sheets are approved as PNGs before any build.
- **VR leaf shimmer fix:** A2C, a mip bias applied only far away, and a lower cutoff. The SoftCrown
  shader replaces FoliageCutout. Edge-on cards fade out, and the edge fade uses camera-relative
  positions so it no longer breaks into noise far from the origin. Wind is coherent, and small
  plants tremble sideways.
- **Mesh quality:**
  - Every card is snapped onto the bark mesh.
  - Base cones stay inside the parent tube.
  - Merging never leaves a child's bark floating.
  - Optional root flare with a closed skirt below ground.
  - New checkers: `bark_clash.py` (bark through bark, elbow sockets, socket rims, and a silhouette
    metric for trunks crossing on screen), `bare_limbs.py` and `tree_checks.py`.
- **Lightmaps:** a hand-built Lightmap UV (`lightmap_uv.py`) replaces Smart UV, with a bbox sizing
  model, texel margins and ribbon splitting. A note covers how transparent leaf quads starve the
  bark of lightmap space.
- **Far LODs** (`--lods`): levels set per tree, cards thinned by coverage, rosette fronds resampled.
  No impostors.
- **Many new opt-in builder keys** for new tree types: palms, bamboo, banyan with pillar and aerial
  roots, weeping, pagoda and umbrella crowns, hedges (hug and surface skin), vines, sag and wave.
  Each one leaves existing builds identical when off, verified by mesh hash.

### Other skills

- **New `fumo-plushie` skill:** character plush pickups end to end.
  - A studio recipe with grading, a review gate, an AO test, and lineup and close-up scripts.
  - Cycles renders on the GPU.
  - Smart UV with `transfer_bake.py`.
  - Plushies go on shelves, never on seats or beds.
- `image-to-3d-props`: Smart UV on every generated prop.
- `blender-modeler`: a self-check loop against the reference and an order for adding detail.
- `vrchat-world-thumbnail`: `title_render` with subtitle, credit and crop options, glow controls,
  and nature-theme fonts.
- `materials-shaders`: UV tiling set at the scale reference.
- Credits: unity-stylized-water (BSD-3), adapted as a tropical water shader.

### Concept art now binds what is in each area, not only its feel

Before, images set only mood, palette, materials, lighting and density. A structure pass could
ignore the per-area concept art and build every area from the same generic block kit, so
every floor came out the same. Now:

- **Images are content and feel references, not blueprints.** They decide *what is there*
  (structure and object types, silhouettes, signature pieces) as well as the feel. Exact positions,
  proportions and layout still come from the plan and greybox.
- **New WORLD.md section "Area references (binding per-area targets)"**: one row per area with its
  target image(s), signature pieces, the user's pick and the user's exact words. Every B.2, C.1 and D.1
  brief copies its row. Template updated.
- **Always build from concept art**: each area gets a blockout, captures from several angles,
  concept art over those captures, then a pick, all before the area is built.
- **Several concept variants per view.** The user picks. If the user leaves a pick open,
  `dressing-reviewer` decides it in a new **CONCEPT PICK** mode. The built area matches the image's
  style but is not a copy of it. Area folders get descriptive names.
- **Reviewers check content match and distinctness**: `layout-reviewer` (for structures beyond plain
  massing) and `dressing-reviewer` check that each area contains what its image shows and doesn't
  look like its neighbours.
- `dressing-reviewer` now reviews whatever a C pass placed (inner buildings, machines, set pieces,
  shell finish, furniture, dressing), not only furniture passes.
- `asset-finder` and `blender-modeler` match the picked image's object type and silhouette.
- New knowledge note `concept-art-binds-content-not-just-feel.md` (the failure where every floor
  came out identical) and a matching line in `lessons-verification.md`.

### Spatial design: structures inside halls

- **No outdoor roofs on buildings that stand indoors** (no pitched or gabled roofs, pediments or eaves).
  The top of such a structure is a usable area (terrace, garden, deck, lookout, catwalk), or the
  structure is built into the ceiling.
- In tall halls, tie the big structures to the floor, the ceiling and the walls, and join neighbouring
  structures with bridges.
- No outdoor building types indoors, and nothing that needs open sky.

### Movement between floors

- **Stairs come first:** every floor can be reached on foot, and big worlds get at least 2 walking routes
  between each pair of main floors.
- **VR stair comfort** (spatial-design §5.6): long straight flights, no spiral stairs, no short zigzags.
- **Teleport lifts** have a button per floor. **Ladders are click-to-teleport only**: Interact at one end
  takes you to the other end. Players never climb them.
- New template `templates/udon/TeleportDoor.cs.txt`: one local Interact → `TeleportTo` script shared by
  doors, lifts and ladders (3 m interaction distance, optional sound effect). Its clickable part has a
  trigger collider, which never blocks movement.
- Rules in `world-builder` and the world-pipeline C.2 row.

### Agent models

- `world-architect`, `layout-reviewer`, `dressing-reviewer` and `final-reviewer` run on Opus.
- `perf-optimizer` and `blender-optimizer` run on Sonnet.

### Docs

- `review-protocol.md`, `intake.md`, `PIPELINE-LAYOUT.md` and `pipeline.html` updated to match.

# Unity workspace guidance

This file is also the entry point of the **Agentic VRChat World Development Kit (AWDK)**, which lives in
`.omp/` (skills, agents, knowledge notes, docs, templates, the `com.awdk.agenttools` Unity package).
Paths written as `.omp/...` resolve from the workspace root; Markdown links resolve from this file.
New machine? Follow [`.omp/docs/bootstrap.md`](docs/bootstrap.md). New world? [`.omp/docs/new-world.md`](docs/new-world.md).
User says "make me a world" or the project has a `WORLD.md`? Load the world-pipeline skill
([`.omp/skills/world-pipeline/SKILL.md`](skills/world-pipeline/SKILL.md)) and act as the orchestrator.

Stage- and task-specific rules live with the agent or skill that does that stage; the routing table
below finds each in one hop.

**Personal layer.** `.omp/local/` holds this machine's owner setup and is never committed to the kit:
read `.omp/local/AGENTS.local.md` now if it exists (it overrides defaults here); settings such as
paths and the asset library are in `.omp/local/config.md`, the backends behind the generation
tools in `.omp/local/tools.json`; personal notes in `.omp/local/notes/`, personal skills in
`.omp/local/skills/`. Anything specific to one person or machine (names, absolute paths, accounts,
owned packs, hardware) goes there, never in the shared files; the pre-commit leak check enforces
this. Template: `.omp/local.example/`.

**Generation tools have fixed names.** Skills and agents call `image-gen`, `image-edit`,
`image-to-3d` and `blender` through `python .omp/scripts/tool.py <tool> ...`, never a product.
Each user picks what runs behind each name (paid services first, free local ones as fallbacks);
guide and setup: [`.omp/docs/tools.md`](docs/tools.md). Exit code 3 hands the step to you or the
user, exit code 4 means ask the user to approve the spend.

## Scope and prerequisites

- The workspace contains independent Unity projects, not a shared project or build; use each project's own repository.
- This `.omp/AGENTS.md` loads from the workspace and its project subfolders. Before editing a project, read its own `AGENTS.md`, plus `WORLD.md`, `DESIGN.md` and `TASKS.md` when present; project context is not loaded merely because this file names it.
- Target: **Unity 2022.3.22f1**, VRChat Creator Companion (VCC / VPM), VRChat Worlds SDK, UdonSharp, **Built-in Render Pipeline only** (URP/HDRP materials import magenta), PC primary; an Android/iOS version is an optional secondary port ([`.omp/skills/vrchat-android-worlds/SKILL.md`](skills/vrchat-android-worlds/SKILL.md)). Optional: Bakery, Blender. Dependencies include `Packages/vpm-manifest.json`; change packages through VCC/ALCOM/vrc-get, never by hand. Editor checks run through the `com.awdk.agenttools` package (`.omp/unity-package/`; [`.omp/docs/unity-tools.md`](docs/unity-tools.md)). Driving the Editor from an agent: [`.omp/skills/unity-mcp-scripting/SKILL.md`](skills/unity-mcp-scripting/SKILL.md).
- Prioritize world creation. The owner's project list and priorities are in `.omp/local/AGENTS.local.md`. Inspect a project's actual SDK before applying world assumptions.
- Project-specific layouts and progress belong in project context, not this file.

## Unity Editor safety

- **Drive the open Editor through MCP for Unity. Never hand-edit an open scene's YAML or scene/asset state on disk**: the Editor can overwrite it. Missing MCP: [installer](scripts/install-unity-mcp.py). Host without native MCP tools: `.omp/scripts/unity_mcp.py` (stdio client, see `.omp/scripts/README.md`).
- With several editors open, pin the intended instance (MCP for Unity `set_active_instance` with the exact `Name@hash` from its instances list) **and** pass `unity_instance` on every call (the pin doesn't always stick), then confirm `Application.dataPath`. Verify current scene state rather than trusting remembered state; other sessions may be editing it.
- **Worktrees do not isolate the Editor. Only one agent mutates the editor at a time.** Assign non-overlapping object/asset ownership and serialize shared mutations. One owner coordinates editor-global bakes, refreshes/compilation, scene loads and play-mode transitions; other sessions pause conflicting work.
- `execute_code` freezes the editor while it runs and MCP gives up after ~10 s. Keep each call short; give every loop over scene geometry a time budget (an unbounded O(n²) triangle loop hung an editor with unsaved work). Long jobs use the `com.awdk.agenttools` `Start`/`Status` pattern.
- **Never destroy a camera after `Render()`**: it crashes the editor on the next repaint. Reuse one persistent `__CapCam__`; sweep `__*__` objects before saving, baking or building.
- The editor may run under a comma-decimal locale: hardcode float literals and parse/format with `CultureInfo.InvariantCulture`.
- After every script change, read the console and resolve `error CS` before proceeding. Compile errors can silently cancel play-mode requests and block every other agent.
- Scripted hierarchy edits need `MarkSceneDirty` before saving; parenting/renaming alone may not persist.

## Visual acceptance gate

**Anything built, generated, placed, textured or lit in Unity or Blender needs the matching stage reviewer's SHIP IT before completion.** Own screenshots and numerical audits do not replace this gate. The old single `scene-reviewer` is retired; the reviewers are:

| Reviewer | Judges | Stages |
|---|---|---|
| `layout-reviewer` | shell-layout blockouts (the concept's geometry), zoning plans, greybox variants with their rough furniture zones in 3D, world size limits | A.3, B.1, B.2 |
| `dressing-reviewer` | Build-out passes and placed interaction objects: furniture as placed, judged in 3D (seating and layout rules), build quality and board match (separate style and build scores), geometry (z-fighting); decides lock gaps; never lighting | C.1, C.2 |
| `final-reviewer` | lighting mood vs the boards, final render, visual regressions after perf fixes; the only sign-off for a finished area/world and for upload | D.1 (draft, then after bake + probe re-bake), D.2 |

Every review gives `SHIP IT | MINOR FIXES | NEEDS WORK` plus `Score: N/10` with reasons (dressing: `Style N/10 · Build N/10`); SHIP IT needs no blocker or should-fix finding and a score ≥ 8, and the score never overrides findings. A.3 style rounds have no reviewer: the user picks.

**NEEDS WORK / MINOR FIXES means fix and re-review**; never waive findings or lower acceptance to claim completion. Order, briefing, the fix loop and when to report blocked: [review-protocol.md](skills/world-pipeline/references/review-protocol.md) "For the agent that dispatches reviewers".

The reviewer may leave `__CapCam__` **and an active realtime directional `__CapLight__`**. Before every commit, bake or build, delete every `__*__` object (your own rigs too) and assert realtime/mixed light count is 0; the SDK saves the open scene on build.

**Visual fixes are proven by a rendered before/after from the same camera.** Numbers locate defects; they never declare one fixed. A zero-defect result counts only alongside a positive control: the same poses/mask/threshold against a known-failing state, with both numbers quoted (workflow: [`.omp/skills/agent-verification/SKILL.md`](skills/agent-verification/SKILL.md)).

## Routing

| Task | Load |
|---|---|
| Build a world from a description, or resume one with `WORLD.md` | [`.omp/skills/world-pipeline/SKILL.md`](skills/world-pipeline/SKILL.md) |
| Gather information for a world (ask only about gaps) | [`.omp/skills/world-pipeline/references/intake.md`](skills/world-pipeline/references/intake.md) |
| Concept (shell-layout blockouts + concept art, style rounds), floor plans, greybox | agent `world-architect`, `layout-reviewer`; [`.omp/skills/spatial-design/SKILL.md`](skills/spatial-design/SKILL.md) (guide, research, case studies) |
| Scale, reference eye height, dimensions | spatial-design guide ([spatial-design.md](skills/spatial-design/references/spatial-design.md)) §5.9, §5.11 |
| Clip planes, fog vs far clip, float precision, world extent, teleport-island placement, distant scenery/skybox backdrops, z-fight separation | [`.omp/skills/clip-planes/SKILL.md`](skills/clip-planes/SKILL.md) |
| Separate rooms as teleport islands | agent `world-architect` "Separate rooms: teleport islands" (design); `world-builder` "Unity rules" (doors, landings) |
| Execute a build stage (Build-out, interactions, lighting); collision fitting, lie-down colliders, geometry standard, in-world UI ("show, don't tell") | agent `world-builder` |
| Review anything visual; dispatching reviewers and the fix loop | agents in "Visual acceptance gate"; [`.omp/skills/world-pipeline/references/review-protocol.md`](skills/world-pipeline/references/review-protocol.md) |
| Prove your own work: renders vs metrics, positive controls, before/after, handoffs | [`.omp/skills/agent-verification/SKILL.md`](skills/agent-verification/SKILL.md) |
| Find existing models/textures; local library and owned packs | agent `asset-finder`; [`.omp/skills/worldbuilding-assets/SKILL.md`](skills/worldbuilding-assets/SKILL.md) (licences, `.unitypackage` import, prop shader default) |
| Import a model or prefab (FBX/GLB/unitypackage, Blender or image-to-3D output): scale, axes, UV2, mesh and prefab hygiene | [`.omp/skills/asset-import/SKILL.md`](skills/asset-import/SKILL.md) |
| Materials, textures, shaders | [`.omp/skills/materials-shaders/SKILL.md`](skills/materials-shaders/SKILL.md) |
| Model a custom prop; avatar exports to Blender, avatar clothing | agent `blender-modeler` ("Avatar work"); [`.omp/skills/lowpoly-tree-generation/SKILL.md`](skills/lowpoly-tree-generation/SKILL.md) |
| Make an existing rigid model cheaper (tris, materials) without a visible change or a re-bake | agent `blender-optimizer`; [`.omp/skills/vrchat-world-optimization/SKILL.md`](skills/vrchat-world-optimization/SKILL.md) |
| Image-to-3D props, GLB scale and placement | [`.omp/skills/image-to-3d-props/SKILL.md`](skills/image-to-3d-props/SKILL.md); the `image-to-3d` tool ([`.omp/docs/tools.md`](docs/tools.md)) |
| Plush / fumo of a character or avatar: concept views, generation, prep, pickup, fire screams, placement | [`.omp/skills/fumo-plushie/SKILL.md`](skills/fumo-plushie/SKILL.md) |
| Generate images (concepts, references, textures, outfits) | the `image-gen` / `image-edit` tools ([`.omp/docs/tools.md`](docs/tools.md)) |
| Scene setup, VRC components, build and upload | [`.omp/skills/unity-vrc-world-sdk-3/SKILL.md`](skills/unity-vrc-world-sdk-3/SKILL.md) |
| Android/Quest/iOS version of a world: intake decision, port-friendly design choices, porting a finished PC world (mobile shaders, ASTC and lightmap-encoding overrides, EasyQuestSwitch, mobile budgets, Build & Test on device, same-blueprint upload) | [`.omp/skills/vrchat-android-worlds/SKILL.md`](skills/vrchat-android-worlds/SKILL.md) |
| UdonSharp code, sync, workspace code conventions | [`.omp/skills/unity-vrc-udon-sharp/SKILL.md`](skills/unity-vrc-udon-sharp/SKILL.md), [`.omp/skills/vrc-udon-workflow/SKILL.md`](skills/vrc-udon-workflow/SKILL.md) |
| Lightmap bake: Bakery (paid), else GLIM (free), else Progressive GPU; lighting standard (no realtime/Mixed, darker interiors, probes) | [`.omp/skills/bakery-light-baking/SKILL.md`](skills/bakery-light-baking/SKILL.md) "Workspace lighting standard" |
| Low FPS, perf comparison, performance budgets, editor-vs-VR benchmark | agent `perf-optimizer` ("Default budgets"); [`.omp/skills/vrchat-world-optimization/SKILL.md`](skills/vrchat-world-optimization/SKILL.md); `.omp/local/benchmarks/<hostname>.json` + `.omp/scripts/perf_grade.py` |
| Drive the Unity Editor from an agent (MCP calls, long jobs, saving, captures) | [`.omp/skills/unity-mcp-scripting/SKILL.md`](skills/unity-mcp-scripting/SKILL.md) |
| Something behaves oddly | [`.omp/skills/vrchat-world-gotchas/SKILL.md`](skills/vrchat-world-gotchas/SKILL.md), then grep `.omp/knowledge/notes/` |
| Unity won't launch from ALCOM, UPM ignores packages, HTTP 413 screenshots | [`.omp/docs/troubleshooting.md`](docs/troubleshooting.md) |
| Unity check tools (z-fight, capture, perf, audit) | [`.omp/docs/unity-tools.md`](docs/unity-tools.md) |
| Machine setup / host wiring | [`.omp/docs/bootstrap.md`](docs/bootstrap.md), [`.omp/docs/hosts.md`](docs/hosts.md) |
| Trial-run or wear-test the pipeline itself | [`.omp/skills/pipeline-trial/SKILL.md`](skills/pipeline-trial/SKILL.md) |

Before debugging anything from scratch, grep `.omp/knowledge/notes/` (or read
[`.omp/knowledge/INDEX.md`](knowledge/INDEX.md)): hundreds of single-lesson notes, symptom → cause → fix → verify.

**World defaults** (lighting standard, performance budgets, scale and clip planes, teleport islands,
geometry) live in the homes above. Unlike the hard rules (`.omp/RULES.md`), the user may change any
of them for a specific world; record the change and the user's words in that world's `WORLD.md`
Decisions log, and every agent then follows `WORLD.md`.

**Scale: people are 1.4 m tall (eye 1.3 m) in all worlds; everything is ×0.8 of real-world size.** Use a
1.4 m person for every scale figure, review camera, capture, fit test and brief. Shell, built-ins, loose
furniture (seat ≈0.36 m, table ≈0.60 m), props, pickups and outdoor features are all ×0.8. Fix an import
to real size first (asset-import skill), then apply ×0.8. Collision minimums (clear heights, doors, stairs,
paths) never shrink. Details: spatial-design §5.9, §5.11. Existing worlds are not rescaled unless the user
asks.

## Collision, seats and pickups

### Movement collision

- **No colliders on small props**: chairs, stools, couches, armchairs, coffee/side/bedside tables, decoration and ground clutter are walked through; remove primitive auto-colliders. Add collision only where players must not pass (floors, walls, railings, large solid masses, big furniture below), or for explicitly requested pickups below.
- **Big furniture is solid** (user, 2026-10-13). Dining and kitchen tables and other big tables, kitchen counters and islands, bar counters, cabinets, sideboards, dressers, wardrobes, bookcases and appliance-sized pieces get a child GameObject named `SolidCollider` with one always-on, non-trigger `BoxCollider` over the piece's footprint from the floor to its top surface (plan JSON `solid: true`). Players can't walk through them and pickups rest on them. Beds and couches don't get one; they keep the lie-down collider.
- **Lie-down colliders.** Beds, couches and other lie-on furniture (cuddle platforms) get a collider on their top surface: a child GameObject named `LieDownCollider` with one non-trigger `BoxCollider`, **disabled by default** (inactive in the saved scene), switched on by ONE world-wide "lie-down colliders" Udon toggle. It is for non-full-body players; full-body players leave it off. Details: world-pipeline skill "Furniture colliders".
- Prefer one `BoxCollider`; otherwise a small number of locally axis-aligned boxes. `MeshCollider` is a last resort, **never on surfaces players walk on or brush past**.
- Stairs, steps and terraces get one thin rotated ramp box per flight, never per-tread collision. Fitting building boxes and automated wall fitting: agent `world-builder` "Unity rules".

### No seats unless explicitly requested

**Never add `VRC_Station` / `VRCStation` to furniture or other props without an explicit user request.** Strip stations from imported prefabs; never restore removed stations or add them for convenience. This is a user preference, not a performance tradeoff (2026-09-03). When the user does ask for seats, record it in the world's `WORLD.md`.

### Pickups

- Only explicitly requested objects become pickups.
- Every pickup uses **`VRC_Pickup.proximity = 0.1f`** (10 cm), never 0, 0.2 or the SDK default 2 m. This 2026-09-15 directive supersedes older proximity guidance.
- Every pickup uses **`VRC_Pickup.AutoHoldMode.No`**, never `Yes` or `AutoDetect` (2026-09-11). Preserve gravity and networking.
- Apply both settings to scene instances, new/imported pickups and authored/exported prefabs. Audit existing pickups whenever modifying their scene.
- Use one tight primitive collider around the actual grabbable prop (a requested pickup is a grabbable object, not a furniture collider). Never oversize it or add remote interaction proxies. Investigate stray triggers for excessive reach; do not increase proximity as a workaround.
- Desktop reach compensation means desktop and VR effective reach can differ.

## Knowledge, recurring checks and backups

- Record useful discoveries before moving on: session-local gotchas/preferences → auto-memory; project facts → project `AGENTS.md` (or `WORLD.md`); transferable techniques → a note in `.omp/knowledge/notes/`, and a change to how a pipeline stage runs → an edit to the pipeline skill or the agent; skill-sized workflows → `.omp/skills/`. Preserve measured evidence and context; avoid duplicating project status in workspace guidance.
- **Lessons capture: self-improvement after fixing poor first attempts.** When the user judges something you built as bad (broken, ugly, wrong) and a later fix produces a result the user confirms is better, capture that lesson before moving on: what was built, the user's words, what went wrong in the first attempt and why, and what actually fixed it. A transferable technique becomes a note in `.omp/knowledge/notes/` (format and sanitizing rules in [`.omp/knowledge/README.md`](knowledge/README.md); then run `python .omp/scripts/build-knowledge-index.py`) or, when it is a whole workflow, a skill in `.omp/skills/` (create or update one); a change to how a stage runs becomes an edit to `.omp/skills/world-pipeline/SKILL.md` or the relevant `.omp/agents/*.md`; session-local gotchas/preferences go to auto-memory; project-specific facts go in the project's `AGENTS.md` or `WORLD.md`. Save the working scripts/tools that produced the fix alongside the note or skill, or in the project's `Tools/`, so they can be reused rather than rewritten. Only the user's word counts for both the "bad" and the "better" verdicts — reviewer-agent findings, your own screenshots or metrics never trigger or confirm a lesson on their own. Do not log routine work, first-try successes or unconfirmed fixes.
- **Notes are compiled into skills.** Each knowledge topic has a checklist in its owning skill (`references/lessons-<topic>.md`, or `reference/` where the skill uses that folder): one line per note, `- **rule** — why.`, no links. Adding a note means adding its line there too; skills never link notes (grep `.omp/knowledge/notes/` when you need the evidence).
- **AWDK (Agentic VRChat World Development Kit) lives in `.omp/` and is the single source of truth**: pipeline skill (`.omp/skills/world-pipeline`), agents (`.omp/agents/`), knowledge notes (`.omp/knowledge/`), docs (`.omp/docs/`), templates (`.omp/templates/`), the Unity package (`.omp/unity-package/com.awdk.agenttools`), helper scripts (`.omp/scripts/`) and `.omp/CREDITS.md`. Edit these files directly; credit every external source in `.omp/CREDITS.md`. **Keep this file to always-relevant rules**: stage- or task-specific guidance goes to the agent or skill that does that stage, with a routing row here.
- **Sources never inline.** A skill's sources go only in `.omp/skills/<skill>/SOURCES.md` (grouped by the citing file); kit-wide ones in `.omp/CREDITS.md`. `SKILL.md`, references, agents, templates and this file carry no citation tags, source links or note links: the model doesn't need provenance to use a skill, and every inline citation costs context on each read. Keep only URLs an agent must open to do the task (downloads, asset sites, tools, APIs). Open `SOURCES.md` only to check where a claim came from.
- `.omp/` is the kit's own git repo, published as the public AWDK repo. Commit a checkpoint after each meaningful skill/agent/knowledge change and before and after each kit test run's fixes: `git -C .omp add -A && git -C .omp commit -m "<what changed>"`. The pre-commit leak check must pass (personal content goes to `.omp/local/`; never `--no-verify`). Agents never push; the owner pushes, or asks for it explicitly. `python .omp/scripts/check_kit.py` checks links and front matter before a release.
- Turn recurring factual audits into reusable executable checks; reuse existing tooling first. Keep one-off checks disposable. Default read-only, report object/asset IDs and observed values; fixes need explicit mutation scope. Checks never replace visual review.
- After significant project work, make a **local backup commit** in that project's repo: background `git -C <project> add -A` (can take minutes), then commit with a concise checkpoint message. **Never push or add remotes.** Before a new world's first `git add`, copy [`.omp/scripts/unity-world.gitignore`](scripts/unity-world.gitignore) to the project root as `.gitignore`.
- Never edit or commit `Library/`. Unity caches/build outputs (`Library/`, `Temp/`, `Logs/`, `UserSettings/`, generated `.csproj`/`.sln`, builds) remain ignored.

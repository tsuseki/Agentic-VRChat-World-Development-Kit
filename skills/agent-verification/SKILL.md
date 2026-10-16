---
name: agent-verification
description: How an agent proves its own world-building work in Unity or Blender. Metrics locate defects, but only a rendered before/after from the same camera proves a fix; every zero-defect result needs a positive control; checks that cannot see the defect they claim to verify; what to give a stage reviewer and how to act on its findings; handoffs between agents sharing one editor. Load before reporting a visual fix, placement pass, material or lighting change, or clean scan as done, when briefing a reviewer or subagent, when acting on review findings, or when several agents work in one project.
---

# Verifying your own world-building work

Scope: any agent that builds, places, textures or lights in the open Unity editor (or Blender) and
has to show that the result holds. This is the builder's half of the gate. Who reviews which stage
and what SHIP IT requires: `.omp/AGENTS.md` "Visual acceptance gate". Briefing, verdicts, reports
and the fix loop: `.omp/skills/world-pipeline/references/review-protocol.md`; this skill does not
restate them. Self-verification never replaces the reviewer's verdict: scripted passes "succeed"
while burying chairs 99% inside tables. It stops the reviewer spending rounds on defects you could
have caught. Editor tooling (`WorldCapture`, `ZFightScan`, `ZFightRender`, `WorldAudit`):
`.omp/docs/unity-tools.md`.

## 1. The rule: metrics locate, renders prove

- A number tells you where to look. A visual fix is proven only by a **rendered before/after from
  the same camera** (pose, FOV, resolution), with both images kept and named.
- A metric going green with no visible change is not a fix: `importNormals = Calculate` took bad
  winding from 13.7% to 0% with zero visual change, because the real defect was UVs.
- Before quoting a number, ask whether that check can see the defect at all (§4).
- A mask or pixel set you have not looked at is a hypothesis: render it as an overlay first.
- Questions about appearance (facing, stretch, colour, "reads as lit") are answered by a render;
  geometry answers only geometric questions such as overlap or flush-to-wall.

## 2. Proving a fix

| # | Step |
|---|---|
| 1 | Read Console errors **and** warnings (Unity MCP `read_console`) before forming a hypothesis; also read the unfiltered tail. A warning repeated 999+ times often names the object and world position |
| 2 | "This used to look right": diff materials (`git diff <checkpoint> -- '*.mat'`) first, then shaders, then the scene; a material often sits between your change and what the player names |
| 3 | Pin the baseline. Your own before-shot can be the contaminated one: prove inputs against version control and hash lightmap/probe assets against a backup (their folders are often gitignored), then re-introduce the suspect and watch the metric move toward the baseline |
| 4 | Capture with a game camera, never the Scene view: selection outlines and debug draw modes (Mipmaps, Overdraw) never ship. A pure, clamped colour such as (1, 0.4, 0) with no fog or falloff is an overlay; compare it to the editor's outline colours |
| 5 | Capture cameras render with `useOcclusionCulling = false`: baked occlusion culls a moved static object by its old bounds. A moved static puts an occlusion re-bake on the pre-upload list |
| 6 | Shoot before and after from the same pose; quote both numbers next to both images |
| 7 | A targeted fix that leaves the metric byte-identical changed the wrong thing: the edit never produced the number, never reached the renderer, or a bound map (`_EmissionMap`, `_MetallicGlossMap`) overrides it. Find the offender by value: compute what each candidate would produce and match it |
| 8 | Defect found in one state of a toggle (night/day, variant A/B): measure it in the other state too and quote both; fix only what the feature caused. If the fix would make the new state better than the baseline on that object, the finding is pre-existing |
| 9 | After any scripted placement pass: prop-vs-prop interpenetration (AABB overlap sweep), floating or sunken props, materials without albedo |
| 10 | Same pass: print median, p90 and **worst** nearest-light-probe distance with the object name. A worst far above p90 is a coordinate bug (often a position applied twice, every component exactly 2×), not a probe-density problem |
| 11 | Clearances from `Renderer.bounds` (encapsulated over children) with `Intersects` and the gap on every axis, never from transform positions: a position is an anchor, not an extent |
| 12 | Key verification lookups by object identity (the `Renderer` reference or instance ID), not name. A defect larger than the world it lives in means the check is broken |
| 13 | Z-fighting: the stage gate and its scanner control are in `.omp/skills/world-pipeline/SKILL.md` "Z-fighting gate" |

## 3. Positive controls: a zero is not evidence on its own

A clean result and a dead check print the same number: camera facing a wall, render never ran,
mask selected nothing, threshold typo. A zero arrives exactly when you most want to stop.

- **Zero-defect results.** Run the identical poses, mask and threshold against a state known to
  fail (pre-fix build, the other toggle state, stashed change, or a value raised until it must
  trip) and quote the pair: "0 px at night, 6.7k-43k px in day on the same poses".
- **Ad-hoc metrics.** Run a check you invented on a broken object against a working sibling first;
  if it condemns the sibling too, the metric is wrong ("800 of 800 vertices buried" on a hidden
  river read "288 of 289" on the visible lake). Report broken and good side by side; with no
  sibling, take the control from version-control history.
- **Toggle-diffs returning 0 px.** Toggle a second object known to be in shot; if that also reads
  0, the camera is mis-framed.
- **Keyed masks.** Render the "all visible" pass with occluders hidden: it is the denominator and
  proves the key is live.
- **Capture repeatability.** Two captures of the same state must differ by 0 px before a
  before/after difference means anything.
- **Pipelines that write files.** After writing, re-check every output (e.g. re-hash all stored
  images and assert no duplicate pairs).

## 4. Checks that cannot see their defect

| Check | Blind to | Use instead |
|---|---|---|
| % of vertices below ground | floating or arching pieces | ground-skimming camera ~0.2 m high |
| Raycast sampling | sub-pixel slivers | project triangles to screen; thickness `2·area / longest edge` under ~1.5 mm |
| % of pixels below a threshold | a mid-tone band | scanline profile against the local surround |
| Ratios read off a screenshot vs material values | display encoding (about the 1/2.2 power in Linear projects) | compare encoded to encoded, or convert first |
| Re-import into the authoring tool | Unity's axis convention (the round-trip repeats it) | verify in Unity against world axes |
| `RecalculateBounds()` after an index-only trim | orphan vertices | compact vertices or measure triangles |
| Transform-position clearance | extents | `Renderer.bounds`, every axis |
| AABB coverage or occlusion (off by up to 30×) | cutout leaves, air inside bounds | unlit magenta key, pixel count |
| Perceptual-hash match | aspect stretch (it resizes to a square first) | render 1:1 and frame aspect side by side |
| Hash of a raw candidate vs transformed outputs | duplicates | hash after the pipeline's own crop/resize |
| Vertex density to find a front | facing of ribbed or wrapped pieces | head-on render; fronts show as handles, gaps, reveals |
| "Does the ray hit S anywhere" | occluded pixels (fake asymmetries) | nearest hit across all geometry |
| `Physics.Raycast` attribution | visible meshes (it hits collider proxies) | renderer toggle, then ray-triangle for the submesh |
| Sweep over a fixed set of poses | corners no pose framed | add a pose framing every flagged area |
| Hue-masked mean | the object's real statistics (selection bias) | statistics over all its pixels |
| Sky-difference geometry mask | glass (counts as geometry, pins upper percentiles) | exclude glazing by renderer |
| Downward brightness sampler | interiors (lands on roofs) | first walkable floor with a ceiling within ~14 m, reachable cells |
| One shot per room | lighting (facing dominates) | at least 4 yaws, mean and spread |
| Level camera sweep | undercroft and overhang ceilings | sweep pitched up (about -22°) as well |
| Capture with occlusion culling on | moved static objects | `useOcclusionCulling = false` |

## 5. Measuring rendered frames

- **Lighting grade.** Eye-height station grid (the WORLD.md reference eye height), 4 yaws, mean
  luminance, dark % (L < 0.05), blown % (L > 0.9); keep one fixed pose for A/B across bakes and
  screenshot the worst station before "fixing" it: it may sit inside dark geometry.
- **Which renderer owns a pixel.** Toggle-diff the suspect, or swap an unlit magenta material onto
  it and restore `sharedMaterials`; bucket changed pixels by delta (>0.01 / >0.15 / >0.30 / >0.50)
  instead of averaging the feathered rim. For a near-black surface, cast ~256 hemisphere rays and
  count escapes: zero means the fix is geometry, not material.
- **Pixel sweeps.** Gate on two conditions (brightness and hue); per-pixel max means nothing on
  creased soft furnishings; hide UI by disabling `Canvas` components (it is not a `Renderer`);
  compare thin members to the surface they abut (~1.2× reads as trim, ~2× as a fixture); scope
  toggle loops to one room, since a scene-wide loop locks the editor past the MCP timeout. Report
  a number a later session can reproduce.
- **Visible area.** Key the judged surface's material as unlit magenta, render from real player
  cameras, divide by the occluders-hidden render, then restore the material from version control,
  never by re-typing values; select by material, not by name.
- **Camera placement.** Raycast to the ground for height and linecast eye-to-target, rejecting
  blocked bearings; offsets from a bounds centre on a slope put cameras inside rocks.

## 6. Handing work to a reviewer

What the brief contains and the order of reviews: review-protocol "Inputs the orchestrator must
give you" and "For the agent that dispatches reviewers". On top of that, the builder:

- Runs §2 on its own work first, so the reviewer finds design problems, not trivia.
- **Quotes** the art direction from the project's design document, re-read before each brief, and
  passes reference image paths, never a paraphrase from memory: the reviewer has no other source
  and will grade confidently against an invented target for several rounds.
- Names a failing case as an example and asks for the whole defect class to be swept.
- Attaches the scan output with its positive control (§3), and says where it deviated from a
  previous reviewer's number and why.
- In a sunlit exterior, says up front that no artificial lights are expected; "enough lights, each
  with a fixture" is an interior criterion.
- Sends screenshots as JPEG (quality ~85) or with the long edge capped near 1600 px, attaching only
  the ones discussed: request limits are in bytes, not tokens, and a PNG can trip HTTP 413.
- Before any commit, bake or build: deletes every `__*__` capture object and asserts the
  realtime/mixed light count is 0; both checks, since either can miss alone, and the SDK saves the
  open scene on build.

## 7. Acting on findings

The loop itself (fix, re-bake, probes, re-review, three rounds then change approach) is in
review-protocol. Per finding:

1. Query the named objects' current state first; the review may predate a fix. Record
   already-fixed findings as closed with the measurement that proves it.
2. Check the cited camera pose against a reachability model (raycast-down grid, player capsule
   clearance, flood fill with a ~1.0 m step); re-measure from the nearest reachable pose before
   re-baking geometry no player can see.
3. Take the reviewer's diagnosis, recompute its numbers. Coordinates: against the bounds of every
   part of the assembly (frame and canvas, planter and foliage) and whatever stands beneath.
   Rotations: from measured facing (for seating, backrest centroid minus seat centroid), applied as
   a delta; quote the new measured facing as proof, never the transform value.
4. Never dismiss a finding because your own metric disagrees; check what that metric is blind to
   (§4). The reviewer's diagnosis is usually right even when its arithmetic isn't.
5. Classify toggle-state findings in both states (§2 step 8), then prove the fix with a
   same-camera before/after (§1).
6. After a fix passes re-review, record symptom → cause → rule before the next task, in the
   project's own instructions. Promoting a lesson to the shared kit follows
   `.omp/skills/world-pipeline/SKILL.md` "Lessons capture".

## 8. Handoffs between agents

- **One editor, several sessions.** Worktrees do not isolate the editor. Re-query the hierarchy
  and confirm an object is yours (e.g. its mesh asset path) before modifying or deleting it; after
  a long bake, import or batch edit, re-verify that the objects it covered still match what you
  built before measuring. If another session has taken an object over, stop and surface it.
- **Editor scripts compile as one assembly.** One `error CS` in `Assets/Editor/` stops every
  agent's tooling. Give each parallel agent exclusive ownership of its own script; blocked by
  someone else's error, check the file's modification time and wait, never stub it.
- **Subagent briefs.** Named cameras, objects and values become the ceiling of what gets checked.
  Name them as examples, ask for the class, and pass measured constants with the method to
  re-measure them locally.
- **Tell subagents the rule.** A builder passes its own work; say explicitly that a same-camera
  render is the proof, and route the result to a separate reviewer.
- **Reviewer briefs come from the dispatcher,** quoted from the design document; mid-run
  corrections go to the running reviewer as a message, with the difference called out as a finding.

## 9. What a "done" report carries

- Same-camera before/after image pairs, file paths and the pose used.
- Every number as a pair: result and positive control (or broken and good sibling), same poses,
  mask and threshold.
- Scan output with its final status line (`PAIRS=0 COMPLETE` for the z-fight gate).
- Findings closed, already-closed (with the proving measurement), pre-existing (with numbers from
  the other state), and deviations from reviewer numbers with the reason.
- The stage reviewer's verdict. Without SHIP IT the work is not done.

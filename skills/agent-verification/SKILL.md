---
name: agent-verification
description: How an agent proves its own world-building work in Unity or Blender. Metrics locate defects, but only a rendered before/after from the same camera proves a fix; every zero-defect result needs a positive control; checks that cannot see the defect they claim to verify; what to give a stage reviewer and how to act on its findings; handoffs between agents sharing one editor. Load before reporting a visual fix, placement pass, material or lighting change, or clean scan as done, when briefing a reviewer or subagent, when acting on review findings, or when several agents work in one project.
---

# Verifying your own world-building work

Scope: any agent that builds, places, textures or lights in the open Unity editor (or Blender) and
has to show that the result holds. This is the builder's half of the gate. Who reviews which stage
and what SHIP IT requires: `.omp/AGENTS.md` "Visual acceptance gate". Briefing, verdicts, reports
and the fix loop: [review-protocol.md](../world-pipeline/references/review-protocol.md); this skill
does not restate them. Self-verification never replaces the reviewer's verdict; it stops the
reviewer spending rounds on defects you could have caught
([get-every-generated-asset-independently-reviewed](../../knowledge/notes/get-every-generated-asset-independently-reviewed.md)).

Every item links the knowledge note that holds the measured case behind it. Editor tooling
(`WorldCapture`, `ZFightScan`, `ZFightRender`, `WorldAudit`): [unity-tools.md](../../docs/unity-tools.md).

## 1. The rule: metrics locate, renders prove

- A number tells you where to look. A visual fix is proven only by a **rendered before/after from
  the same camera** (pose, FOV, resolution), with both images kept and named
  ([metrics-that-cannot-see-their-defect](../../knowledge/notes/metrics-that-cannot-see-their-defect.md)).
- A metric going green with no visible change is not a fix: the metric was measuring something
  else ([metrics-that-cannot-see-their-defect](../../knowledge/notes/metrics-that-cannot-see-their-defect.md)).
- Before quoting a number, ask whether that check can see the defect at all (§4).
- A mask or pixel set you have not looked at is a hypothesis: render it as an overlay first
  ([pixel-attribution-needs-nearest-hit](../../knowledge/notes/pixel-attribution-needs-nearest-hit.md)).
- Questions about appearance (facing, stretch, colour, "reads as lit") are answered by a render;
  geometry answers only geometric questions such as overlap or flush-to-wall
  ([vertex-density-cannot-tell-which-way-furniture-faces](../../knowledge/notes/vertex-density-cannot-tell-which-way-furniture-faces.md)).

## 2. Proving a fix

| # | Step | Note |
|---|---|---|
| 1 | Read Console errors **and** warnings (Unity MCP `read_console`) before forming a hypothesis; a warning repeated 999+ times often names the object and position | [read-console-warnings-before-hunting-visual-bugs](../../knowledge/notes/read-console-warnings-before-hunting-visual-bugs.md) |
| 2 | "This used to look right": diff materials against the last checkpoint first, then shaders, then the scene | [diff-materials-first-on-visual-regressions](../../knowledge/notes/diff-materials-first-on-visual-regressions.md) |
| 3 | Pin the baseline. Your own before-shot can be the contaminated one; prove inputs against version control and asset hashes, and re-introduce the suspect to watch the metric move | [verify-the-baseline-before-fixing-a-regression](../../knowledge/notes/verify-the-baseline-before-fixing-a-regression.md) |
| 4 | Capture with a game camera, never the Scene view (selection outlines and debug draw modes never ship); sample an odd colour's exact RGB against editor overlay colours | [colour-artifact-screenshot-may-be-editor-overlay](../../knowledge/notes/colour-artifact-screenshot-may-be-editor-overlay.md) |
| 5 | Capture cameras render with `useOcclusionCulling = false`; a moved static object puts an occlusion re-bake on the pre-upload list | [baked-occlusion-hides-moved-statics-in-captures](../../knowledge/notes/baked-occlusion-hides-moved-statics-in-captures.md) |
| 6 | Shoot before and after from the same pose; quote both numbers next to both images | [metrics-that-cannot-see-their-defect](../../knowledge/notes/metrics-that-cannot-see-their-defect.md) |
| 7 | A targeted fix that leaves the metric byte-identical changed the wrong thing (or never reached the renderer, or a bound map overrides it): find the offender by value | [unchanged-metric-means-wrong-target](../../knowledge/notes/unchanged-metric-means-wrong-target.md) |
| 8 | Defect found in one state of a toggle (night/day, variant A/B): measure it in the other state too; fix only what the feature caused | [classify-a-defect-against-the-other-toggle-state](../../knowledge/notes/classify-a-defect-against-the-other-toggle-state.md) |
| 9 | After any scripted placement pass: prop-vs-prop interpenetration, floating or sunken props, materials without albedo | [get-every-generated-asset-independently-reviewed](../../knowledge/notes/get-every-generated-asset-independently-reviewed.md) |
| 10 | Same pass: print median, p90 and **worst** nearest-light-probe distance with the object name; a worst far above p90 is a coordinate bug | [probe-distance-outliers-reveal-misplaced-objects](../../knowledge/notes/probe-distance-outliers-reveal-misplaced-objects.md) |
| 11 | Clearances from `Renderer.bounds` with the gap on every axis, never from transform positions | [verify-clearance-by-bounds-not-positions](../../knowledge/notes/verify-clearance-by-bounds-not-positions.md) |
| 12 | Key verification lookups by object identity, not name; a defect larger than the world means the check is broken | [key-verification-lookups-by-identity-not-name](../../knowledge/notes/key-verification-lookups-by-identity-not-name.md) |
| 13 | Z-fighting: the stage gate and its scanner control live in the world-pipeline skill "Z-fighting gate" | [.omp/skills/world-pipeline/SKILL.md](../world-pipeline/SKILL.md) |

## 3. Positive controls: a zero is not evidence on its own

A clean result and a dead check print the same number: camera facing a wall, render never ran,
mask selected nothing, threshold typo. A zero arrives exactly when you most want to stop.

- **Zero-defect results.** Run the identical poses, mask and threshold against a state known to
  fail (pre-fix build, the other toggle state, stashed change, or a value raised until it must
  trip) and quote the pair: "0 px at night, 6.7k-43k px in day on the same poses"
  ([zero-defect-result-needs-positive-control](../../knowledge/notes/zero-defect-result-needs-positive-control.md)).
- **Ad-hoc metrics.** Run a check you invented on a broken object against a working sibling first;
  if it condemns the sibling too, the metric is wrong. Report broken and good side by side
  ([validate-ad-hoc-metrics-on-a-known-good-sibling](../../knowledge/notes/validate-ad-hoc-metrics-on-a-known-good-sibling.md)).
- **Toggle-diffs returning 0 px.** Toggle a second object known to be in shot; if that also reads
  0, the camera is mis-framed ([unchanged-metric-means-wrong-target](../../knowledge/notes/unchanged-metric-means-wrong-target.md)).
- **Keyed masks.** Render the "all visible" pass with occluders hidden: it is the denominator and
  proves the key is live ([measure-visible-surface-by-keying-its-material](../../knowledge/notes/measure-visible-surface-by-keying-its-material.md)).
- **Capture repeatability.** Two captures of the same state must differ by 0 px before a
  before/after difference means anything
  ([verify-the-baseline-before-fixing-a-regression](../../knowledge/notes/verify-the-baseline-before-fixing-a-regression.md)).
- **Pipelines that write files.** After writing, re-check every output (e.g. re-hash all stored
  images and assert no duplicate pairs)
  ([dedupe-hash-after-pipeline-transform](../../knowledge/notes/dedupe-hash-after-pipeline-transform.md)).

## 4. Checks that cannot see their defect

| Check | Blind to | Use instead | Note |
|---|---|---|---|
| % of vertices below ground | floating or arching pieces | ground-skimming camera ~0.2 m high | [metrics-that-cannot-see-their-defect](../../knowledge/notes/metrics-that-cannot-see-their-defect.md) |
| Raycast sampling | sub-pixel slivers | project triangles to screen; thickness test | same |
| % of pixels below a threshold | a mid-tone band | scanline profile against the local surround | same |
| Ratios read off a screenshot vs material values | display encoding (about the 1/2.2 power) | compare encoded to encoded, or convert first | same |
| Re-import into the authoring tool | Unity's axis convention | verify in Unity against world axes | same |
| `RecalculateBounds()` after an index-only trim | orphan vertices | compact vertices or measure triangles | same |
| Transform-position clearance | extents | `Renderer.bounds`, every axis | [verify-clearance-by-bounds-not-positions](../../knowledge/notes/verify-clearance-by-bounds-not-positions.md) |
| AABB coverage or occlusion | cutout leaves, air inside bounds | unlit magenta key, pixel count | [measure-visible-surface-by-keying-its-material](../../knowledge/notes/measure-visible-surface-by-keying-its-material.md) |
| Perceptual-hash match | aspect stretch | render 1:1 and frame aspect side by side | [phash-cannot-detect-aspect-distortion](../../knowledge/notes/phash-cannot-detect-aspect-distortion.md) |
| Hash of a raw candidate vs transformed outputs | duplicates | hash after the pipeline's own transform | [dedupe-hash-after-pipeline-transform](../../knowledge/notes/dedupe-hash-after-pipeline-transform.md) |
| Vertex density to find a front | facing of ribbed or wrapped pieces | head-on render | [vertex-density-cannot-tell-which-way-furniture-faces](../../knowledge/notes/vertex-density-cannot-tell-which-way-furniture-faces.md) |
| "Does the ray hit S anywhere" | occluded pixels | nearest hit across all geometry | [pixel-attribution-needs-nearest-hit](../../knowledge/notes/pixel-attribution-needs-nearest-hit.md) |
| `Physics.Raycast` attribution | visible meshes (it hits collider proxies) | renderer toggle, then ray-triangle | [pixel-sweep-lighting-measurement-traps](../../knowledge/notes/pixel-sweep-lighting-measurement-traps.md) |
| Sweep over a fixed set of poses | corners no pose framed | add a pose framing every flagged area | same |
| Hue-masked mean | the object's real statistics | statistics over all its pixels | same |
| Sky-difference geometry mask | glass (counts as geometry) | exclude glazing by renderer | [difference-masks-count-glass-as-geometry](../../knowledge/notes/difference-masks-count-glass-as-geometry.md) |
| Downward brightness sampler | interiors (lands on roofs) | walkable floor with a ceiling, reachable cells | [interior-brightness-sampling-must-require-a-ceiling](../../knowledge/notes/interior-brightness-sampling-must-require-a-ceiling.md) |
| One shot per room | lighting (facing dominates) | at least 4 yaws, mean and spread | [sample-several-yaws-per-point-when-measuring-a-room](../../knowledge/notes/sample-several-yaws-per-point-when-measuring-a-room.md) |
| Level camera sweep | undercroft and overhang ceilings | sweep pitched up as well | [reviewer-findings-need-reachability-triage](../../knowledge/notes/reviewer-findings-need-reachability-triage.md) |
| Capture with occlusion culling on | moved static objects | `useOcclusionCulling = false` | [baked-occlusion-hides-moved-statics-in-captures](../../knowledge/notes/baked-occlusion-hides-moved-statics-in-captures.md) |

## 5. Measuring rendered frames

- **Lighting grade.** Eye-height station grid (the WORLD.md reference eye height), 4 yaws, mean
  luminance, dark % (L < 0.05), blown % (L > 0.9); keep one fixed pose for A/B across bakes and
  screenshot the worst station before "fixing" it
  ([objective-lighting-qa-with-a-luminance-station-grid](../../knowledge/notes/objective-lighting-qa-with-a-luminance-station-grid.md)).
- **Which renderer owns a pixel.** Toggle-diff the suspect, or swap an unlit magenta material onto
  it; bucket changed pixels by delta instead of averaging the feathered rim. For a near-black
  surface, count hemisphere-ray escapes: zero means the fix is geometry, not material
  ([toggle-diff-and-mask-pass-attribute-pixels](../../knowledge/notes/toggle-diff-and-mask-pass-attribute-pixels.md)).
- **Pixel sweeps.** Gate on two conditions (brightness and hue), hide UI by disabling `Canvas`
  components, compare thin members to the surface they abut, and scope toggle loops to one room:
  a scene-wide loop locks the editor past the MCP timeout. Report a number a later session can
  reproduce ([pixel-sweep-lighting-measurement-traps](../../knowledge/notes/pixel-sweep-lighting-measurement-traps.md)).
- **Visible area.** Key the judged surface's material, render from real player cameras, divide by
  the occluders-hidden render, then restore the material from version control; select by material,
  not by name ([measure-visible-surface-by-keying-its-material](../../knowledge/notes/measure-visible-surface-by-keying-its-material.md)).
- **Camera placement.** Raycast to the ground for height and linecast eye-to-target; offsets from a
  bounds centre on a slope put cameras inside rocks
  ([metrics-that-cannot-see-their-defect](../../knowledge/notes/metrics-that-cannot-see-their-defect.md)).

## 6. Handing work to a reviewer

What the brief contains and the order of reviews: review-protocol "Inputs the orchestrator must
give you" and "For the agent that dispatches reviewers". On top of that, the builder:

- Runs §2 on its own work first, so the reviewer finds design problems, not trivia
  ([get-every-generated-asset-independently-reviewed](../../knowledge/notes/get-every-generated-asset-independently-reviewed.md)).
- **Quotes** the art direction from the project's design document and passes reference image
  paths, never a paraphrase from memory; the reviewer has no other source
  ([quote-the-art-direction-never-paraphrase-it](../../knowledge/notes/quote-the-art-direction-never-paraphrase-it.md)).
- Names a failing case as an example and asks for the whole defect class to be swept
  ([subagent-brief-scope-becomes-ceiling](../../knowledge/notes/subagent-brief-scope-becomes-ceiling.md)).
- Attaches the scan output with its positive control (§3), and says where it deviated from a
  previous reviewer's number and why
  ([recompute-reviewer-suggested-coordinates](../../knowledge/notes/recompute-reviewer-suggested-coordinates.md)).
- In a sunlit exterior, says up front that no artificial lights are expected
  ([daylit-exteriors-need-no-artificial-lights](../../knowledge/notes/daylit-exteriors-need-no-artificial-lights.md)).
- Sends screenshots as JPEG or with the long edge capped near 1600 px, attaching only the ones
  discussed: request limits are in bytes, not tokens
  ([oversized-screenshots-hit-request-byte-limit](../../knowledge/notes/oversized-screenshots-hit-request-byte-limit.md)).
- Before any commit, bake or build: deletes every `__*__` capture object and asserts the
  realtime/mixed light count is 0; both checks, since either can miss alone
  ([sweep-leftover-capture-rigs-before-commit-or-bake](../../knowledge/notes/sweep-leftover-capture-rigs-before-commit-or-bake.md)).

## 7. Acting on findings

The loop itself (fix, re-bake, probes, re-review, three rounds then change approach) is in
review-protocol. Per finding:

1. Query the named objects' current state first; record already-fixed findings as closed with the
   measurement that proves it
   ([verify-review-findings-against-live-scene](../../knowledge/notes/verify-review-findings-against-live-scene.md)).
2. Check the cited camera pose against a reachability model; re-measure from the nearest
   reachable pose before re-baking hidden geometry
   ([reviewer-findings-need-reachability-triage](../../knowledge/notes/reviewer-findings-need-reachability-triage.md)).
3. Take the reviewer's diagnosis, recompute its numbers: coordinates against the bounds of every
   part of the assembly
   ([recompute-reviewer-suggested-coordinates](../../knowledge/notes/recompute-reviewer-suggested-coordinates.md)),
   rotations from measured facing, quoting the new measured facing as proof
   ([reviewer-rotation-values-are-inferred](../../knowledge/notes/reviewer-rotation-values-are-inferred.md)).
4. Never dismiss a finding because your own metric disagrees; check what that metric is blind to
   (§4, [phash-cannot-detect-aspect-distortion](../../knowledge/notes/phash-cannot-detect-aspect-distortion.md)).
5. Classify toggle-state findings in both states (§2 step 8), then prove the fix with a
   same-camera before/after (§1).
6. After a fix passes re-review, record symptom → cause → rule before the next task
   ([log-a-lesson-after-every-review-fix](../../knowledge/notes/log-a-lesson-after-every-review-fix.md)).
   Project facts go in the project's own instructions; promoting a lesson to a shared note follows
   world-pipeline "Lessons capture" ([SKILL.md](../world-pipeline/SKILL.md)).

## 8. Handoffs between agents

- **One editor, several sessions.** Worktrees do not isolate the editor. Re-query the hierarchy
  and confirm an object is yours before modifying or deleting it; after a long bake, import or
  batch edit, re-verify that the objects it covered still match what you built before measuring
  ([parallel-agent-sessions-in-one-unity-editor](../../knowledge/notes/parallel-agent-sessions-in-one-unity-editor.md)).
- **Editor scripts compile as one assembly.** Give each parallel agent exclusive ownership of its
  own script; blocked by someone else's `error CS`, check the file's modification time and wait,
  never stub it ([one-broken-editor-script-blocks-all-agents](../../knowledge/notes/one-broken-editor-script-blocks-all-agents.md)).
- **Subagent briefs.** Named cameras, objects and values become the ceiling of what gets checked.
  Name them as examples, ask for the class, and pass measured constants with the method to
  re-measure them locally
  ([subagent-brief-scope-becomes-ceiling](../../knowledge/notes/subagent-brief-scope-becomes-ceiling.md)).
- **Tell subagents the rule.** A builder passes its own work; say explicitly that a same-camera
  render is the proof, and route the result to a separate reviewer
  ([metrics-that-cannot-see-their-defect](../../knowledge/notes/metrics-that-cannot-see-their-defect.md)).
- **Reviewer briefs come from the dispatcher,** quoted from the design document; mid-run
  corrections go to the running reviewer as a message, with the difference called out as a finding
  ([quote-the-art-direction-never-paraphrase-it](../../knowledge/notes/quote-the-art-direction-never-paraphrase-it.md)).

## 9. What a "done" report carries

- Same-camera before/after image pairs, file paths and the pose used.
- Every number as a pair: result and positive control (or broken and good sibling), same poses,
  mask and threshold.
- Scan output with its final status line (`PAIRS=0 COMPLETE` for the z-fight gate).
- Findings closed, already-closed (with the proving measurement), pre-existing (with numbers from
  the other state), and deviations from reviewer numbers with the reason.
- The stage reviewer's verdict. Without SHIP IT the work is not done.

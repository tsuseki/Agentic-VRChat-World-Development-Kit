# Review protocol — shared by every reviewer agent

`layout-reviewer`, `dressing-reviewer` and `final-reviewer` all follow this file. Each agent file
adds only its own scope, criteria and verdict rules.

## Reviewers by stage

| Stage | Reviewer | Mode | Scores |
|---|---|---|---|
| A.3 Concept: shell layouts | `layout-reviewer` | rank the shell-layout blockouts in 3D (structure, massing, scale vs the reference eye height, world extent, divergence); the user picks layout + look | every option /10 |
| A.3 Concept: text-route images and style rounds | none | the user picks | — |
| B.1 Floor plan (zoning) | `layout-reviewer` | rank the zoning-plan variants inside the locked shells (no furniture) | every option /10 |
| B.2 Greybox | `layout-reviewer` | rank the variants in 3D from eye height (massing + rough furniture zones, world size limits), then judge the refined pick | every option /10, then `Score` |
| Concept art per area (before any area is built) | `dressing-reviewer` CONCEPT PICK, only for picks the user leaves open | rank the variants per view, pick the best; the user can overrule | every option /10 |
| C.1 Build-out (per pass) | `dressing-reviewer` | judge whatever the pass placed, in 3D: structures, shell finish, furniture (seating and layout rules), dressing; style match with the area's picked concept image (same style, not a copy), build quality and board match; decides lock gaps; never lighting. Structure passes also get `layout-reviewer` for massing, circulation and reach | `Style N/10 · Build N/10` |
| C.2 Interactions & playability | `dressing-reviewer` | judge the placed interaction objects | `Style N/10 · Build N/10` |
| D.1 Lighting | `final-reviewer` | DRAFT MOOD on the draft bake (mood vs the boards), then FINAL after bake + probe re-bake (lighting, polish, textures and sky, world extent); FINAL is the only upload gate (D.3). Runs only once the user calls for final lighting; quick bakes the user requests earlier get no review loop (`bakery-light-baking` "Baking rules") | `Score` |
| D.2 Performance | `final-reviewer` | PERF REGRESSION: what perf changes did to textures, the sky, merges, LODs and mirrors (same-camera before/after) | `Score` |

There is no separate style reviewer: world-architect pitches every A.3 option, the user judges
style at A.3 and picks concept art per area (dressing-reviewer picks what he leaves open),
dressing-reviewer checks style and board match on everything placed in C, final-reviewer checks
lighting and mood in D.1.

**Code-built complex geometry is a blocker (every reviewer, from C.1).** Any non-box shape (tank,
pipe, dome, truss, gate, machine, crystal, statue) built in Unity from primitives or
generator meshes instead of an imported asset (asset-finder, blender-modeler or Tripo) is a
blocker, whatever it scores otherwise (`.omp/RULES.md` rule 10). Say which source should make it.

## Role

- **You review; you do not fix.** Read-only except the capture rig (`__CapCam__`), temporary
  measuring aids and, in trials, the event log ("Trial logging"). Never move, edit or delete scene
  objects, change materials or lights, save the scene, or enter play mode. If you change something
  by accident, say so at the top of the report.
- **Temporary measuring aids** are allowed when a method needs them, all created with
  `hideFlags = HideFlags.DontSave` and removed in the same session: `MeshCollider`s added to
  visible meshes for ray methods, the scale figure (`__RevPerson__`, "Capture rig"), a briefly
  shortened LOD cross-fade, and in-memory A/B toggles on materials (`SetFloat`, `EnableKeyword`,
  zeroed `_EmissionColor`). Restore every value you changed. In-memory edits on shared material
  assets mark them dirty even when restored: call `EditorUtility.ClearDirty(mat)` after restoring.
- **End every review with a state report**: active scene `isDirty = False`, 0 `__*__` objects other
  than `__CapCam__`, 0 temporary colliders, 0 console errors, LOD cross-fade duration restored.
- **Critic, not cheerleader.** Your value is catching what the builder stopped seeing. Don't invent
  problems either: separate blockers from nits.
- You cannot ask the user questions. Work with the brief you were given and list the gaps under Caveats.

## Inputs the orchestrator must give you

1. **Stage** you are reviewing (stage ID, e.g. `C.1`) and the **world brief** path
   (`<project>/WORLD.md`): theme, mood, capacity, style decisions already approved, and its
   **Design Lock** table (`Design/lock/`).
2. **Target**: GameObject names, an area, or candidate roots (shotgun review).
3. Specific concerns, the latest z-fight scan and other scan output for the target, the previous
   report on re-reviews, and the screenshot output directory. The brief asks you to sweep the
   whole issue class, not only the one example named.

If the brief is missing, review general quality and state that brief adherence was not judged.

## Judge each area by its own archetype (every reviewer)

The rules you enforce live in `.omp/skills/spatial-design/references/spatial-design.md`; the builder works
to the same sections, so you and the builder share one set of criteria.

1. Read WORLD.md's **archetypes** (which areas are A1–A5, people per area) and its **reference eye
   height** (default 1.3 m). Missing archetypes → label each area yourself from spatial-design §1.1 and
   say so under Caveats.
2. Open spatial-design §1.5 (archetype → sections) and load the row for each area in your target,
   plus §4 when the target joins areas of different archetypes. Your agent file names the extra
   sections your stage owns.
3. Judge every area against **its own archetype** (§1.2): an A1 nook inside an A3 venue is judged by
   §3.1, not by A3 venue rules. Size and spacing numbers come from §3 and §5.11, scaled per §5.9
   from the reference eye height; never quote a fixed number from memory.
4. **Cite the spatial-design section** in every finding that rests on one (e.g. "§5.2: facing seats
   1.9 m apart, ≤1.07 m"). A deliberate deviation the user approved (recorded in WORLD.md Decisions,
   or built into the approved greybox) outranks the rule for that world; it is not a finding. A
   reference image alone never establishes a dimensional deviation ("Images are content and feel references").

## Images are content and feel references, not blueprints (every reviewer)

AI images don't translate into 3D: their perspective and parallax lines don't line up, their scale
is ambiguous and their layouts are often impossible. Never raise a finding because exact positions,
proportions or layout differ from an image; dimensions and circulation are judged only against
`SHELL_PICK`, the approved greybox and spatial-design, and furniture placement in 3D against
spatial-design and the pipeline skill's "Seating and layout rules (C.1)".

From every image that covers your target (lock images, the area's row in WORLD.md "Area
references", user references) judge **what is there** as well as mood, palette, materials,
lighting character and density:

1. **Content match.** Before judging, list the area image's signature pieces (e.g. "blast furnace
   with ladle, 2–4 overhead cranes, tracked hull in scaffolding, hydraulic press"). Each one missing
   from the build, or replaced by generic filler, is a **blocker**. Put the image next to your
   capture in the report.
2. **Distinctness.** When the target spans several areas or floors of different programmes, make
   one sheet with one matching shot per area. Two areas that read the same (same structure kit,
   same silhouettes) where their images differ is a **blocker**, whatever the massing scores.
3. **Missing target.** If the brief names no area image for an area that has a row in "Area
   references", or the row has no image yet, the verdict is NEEDS WORK with "no concept target":
   the area is not reviewable against content yet.

## Judging against the Design Lock (every reviewer)

After the A.4 approval (pipeline skill "Design Lock") the lock **is** the user's taste; judge the
target against it, not against what you would have picked.

1. Read WORLD.md's Design Lock table and `Design/lock/lock.json`. Open every lock image whose item
   or tags cover your target (the palette, materials and lighting boards, the overall/exterior
   views) next to your screenshots.
2. Every `feel` line is a criterion. A deviation from one is a finding: a **blocker** when it changes
   what the caption names (wrong palette family, a cool key where the board is warm, a sparse room
   where the board's density is full), a should-fix when it is a visible drift. Cite the lock file
   and the line.
3. Matching the lock is never a finding, even where you would choose otherwise; `free` lines bind
   nothing. The lock outranks the References table and general taste; it never outranks the plan
   JSON's dimensions, spatial-design's numbers or the collision minimums.
4. **Lock gaps.** A genuinely stylistic question the lock leaves open (the user would have an
   opinion; neither the lock, the brief nor your criteria settle it) is not a finding.
   `dressing-reviewer` decides it provisionally against the boards and reports it under **Lock
   gaps** with the options and the decision; other reviewers list it for dressing-reviewer to decide.

When ranking shell layouts, plans and greybox variants you score design candidates; the brief and the references are your
targets.

## Unity transport

Use the MCP for Unity tools your host exposes (`execute_code` with `compiler: roslyn`,
`find_gameobjects`, `read_console`, `set_active_instance`, ...). Reviewers never write project files
(the trial event log is the one exception).

**The editor freezes while `execute_code` runs and MCP gives up after ~10 s.** Keep every call
short. Never run an unbounded loop over scene triangles: an O(n²) scan froze the user's editor
with unsaved work. Use the agenttools package (`ZFightScan`, `WorldCapture`, `ZFightRender`,
`WorldAudit`; see `.omp/docs/unity-tools.md`), which is time-sliced and required.

## Before capturing

- Pin the instance: read the `mcpforunity://instances` resource; if more than one, call `set_active_instance`
  with the exact `Name@hash`. Confirm `Application.dataPath` is the project you were told.
- Confirm the target exists (`find_gameobjects`); record positions/bounds to frame shots. A
  missing target is the finding, not a reason to review something else.
- `read_console` once (`{"action":"get","types":["error"],"count":"20","format":"plain"}`, or
  `"format":"detailed","include_stacktrace":true`); note compile errors (they can break capture).
  An `ObjectDisposedException` from `UnityEditor.Search.PropertyDatabase.MergeStoresToFile` is
  editor noise, not a finding.
- Never open a scene from a review call: opening a large world scene outlasts the MCP window. Ask
  for the scene to be open.

## Capture rig (Unity)

Preferred: `WorldCapture.Shoot(outDir, shotsJson)` then poll `WorldCapture.Status()` until it
reports `COMPLETE`; it implements the camera rules below **except LOD settling** (do that first, as
below, and list each pose twice). Manual fallback:

Reuse one persistent `__CapCam__`. **Creating a temp Camera + RenderTexture and
`DestroyImmediate`-ing the camera after `Render()` SIGSEGVs the editor on the next repaint.** The
camera is `DontSave`, so it never dirties or saves with the scene, but `GameObject.Find` can't see
it once it is hidden or the scene was reloaded: find it by name with
`Resources.FindObjectsOfTypeAll<Camera>()` (the same camera `WorldCapture` uses), or every call
creates a duplicate.

```csharp
Camera cam = null;
foreach (var c in Resources.FindObjectsOfTypeAll<Camera>())
    if (c != null && c.name == "__CapCam__" && !EditorUtility.IsPersistent(c)) { cam = c; break; }
if (cam == null) {
    var go = new GameObject("__CapCam__") { hideFlags = HideFlags.DontSave };
    cam = go.AddComponent<Camera>();
}
cam.enabled = false;                     // manual renders only
cam.useOcclusionCulling = false;         // baked occlusion hides moved statics
cam.fieldOfView = 60f;
cam.nearClipPlane = 0.03f; cam.farClipPlane = 2000f;
// per shot:
cam.transform.position = new Vector3(10f, 1.6f, -4f);
cam.transform.LookAt(new Vector3(12f, 1.2f, -2f));
var rt = RenderTexture.GetTemporary(1600, 900, 24);
cam.targetTexture = rt; cam.Render();
RenderTexture.active = rt;
var tex = new Texture2D(1600, 900, TextureFormat.RGB24, false);
tex.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0); tex.Apply();
System.IO.File.WriteAllBytes(@"<outdir>\01_wide.png", tex.EncodeToPNG());
RenderTexture.active = null; cam.targetTexture = null;
RenderTexture.ReleaseTemporary(rt);
UnityEngine.Object.DestroyImmediate(tex);   // the texture may be destroyed; the CAMERA never
```

- Batch several shots per `execute_code` call (loop over pos/lookAt/name tuples), within the time limit.
- **Hardcode float literals.** The editor may run under a comma-decimal locale: `float.Parse("172.5")` gives 1725.
  Parse/format with `CultureInfo.InvariantCulture`.
- **Never add a light** to the rig or scene unless your agent file explicitly permits it. A rig light
  shows up in the user's live Scene view. Too dark to judge placement → brighten a `*_b.png` copy
  in post (PIL `ImageOps.autocontrast`) and say so.
- Leave `__CapCam__` in place; never save the scene. The orchestrator sweeps `__*__` objects
  before any commit, bake or build.
- After a reimport the first capture may be stale. Take a throwaway shot first.
- **Settle the LOD cross-fade before every capture.** Grey dither on trees right after the camera
  jumps is the LOD cross-fade (a freshly re-registered LODGroup also starts mid-fade), not a
  defect. In the capture call: `float old = LODGroup.crossFadeAnimationDuration;
  LODGroup.crossFadeAnimationDuration = 0.001f;`, render each pose twice (or 2–3 throwaway `_warm`
  shots) and keep the last, then restore `old` (Unity default 0.5) in the same call. Unsettled, LOD
  dither or mixed LOD levels land in A/B frames as false diffs. For a hide-and-diff over many views,
  freeze fades the same way before diffing.
- **Same rig settings every round**: rendering path, MSAA (8 for beauty, 1 for the lightmap-only
  pass), HDR, resolution and FOV stay fixed across a review's rounds, or the settings change shows
  up as a diff.
- **Scale figure** (layout and dressing shots, and any finding about size):
  `GameObject.CreatePrimitive(PrimitiveType.Capsule)` named `__RevPerson__`,
  `hideFlags = HideFlags.DontSave`, its collider destroyed at once, scale (0.4, 0.7, 0.4) = a 1.4 m
  person, `y = floor + 0.7`. Destroy it after the shots.
- **Top-down site shots**: camera 14–26 m above the site centre, look point offset by z + 0.01 so
  `LookAt` doesn't degenerate on a straight-down view. Check every pose isn't inside geometry
  (raycast down from the camera; a pose inside a wall renders as a wall).
- **Scratch files** (`_warm.png`, test frames): delete them with a shell `rm` outside Unity; the
  `execute_code` safety check rejects `System.IO.File.Delete`.

Blender targets: `get_objects_summary`, then `render_viewport_to_path` front/side/¾/close-up. Use
`execute_blender_code` only to frame the camera.

### Lightmap-only render (no albedo)

A capture camera can't use the Scene view's "Baked Lightmap" draw mode. Render with a replacement
shader instead, built and destroyed in the same `execute_code` call:

```csharp
var sh = ShaderUtil.CreateShaderAsset(src);       // src = the shader text below
Shader.SetGlobalFloat("_RevLMScale", 0.25f);      // 0.25 for bright outdoor bakes; 1 for interiors
var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB, 1);
cam.targetTexture = rt; cam.RenderWithShader(sh, "RenderType");
// ReadPixels / EncodeToPNG as above, then:
UnityEngine.Object.DestroyImmediate(sh);
```

```
Shader "Hidden/RevLMOnly" {
  Properties { _MainTex ("", 2D) = "white" {} _Cutoff ("", Float) = 0.5 }
  CGINCLUDE
  #include "UnityCG.cginc"
  float _RevLMScale; sampler2D _MainTex; float4 _MainTex_ST; float _Cutoff;
  struct a2v { float4 pos : POSITION; float3 n : NORMAL; float2 uv : TEXCOORD0; float2 uv1 : TEXCOORD1; };
  struct v2f { float4 pos : SV_POSITION; float2 lm : TEXCOORD0; float3 n : TEXCOORD1; float2 uv : TEXCOORD2; };
  v2f vert (a2v i) { v2f o; o.pos = UnityObjectToClipPos(i.pos);
    o.lm = i.uv1 * unity_LightmapST.xy + unity_LightmapST.zw;
    o.n = UnityObjectToWorldNormal(i.n); o.uv = TRANSFORM_TEX(i.uv, _MainTex); return o; }
  fixed4 shade (v2f i) {
  #ifdef LIGHTMAP_ON
    return fixed4(DecodeLightmap(UNITY_SAMPLE_TEX2D(unity_Lightmap, i.lm)) * _RevLMScale, 1);
  #else
    return fixed4(ShadeSH9(float4(normalize(i.n), 1)) * _RevLMScale * float3(1, 0.55, 1), 1); // probe-lit = pink
  #endif
  }
  fixed4 fragO (v2f i) : SV_Target { return shade(i); }
  fixed4 fragC (v2f i) : SV_Target { clip(tex2D(_MainTex, i.uv).a - _Cutoff); return shade(i); }
  ENDCG
  SubShader { Tags { "RenderType"="Opaque" }
    Pass { Tags { "LightMode"="ForwardBase" } Cull Off
      CGPROGRAM
      #pragma vertex vert
      #pragma fragment fragO
      #pragma multi_compile _ LIGHTMAP_ON
      ENDCG } }
  SubShader { Tags { "RenderType"="TransparentCutout" }
    Pass { Tags { "LightMode"="ForwardBase" } Cull Off
      CGPROGRAM
      #pragma vertex vert
      #pragma fragment fragC
      #pragma multi_compile _ LIGHTMAP_ON
      ENDCG } }
}
```

- Lightmapped pieces show their baked light only; probe-lit pieces show pink, so a renderer that
  lost its lightmap binding stands out.
- At ×0.25 the sampled value doubles as a lightmap-intensity read (sRGB 162/255 at ×0.25 ≈ 1.4×
  linear).
- Blind spots: Unity terrain renders flat grey (its lightmap UV is not uv1), and custom
  vertex-pulled shaders (merged ground-cover cells) don't draw at all; judge those from beauty
  shots. Where a back face fills the frame, use a `Cull Back` variant.
- Shaders with world-space noise (terrain splats) mottle albedo differently in two copies of an area
  at different world positions. Before calling a beauty brightness difference between two copies
  (world vs a promo copy) lighting, compare them in this pass.

## Shot discipline

- **Player eye level from where players actually stand** is the view that matters most: the
  reference eye height in WORLD.md (default 1.3 m). Every review includes it.
- Wide establishing shot, close-ups of junctions (object meets floor/wall), reveal angles
  (skimming/low diagonals) that expose intersections, floating props and z-fighting.
- Interiors: at least two opposite corners. Shotgun reviews: **the same camera set relative to each
  candidate's origin**, so the comparison is fair.
- **Read every screenshot.** Every claim in the report cites a screenshot or a measured value.
- **Your own poses, re-used verbatim.** Record every pose in the report as a pose string
  `name|x,y,z[,g]|pitch,yaw|fov|near|far` (`g` = y is raycast-to-ground plus that height). On a
  re-review, re-shoot your previous round's pose strings exactly; the builder's poses and numbers
  never stand in for yours. A builder's "0 % clipped" read 1.35 % at the reviewer's pose, and "not
  visible from the landing" was false at the reviewer's camera.
- **Repeated structures: shoot every instance**, not one. A defect the builder checked at one
  instance showed at three of the four others.

## Verdict and score

Every review ends with a verdict **and** a score out of 10 with the reasons for it:

```
Verdict: SHIP IT | MINOR FIXES | NEEDS WORK
Score: N/10 — <the reasons: what earns the points, what costs them>
```

`dressing-reviewer` gives two scores instead of one, so trials can show which half the user
disagrees with: `Style N/10 · Build N/10` (style = board match: palette, materials, density, mood;
build = geometry, placement, junctions, finish, z-fighting).

- **SHIP IT**: no blocker and no should-fix finding for this stage, **and** score ≥ 8 (both
  dressing scores ≥ 8).
- **MINOR FIXES**: should-fix findings only.
- **NEEDS WORK**: at least one blocker.
- **The score never overrides findings.** A 9/10 with a should-fix is MINOR FIXES. A score below 8
  with no blocker or should-fix is inconsistent: name what holds it back as findings.
- **Rankings** (A.3 shell layouts, B.1 plans, B.2 variants) report `RANKED`, score **every option** /10
  with its reasons, and order them best first. Equal scores need a stated tiebreak.
- Scores are comparable across passes on the same target: a re-review states the previous score
  and why it moved.
- Your verdict covers **your stage only**. Only `final-reviewer` can sign a world off.
- Re-review after fixes: check every previous finding by number (fixed / not fixed / regressed)
  before looking for new ones, at your previous round's poses, with r(n−1) vs r(n) sheets cut from
  the same crop boxes.

## Report format

- **Stage / mode**: the stage ID and what you were asked, and anything you downgraded (e.g. unbaked
  scene sent to final).
- **Verdict** plus a one-sentence justification.
- **Score**: `N/10` (dressing: `Style N/10 · Build N/10`; rankings: every option /10) with its reasons.
- **What works**: 2–4 specific strengths.
- **Passed because** (SHIP IT and a ranking's winner): the specific reasons it passes, each citing a
  screenshot, a measurement, a lock `feel` line or a spatial-design section. They are logged and
  checked against the user's verdict in trials.
- **Issues**, numbered, ordered by severity. Each: severity (**blocker / should-fix / nit**), exact
  object name(s) and location, the area's archetype and the spatial-design section it breaks (when
  one applies), what's wrong, a concrete fix, and the screenshot that shows it.
- **Previous findings** (re-reviews only): status per number, and the previous score.
- **Screenshots**: directory, plus a one-line caption per file.
- **Caveats**: what you couldn't judge.
- **State at hand-back**: the end-of-review state report ("Role").
- **Lock gaps** (if any): the open stylistic question, the options, and dressing-reviewer's
  provisional decision against the boards.

Default screenshot directory: `<project>/Design/reviews/<stage>-<target>-<nn>/` inside the world's
project (`mkdir -p` it), never the system temp folder: the user opens review images from the
project (user, 2026-10-13). Use descriptive file names: `02_eyelevel_from_door.png`. Keep one shot
folder per round (`r2/shots/`, `r3/shots/`): it is the next round's "before" set, so keep the pose
strings and crop boxes in the report.

## Trial logging

During a pipeline trial (`<project>/Trial/log.jsonl` exists, or the brief says so), append one
`review` event per verdict with `python .omp/skills/pipeline-trial/scripts/trial_report.py
<project>/Trial --append -`: stage ID, reviewer, mode, round, target, verdict, **`score`** (0–10;
required except on `RANKED`; dressing-reviewer gives its overall score here),
**`scores` {`style`, `build`}** (dressing-reviewer), **`option_scores`** {option
id: 0–10} on `RANKED` (every option), ranking, every finding with its severity, reason, fix,
section and screenshot paths, the **passed because** reasons, and a `lock_gap` event per lock gap.
The script copies your screenshots into `Trial/img/`. The user then marks each call agree or
disagree and may give their own score; the report shows the difference. This log is the one file a
reviewer writes; schema in `.omp/skills/pipeline-trial/SKILL.md` "Event log".

## For the agent that dispatches reviewers and acts on verdicts

The gate itself is in `.omp/AGENTS.md` "Visual acceptance gate"; this is how to run it.

1. **Order**: model → import/place → material → lighting bake → reflection probes → final review.
   `dressing-reviewer` may catch geometry/placement issues early but cannot sign off lighting.
   `final-reviewer` judges mood on a draft bake (D.1) before the final bake, and signs off only after
   the final bake and probe re-bake; realtime helper lights/unbaked scenes are not final evidence.
2. **Brief** with everything under "Inputs" above: `WORLD.md` path/art direction, exact
   GameObjects/area, concerns, the latest z-fight scan and other scan output, the previous report on
   re-reviews; optionally a screenshot directory. Ask the reviewer to sweep the whole issue class,
   not only one example.
3. **NEEDS WORK / MINOR FIXES means fix and re-review** (pipeline skill "Plan → Build → Review
   loop"): the findings plus the area's unfinished work become the next pass plan. Close every
   blocker and should-fix; leaving nits requires the user's decision. Open each finding's screenshot
   before fixing, check player reachability, and inspect rendered before/after evidence. Re-bake the
   affected area after fixes that affect its bake, including lighting/material changes; then bake
   probes and re-review.
4. After three consecutive revision/review rounds with no improvement on the same findings, change
   approach. If no actionable alternative exists, report blocked with unresolved findings, evidence,
   attempted fixes and the missing asset/tool/user decision. Never waive findings or lower
   acceptance to claim completion.

# Draw-call attribution: by root AND by category

The root sweep (`perf-optimizer` Procedure step 3) answers "which part of the world costs most".
Owners usually ask the other question: "what *kind* of thing costs most" (glass, railings, lamps,
games, furniture, pictures). Give both. The category view is what turns a red total into a fix
list: in a measured penthouse world the rooms all looked alike by root, but by category the top
rows were light-fixture hardware (~260 draws), glass panes and frames (~260), built-ins (~110) and
railings (~80), while the owner's suspect, the garden trees, cost ~10.

## 1. Capture one frame with object names

1. Play mode, worst viewpoint, content phase recorded (downloaded images, active games).
2. Enable the Frame Debugger, read every event, then **disable it before any timing sample**
   (it freezes the frame).
3. The MCP adapter can return marker-only names (`RenderForwardOpaque.Render`). Then read the
   event descriptors by reflection, read-only: `UnityEditorInternal.FrameDebuggerUtility` →
   the event array; each descriptor has `m_Type` (Mesh, StaticBatch, InstancedMesh,
   DynamicGeometry, Clear, Resolve…) and `m_Obj` (the instance ID of the renderer's object). Map
   `m_Obj` → `EditorUtility.InstanceIDToObject` → full hierarchy path.
4. Save the raw list as JSON, one object per event:
   `{"index", "type", "name", "path", "root", "obj"}`. Keep it as evidence; every later grouping
   is recomputed from it.

## 2. Group by category

`python .omp/skills/vrchat-world-optimization/scripts/draw_categories.py events.json`
groups draw events with the default rules (first match wins, order matters) and prints a ranked
table with examples per category. Pass `--rules my_rules.json` to adapt names to a world
(`[["Category", "regex"], ...]`), `--split "Category"` to drill into one category by its
sub-paths, `--json out.json` to save it.

Read the table with its limits:

- **`StaticBatch` events carry no single object.** Report them as their own row
  ("static batches, not attributable"); never spread them over categories. A large row means
  Unity already merged a lot; what is left in the named rows is what it could *not* batch.
- **Events ≠ `UnityStats` draw calls.** Quote both; rank with events, budget with draw calls.
- Keyword rules misfile a few objects (a `MidRail` under lights, a light switch under fixtures).
  Spot-check every category's examples before you quote it, and say "approximately".
- A category count is not a saving. Confirm the top categories with the toggle sweep (disable the
  category's renderers in play mode, re-sample) before promising a number.

## 3. Why named objects did not batch (check before fixing)

For each top category, sample its renderers and record what breaks batching:

| Cause | Check | Fix direction |
|---|---|---|
| Transparent material | `renderQueue >= 2500` | never batched by Unity; merge only coplanar same-facing pieces ([merging.md](merging.md) "Transparent") |
| Different materials per piece (trim + emissive diffuser, per-room tuned material variants) | distinct `sharedMaterial` per renderer | one merged mesh per material per room |
| Different lightmap pages | `lightmapIndex` differs | split merges per lightmap index |
| Not static / batching flag off | `GameObjectUtility.GetStaticEditorFlags` | set flags only where the object never moves |
| Different reflection probes / probe anchors | `probeAnchor`, blended probes | group per probe zone |
| Same probe on paper, different in the shader | Frame Debugger "different reflection probe"; `unity_SpecCube0_BoxMin.w` reads e.g. 0.9999998 vs 1 | set `Renderer.probeAnchor` to one shared point per group (no re-bake) |
| Instanced repeats not instancing | lightmapped instances on > 1 lightmap index; terrain trees under a `WindZone` (per-tree `_Wind`); renderer also static-batched | one lightmap page for the group (one 2K beat two 1K); hand-placed prefabs + sway shader instead of terrain trees; choose instancing OR static batching per asset, never both [Chrono Cabin 2024] |
| Multi-part assets (post, cap, shoe, rail as separate objects) | child count under one asset | merge per assembly run |

Typical expensive classes, all invisible in triangle counts: modular railings, lamp hardware
split into trim + diffuser, glazing split per pane and per face, shelves of individual bottles or
books, server racks of individual units.

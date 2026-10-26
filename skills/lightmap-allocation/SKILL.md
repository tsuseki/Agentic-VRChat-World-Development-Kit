---
name: lightmap-allocation
description: "Decide which renderers get lightmap texels and how many, and catch broken allocation before and after a bake, for VRChat worlds (Unity 2022.3 Built-in RP; Bakery first, GLIM or Progressive as fallbacks; VRC Light Volumes). Covers the per-class reception table (lightmapped / probe- or Light-Volume-lit but still casting / dynamic), texel-density targets, Scale In Lightmap and chart-share maths, lightmap groups, UV2 quality (import margin, Blender-authored UV2, per-material share, overlap, organic meshes), the measured pre-bake audit with thresholds and the post-bake binding and visual checks. Use when: preparing any lightmap bake or a C.1 piece for baking, setting receiveGI / ContributeGI / Scale In Lightmap / lightmap groups, importing or unwrapping models for lightmapping, glass or transparent meshes take atlas space, pillows, cushions, bedding or sculptures bake faceted or torn, parts of one object (trunk vs branches) bake different colours, one object eats an atlas, too many lightmaps, overlapping-UV warnings, or reviewing bake quality object by object."
---

# Lightmap allocation

A bake can only be as good as the texels each surface receives. Most "bad bake" reports in this
workspace were allocation faults, not sample counts:
- thin glass ate the atlas;
- fragmented UV2 tore pillows into dark facets;
- one material got 3 % of its mesh's UV2;
- a hidden envelope took 68 % of an atlas;
- the importer's margin left UV2 90 % empty.

This skill decides, **before** baking, what is lightmapped and how densely, and it proves the
allocation by measurement and near-reach renders afterwards. Bake settings, emitters, probes and
artifact diagnosis stay in `.omp/skills/bakery-light-baking/SKILL.md`.

## 1. Reception: who gets texels

Three modes per renderer:

| Mode | Settings | Gets |
|---|---|---|
| **L** lightmapped | static `ContributeGI`, `receiveGI = Lightmaps`, valid UV2, a lightmap group | baked direct + GI, contact shadows, its own chart |
| **P** probe/LV-lit, still casting | `ContributeGI`, `receiveGI = LightProbes`, `BlendProbes`; LV-aware material in Light Volume worlds; no group selector, no storage row | casts and occludes in the bake, lit by probes/volumes, no atlas space |
| **D** dynamic | not static, `BlendProbes` (LV material in LV worlds) | nothing baked; moves |

Workspace default (the user's rules). A world may change any row; record it with the user's words
in that world's `WORLD.md` Decisions log, and then `WORLD.md` wins.

| Class | Mode | Key rule |
|---|---|---|
| Walls, floors, ceilings, shell, built-ins | L | hero area group; hidden backs and exterior envelopes demoted (§2) |
| Large furniture (> ~0.4 m): sofas, beds, tables, cabinets, lamp bodies, rugs, big plants and pots, statues | L | UV2 must pass the audit; otherwise re-unwrap, never move to probes to dodge it |
| Small hard decor (≤ ~0.4 m): taps, bottles, fruit, souvenirs, small figurines, books on shelves | L if its UV2 passes the audit and its short side gets ≥ 8 texels; otherwise P (LV in LV worlds) | user: "only small props can go with lightvolumes", "small objects should move to light volumes if [the lightmap is] broken" |
| Soft or organic small pieces: pillows, cushions, throws (≤ ~0.6 m), small sculptures | same rule; their auto UV2 almost always fails the audit, so expect P (LV) | incident: about 800 of 2,379 small renderers had fragmented auto UV2 |
| Anything under ~0.12 m in its middle dimension | P | no margin rescues a 1–2 texel chart |
| Flush wall fittings < ~20 cm (switches, outlets, vents) | P | 4 × 3 texel charts bake half-black smears |
| Glass, transparent, glazing | P, `ReflectionProbeStatic` off | thin panes demand huge charts and gutter-bleed onto the view |
| Cutout foliage: hero trees | L with hand-built Lightmap UV (bark budget) | auto unwrap gives bark ~3 % of the UV2 |
| Cutout foliage: scatter, small plants | P | grass under baked tree shadows: L or ground-lightmap sampling |
| Light meshes and emitters (`BakeryLightMesh`) | never L (Bakery skips them); no selector | split emitter child from a lightmapped body when the body must be lit |
| SSS shades | L in their own `computeSSS` group, generous scale (~6) | closed volume, shadows On |
| Pickups, Udon-moved and animated parts | D | ambient sway: keep L and move vertices in the shader |
| Mirrors, video screens | not `ContributeGI`, not L | they bake as coloured area lights or hang Progressive |
| Far scenery, skyline, backdrops | L in one small shared group, or P/off outside the probe hull | never in a hero group |
| LOD levels | L per LOD level group (Bakery `sceneLodLevel`), LOD1/2 discounted; or P | GLIM bakes hand-authored LOD0 only |
| Merged / batched meshes | bake the originals; merges reuse each source's UV2 and scale-offset | merged-only defects block the merge chain |
| Terrain | L, every tile in a group | hero tiles need full-range UV2 |
| Pack furniture without UV2 | P until given UV2, then L | P still casts contact shadows |

Full table with reasons and settings: [references/reception-and-density.md](references/reception-and-density.md) §1.

## 2. Budget and density

- **Density targets** (effective texels/m, 1 unit = 1 m):
  - hero interior shell 20–40;
  - furniture players sit or lie on 30–60;
  - exterior play ground and garden furniture 10–30;
  - background terrain and far facades 1–5;
  - hidden backs at Scale In Lightmap 0.1, or 0 (occluder only).
- **Short-side minimum:** every lightmapped piece gets **≥ 8 texels across the short side of its
  main face**. Below that, raise Scale In Lightmap (usually ≤ 8; past that, fix the UV2 or change
  reception).
- **Chart share** of a renderer = `lightmapScaleOffset.x × .y` of its atlas. It grows with
  `scaleInLightmap²`, so doubling a scale quadruples the share. Inside one group Scale In Lightmap is
  a relative share: raising one renderer thins all the others in a fixed-resolution group.
- **Groups:**
  - a few explicit groups, zero ungrouped renderers;
  - a fixed-resolution group (e.g. 2048) per hero area;
  - one small shared fixed group (e.g. 512) for background and terrain;
  - SSS in its own group;
  - one group per LOD level;
  - probe-lit renderers carry no selector.
- **Padding:** gutters measured in texels at the final resolution ≥ padding + 1. Bakery texel
  padding 8 on hero groups.

Maths, per-class table and VRAM: [references/reception-and-density.md](references/reception-and-density.md) §2–§4.

## 3. UV2 quality

- **Import:** *Generate Lightmap UVs* with margin method **Manual** (pack margin ~6), never
  Calculate at a low minimum resolution.
- **Blender-authored UV2** for hero furniture, trees, organic and multi-material pieces: few large
  flat charts, area shares set by allocation, not raw surface area. Import with *Generate Lightmap
  UVs* off and keep Bakery's UV processing from overriding it.
- **Per-material parity:** each submesh's UV2 share should be near its surface-area share.
- UV2 inside 0–1, finite, non-overlapping. Charts ÷ triangles well below 1.0.
- **Organic meshes:** flat-chart unwrap with few charts, or don't lightmap them.

Details: [references/uv2-quality.md](references/uv2-quality.md).

## 4. Pre-bake audit (measured)

Run it on every lightmapped renderer of the baked area. Flag a renderer when:

| # | Check | Flag |
|---|---|---|
| 1 | Tiny triangles | > 30 % of UV2 triangles under 0.01 texel² |
| 2 | Fragmented charts | > 50 % of charts under 4 texels (√ chart area) |
| 3 | Per-material starvation | a submesh with ≥ 10 % of the surface area and < 5 % of the UV2 area |
| 4 | Atlas hogs | top 10 renderers by chart share per atlas; any hidden, exterior-back or far renderer > 2 %; any renderer > 10 % without a reason |
| 5 | Transparent still lightmapped | render queue ≥ 2500, Transparent/Fade mode, or a glass/window/glazing material |
| 6 | Too small to lightmap | largest bounds < 0.12 m, or middle < 0.12 m with fewer than 12 texels across it |
| 7 | Short side | < 8 texels across the main face's short side |
| 8 | UV2 validity | missing, outside 0–1, NaN; charts ÷ triangles ≥ 0.9 |
| 9 | Groups | ungrouped lightmapped renderers; probe-lit renderers with a selector; LOD renderers without a per-level group |
| 10 | Gutters | < padding + 1 texels at final resolution |

Each flag gets a fix:
- change reception (§1);
- re-unwrap (§3);
- change scale or group (§2);
- or a written reason in the bake report.

**Tooling:** use the `com.awdk.agenttools` lightmap UV2 audit when the package has one. Otherwise use
the project's own editor script with a static `Run(rootPath, outTsv)` that writes one row per
renderer with the metrics above. Metric definitions and the time-budgeted loop:
[references/audit.md](references/audit.md) §1.

## 5. Post-bake checks

- **Bindings:**
  - every lightmapped renderer has a valid index and a finite scale-offset;
  - nothing sits on a 16×16 map;
  - the storage `maps` count equals the live count;
  - clones and renderers placed since the bake count as unbaked;
  - never hard-code lightmap ids, which shift when a group is added or emptied.
- **Visual:**
  - a lightmap-only render of each room;
  - near-reach shots (≤ 0.6 m, eye height) of every soft or organic piece and every audit-flagged
    renderer;
  - merged vs unmerged originals from the same views.
- **Positive control:** the same rig on one known-bad piece (an unfixed flagged renderer, or a copy
  at Scale In Lightmap 0.1) must show the defect. Quote both results.
- **Gate:** the final-reviewer is the gate.

Procedure: [references/audit.md](references/audit.md) §2–§3.

## Stage hooks

- **C.1 Build-out:** set reception and scale per §1–§2 as each piece is placed. Fix UV2 at import.
- **D.1 before every final bake:** run the §4 audit and attach the TSV and flag counts to the bake
  report.
- **D.1 after the bake:** run the §5 checks, then bake the reflection probes.
- **final-reviewer criterion 2** reruns §4 and §5 on the area.

Lessons checklist (one rule per note): [references/lessons-lightmap-allocation.md](references/lessons-lightmap-allocation.md).
Sources: `SOURCES.md` (not needed to use the skill).

# Allocation audit: before and after the bake

Numbers locate allocation defects; renders decide them. Every audit run reports its flag counts next
to near-reach shots of the flagged pieces, and a zero result is quoted only with its positive
control.

## 1. Pre-bake audit

### Running it

- Use the `com.awdk.agenttools` lightmap UV2 audit when the installed package has one (see
  `.omp/docs/unity-tools.md`).
- Otherwise use the project's own editor script with a static `Run(rootPath, outTsv)`. It takes a
  scene root path and an output path, writes one TSV row per renderer under the root and returns the
  flag counts.
- Write numbers with `CultureInfo.InvariantCulture`; a comma-decimal locale breaks every later parse.
- Long scenes run through the package's `Start`/`Status` job pattern. Give the triangle loop a time
  budget, because an unbounded loop over scene geometry freezes the editor.
- The audit is read-only. Fixes are a separate, scoped pass. Before a bulk fix, snapshot every
  renderer's `lightmapIndex` and compare the expected touch count with the actual one.

### Per-renderer columns

| Column | Definition |
|---|---|
| path, mesh, materials | hierarchy path, mesh asset, material per submesh |
| mode | L / P / D from `ContributeGI`, `receiveGI`, static flags |
| group | Bakery selector `lmgroupAsset` name (searched up the parents), or none |
| bounds | world AABB sizes sorted: small, middle, large |
| worldArea, uv2Area | sums over triangles; world positions include the transform |
| T | texels per UV unit: after a bake `atlasSize × sqrt(so.x × so.y)`, else `res × scaleInLightmap × sqrt(worldArea / uv2Area)` |
| texelsPerM | `T × sqrt(uv2Area / worldArea)` |
| tinyTriFrac | fraction of UV2 triangles with `uv2TriArea × T² < 0.01` |
| charts, tinyChartFrac | charts are connected components of the triangle graph by shared UV2 vertex index (union-find over `mesh.triangles`); size = `sqrt(chartUv2Area) × T`; fraction under 4 |
| chartsPerTri | charts ÷ triangles |
| worstSubmesh | lowest `uv2Share / areaShare` with its two shares |
| share | `so.x × so.y` after a bake, else the estimated share of the group's atlas |
| shortSideTexels | `T × sqrt(uv2Area / worldArea) × middle bounds dimension` (texels across the main face's short side) |
| minGapTexels | smallest gap between chart bounding boxes × T (only for meshes ≥ ~1.3 m, sampled if large) |
| uv2Valid | present, inside 0–1, finite |
| transparent | any material with render queue ≥ 2500, Standard Fade/Transparent mode, or a glass/window/glazing name |

### Flags and what each one gets

| Flag | Threshold | Default fix |
|---|---|---|
| FRAG_TRIS | `tinyTriFrac > 0.30` | small or soft piece → P; large piece → re-unwrap (uv2-quality.md §2, §5) |
| FRAG_CHARTS | `tinyChartFrac > 0.50` | same as FRAG_TRIS |
| SUBMESH_STARVED | a submesh with `areaShare ≥ 0.10` and `uv2Share < 0.05` | weighted re-pack or split the part |
| HOG | top 10 by share per atlas; hidden, back or far renderer `share > 0.02`; any `share > 0.10` without a stated reason; `T` larger than the atlas | demote Scale In Lightmap (0.1 for hidden), move to the background group, or P |
| TRANSPARENT_L | transparent and `receiveGI = Lightmaps` | P |
| TOO_SMALL | `large < 0.12 m`, or `middle < 0.12 m` and `shortSideTexels < 12` | P |
| SHORT_SIDE | `shortSideTexels < 8` on an L renderer | raise Scale In Lightmap (usually ≤ 8), else P or re-unwrap |
| UV2_INVALID | no UV2, any value outside 0–1, NaN or infinite | regenerate; a single one can break its whole group |
| DUP_TRIS | `chartsPerTri ≥ 0.9` | dedupe and weld, re-unwrap |
| GUTTER | `minGapTexels < padding + 1` at the final resolution | widen margin, then trim scale |
| UNGROUPED | L with no selector (Bakery scenes with explicit groups) | add a selector |
| SELECTOR_ON_P | P renderer carrying a selector | remove (it can bake an empty atlas) |
| NON_LV_SHADER | P or D renderer whose material shader is not LV-compatible (`Light Volume Samples/*`, lilToon, Poiyomi or another listed one), e.g. Standard | assign an LV copy of the material (`<name>_LV.mat`) |
| LOD_GROUP | renderer in a `LODGroup` whose group has `sceneLodLevel = -1` | one group per LOD level |
| GI_SCREEN | mirror or video/runtime screen with `ContributeGI` | clear the flag |

Report: flag counts per area; the top 10 hogs per atlas with their shares; every flagged renderer
with its fix or a one-line reason to keep it. Re-run the audit after the fix pass. The flag counts
must fall, and the count of renderers you touched must match the plan.

## 2. Post-bake binding checks

Run them after save, close and reopen, so you check what will ship:
- **Scale-offsets:** every L renderer has `0 ≤ lightmapIndex < 65534` and a **finite**
  `lightmapScaleOffset`. Also check the `bakedScaleOffset` list in Bakery's storage.
  - An infinite or NaN offset anywhere means a bad UV2 in that group. Expect exactly one culprit
    mesh.
- **Orphans:** no renderer sits on a 16×16 map with scale-offset `(1,1,0,0)`. That is an ungrouped
  object that baked flat or black.
- **Map counts:** the storage `maps` count equals `LightmapSettings.lightmaps.Length`. An empty storage
  saved after a failed or selected bake is what makes the whole world render flat in Play.
- **Index meaning:** `lightmapIndex` is only meaningful right after a bake: −1 means not baked, 65534
  means not lightmapped (P or D).
  - Renderers placed or cloned since the last bake are unbaked, whatever their copied index says. A
    clone keeps its source's serialized index and offset; Bakery's storage has no row for it.
  - Renderers moved to P need their storage row removed, or Bakery restores the old binding at load.
- **Never hard-code lightmap ids.** Adding a group adds a map and shifts the ids after it; an emptied
  group drops out. Check by renderer path ("bound to some valid map"), never "bound to id 5".
- **Expected atlases:** compare the count with the plan. One extra map is the first sign of an orphan
  terrain tile or a group of only P renderers.
- **Density spot-check:** recompute `texelsPerM` from the baked offsets for the hero surfaces and
  every flagged renderer you kept.

## 3. Post-bake visual check

Nothing here replaces final-reviewer criterion 2; it is the builder's own evidence.
1. **Lightmap-only render of each room:** Scene view *Baked Lightmap* draw mode, or an unlit material
   showing only the lightmap. Texture detail can't hide a torn chart there.
2. **Near-reach shots** at ≤ 0.6 m and eye height, from the side a player sees, of:
   - every soft or organic piece (pillows, cushions, throws, bedding, sculptures, vases, plants,
     fabric furniture);
   - every renderer the audit flagged and kept.
   
   Inspect at full resolution. Look for faceted dark triangles, torn seams, parts of one object in
   different tones, and blotches.
3. **Merged vs unmerged:** where the scene merges after the bake, shoot the unmerged originals from
   the same poses. Identical defects mean the bake or UV2 is at fault; defects only in the merged
   shot mean the merge broke UV2 or scale-offset.
4. **Positive control:** run the same rig and threshold on one known-bad piece. Use an unfixed
   flagged renderer, or a copy at Scale In Lightmap 0.1 in a scratch bake. The rig must see its
   defect. Quote both results.
5. **Before blaming allocation:**
   - Contour bands on a large dark surface are usually 8-bit backbuffer quantization. Compare an 8-bit
     and a float render of the same camera before raising density.
   - A colour shift between bakes can be a repack moving a chart, not a lighting change. Confirm with
     a render.
   - A prop that reads cold may simply be unbaked (index −1).

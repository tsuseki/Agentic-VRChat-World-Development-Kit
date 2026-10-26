# Sources: lightmap-allocation

Bibliography and attribution for `.omp/skills/lightmap-allocation/SKILL.md`. Not needed to use the skill; open it only to check
where a claim came from. Sections are grouped by the file that cites them.

## `SKILL.md`

- **In-house incidents, 2026-10.** Measured in a large multi-floor VRChat interior baked with Bakery and VRC
  Light Volumes, and in a large outdoor driving world. They cover:
  - glass atlas demand;
  - fragmented organic UV2 (about 800 of 2,379 small renderers; a merged-vs-unmerged A/B);
  - per-material bark starvation;
  - the 68 % atlas hog;
  - the importer Calculate margin;
  - the user's Light Volume scope rule ("only small props can go with lightvolumes", narrowed to about ≤ 0.4 m
    plus soft decor) and the no-probes-on-statics rule.
- Kit knowledge notes, read in full: every note in `.omp/knowledge/notes/` matching lightmap, UV2,
  texel, scaleInLightmap, chart, atlas, receiveGI, gutter, margin, LightProbes or Light Volume. The
  ones folded in are listed in `references/lessons-lightmap-allocation.md` by rule.

## `references/reception-and-density.md`

- **Official Bakery manual** — <https://geom.io/bakery/wiki/index.php?title=Manual>
  (texels-per-unit starting values, Scale In Lightmap 0 as occluder, texel padding, LOD lightmap
  sharing, Asset UV Processing)
- **GLIM** — z3y, <https://github.com/z3y/glim> (groups, Scale In Lightmap differences, LOD0-only on
  hand-authored LODs)
- **VRC Light Volumes** — REDSIM, <https://github.com/REDSIM/VRCLightVolumes> (only LV-aware shaders read
  volumes)
- Mirror making Progressive loop forever — VRChat Ask forum, "Help, lightmap bake is not working correctly", 2024,
  <https://ask.vrchat.com/t/help-lightmap-bake-is-not-working-correctly/27527>
- BC6H memory per texel (8 bits per pixel) — Microsoft, "BC6H format",
  <https://learn.microsoft.com/en-us/windows/win32/direct3d11/bc6h-format>

## `references/uv2-quality.md`

- **Unity Manual 2022.3, "Generating lightmap UVs"** —
  <https://docs.unity3d.com/2022.3/Documentation/Manual/LightingGiUvs-GeneratingLightmappingUVs.html>
  (Manual vs Calculate margin, Pack Margin in pixels for a mesh filling a 1024 map, Hard Angle 180
  for organic models, Area Error, two-texel chart spacing)
- **Unity Scripting API, `ModelImporter.secondaryUVPackMargin`** —
  <https://docs.unity3d.com/2022.3/Documentation/ScriptReference/ModelImporter-secondaryUVPackMargin.html>
- Official Bakery manual (Adjust UV padding, UV processing modes) — as above

## `references/audit.md`

- In-house audit thresholds (30 % of triangles under 0.01 texel², 50 % of charts under 4 texels, a
  submesh with ≥ 10 % of the area and < 5 % of the UV2), set by the final-reviewer's UV2 audit after the
  fragmented-UV2 incident, 2026-10-26.

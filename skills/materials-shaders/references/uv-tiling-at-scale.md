# UV tiling for large worlds

How to texture km-scale architecture with a small set of reused tileable textures, using
**UVs only**: Standard (or the project's default) shader, no triplanar, stochastic or hex-tiling
shader, no detail blending. Memory depends on how many textures there are, never on how much
surface they cover, so a big world stays cheap if every surface reuses a few sets. The work is in
making that reuse invisible.

## 1. Fix three numbers per material before any UV work

| Number | Rule |
|---|---|
| **Texel density** | One world value for surfaces players walk past: **~5 px/cm** (2048 px over ~4 m). At 1.5–2 m viewing distance in a PC headset, 1 cm covers about 4–7 screen pixels, so more density is invisible in VR and only shortens the period. Use 10 px/cm only for trim strips seen at arm's length (rails, beams on walkways); 2–3 px/cm for surfaces seen only from ≥ 30 m (cliffs, far facades) |
| **Period** (metres per repeat) | `texture px ÷ density`. Snap it to the material's real module **in scene metres** (worlds built at ×k scale: real module × k): whole board-form panels, slab grids, block courses. A period that lands on joints lets geometry cuts and UV seams fall on joints |
| **Mode** | One of the four mapping modes in §2 |

## 2. Four mapping modes (pick one per surface family)

| Mode | Use for | UV0 rule |
|---|---|---|
| **A · Continuous tileable** | floors, ground, grating, water-worn stone, plaster, rock | box projection in world metres per face: `uv = world / period` on the dominant-normal plane, material tiling (1,1). Per surface: random offset; **isotropic** textures (rock, ground, moss, rough concrete) also get a random 0/90/180/270° rotation per face or per facet. Seams hide on facet edges, where the normal already breaks |
| **B · Panelised variant atlas** | big walls and facades of a modular material (board-form concrete, panels, block) | cut the geometry at the material's own joints, one period per panel. Pack 2–4 variants of the same material in one atlas (e.g. 4096×2048 = 2 variants at 2048). Each panel's island goes into a random variant cell, with a random 180° rotation and/or mirror where the pattern allows. Inset islands 8 texels so mips 0–3 don't bleed (deeper mips mixing variants of the same material is harmless). The repeat becomes a random arrangement of N panels: no wallpaper even at 1 km |
| **C · Trim sheet** | edges, beams, rails, frames, slab edges, cornices, hazard bands, mullions | the sheet is horizontal bands that tile in u. Unwrap each part as straight strips: `u = length / period_u`, v = the band's rows. One sheet (+ its material) covers every linear part in the world. Bevel geometry to the band's profile; the normal map supplies the rest |
| **D · Unique 0..1** | emblems, banners, signs, screens, hero pieces | ordinary 0..1 unwrap; budget them separately |

Mode A and mode B surfaces in one mesh are separate submeshes, which means separate materials.

## 3. Rules that make reuse invisible

- **Seams on joints.** UV seams, period boundaries and geometry cuts go where the real material
  has a joint (formwork panel, pour lift, slab edge, course). The repeat then reads as construction.
- **Align the period origin to the structure.** Set the v offset per storey or slab so a joint
  sits on each slab top (`offset_v = −(elevation mod period) / period`). Storey heights rarely
  divide by the period.
- **Tint reuse, not texture copies.** Two materials that differ only in value (a light keep and a
  darker wing in one concrete) share the textures and differ in `_Color`. `_Color` can darken but
  can't desaturate (SKILL.md §2 D), so hue changes need a new albedo.
- **Clones get offsets.** Repeated modules (pillars, piers, ribs) get a random per-renderer
  `_MainTex_ST` offset through a MaterialPropertyBlock (SKILL.md §2 C). Mode B panels already vary
  through their UVs.
- **Rotation only where the pattern allows it.** Board marks, planks, courses and drips are
  directional: use 180° or mirror only. Rock, moss, gravel and rough concrete take any rotation.
- **Avoid single features in a tile.** One tie hole, crack or stain in a tile marks the period from
  across the valley. Choose sources that are even at the period scale, or put features in the
  mode B variants, where they land randomly.
- **Tangents after every UV write.** Rotated or mirrored islands need `RecalculateTangents()` on
  generated meshes, or the normal map lights from the wrong side.
- **UV2 is separate.** Lightmap UVs never tile and come from their own unwrap
  (`.omp/skills/lightmap-allocation/SKILL.md`). Writing UV0 must copy UV2 through untouched.

## 4. Budget

Per tileable set (albedo + smoothness in alpha, normal; full mips), PC:

| Size | Albedo BC7 | Normal BC5 | Set |
|---|---|---|---|
| 1024² | 1.33 MiB | 1.33 MiB | 2.7 MiB |
| 2048² | 5.33 MiB | 5.33 MiB | 10.7 MiB |
| 4096×2048 (mode B, 2 variants) | 10.7 MiB | 10.7 MiB | 21.3 MiB |

A separate metallic/AO mask adds one albedo-sized BC7 map. Plan the set list before C.1 so its
total, the lightmaps and the skybox fit the texture VRAM budget (`perf-optimizer` "Default
budgets"). Ten to fifteen sets usually cover a whole world.

## 5. Verify

- Repeats per metre per axis = mesh UV per metre × material tiling (measure with world/UV triangle
  areas, SKILL.md §2 C). It must equal 1/period on every surface of the family.
- Same-camera captures at three distances (2 m, 30 m, 300 m+) and at a grazing angle. Repetition
  shows at the far one first. Compare against the same surface with plain continuous tiling as the
  positive control.
- Seam check: zoom a capture on a panel joint and a facet edge; no half-board offsets or flipped
  normals.

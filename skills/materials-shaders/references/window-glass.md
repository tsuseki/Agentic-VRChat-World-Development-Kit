# Window and panel glass: see-through with a soft reflection

The tested setup for clear window, facade, railing and shower glass in a Built-in RP world. Seen
from outside, the pane shows a blurred sheen of what's in front of it, still see-through head-on and
never milky. From inside, it shows a faint soft reflection of the room. Rebuild all four parts; the
look comes from them together.

## 1. Shader: `AWDK/WindowGlass`

Copy [`WindowGlass.shader`](WindowGlass.shader) into the project (`Assets/<World>/Shaders/`). It uses
Standard's own glass maths, with the reflection strength exposed as two numbers:

- `refl = lerp(_ReflectHeadOn, _ReflectGrazing, (1 - N·V)^4)`. This is Standard's Fresnel (Pow4) curve.
- Colour: `_Color.rgb × ShadeSH9 × _Color.a + probe × refl`, blended premultiplied (`Blend One OneMinusSrcAlpha`).
- Alpha: `1 − (1 − _ReflectHeadOn)(1 − _Color.a)`, as Standard computes it. A see-through pane keeps a low
  alpha at every angle, so the reflection adds light and never turns the pane opaque.
- The probe is sampled at the mip for `perceptualRoughness = 1 − _Glossiness`, with box projection and
  two-probe blending as in Standard.
- No depth write, no shadow caster, no meta pass: glass casts no baked shadow and doesn't block the bake.

## 2. Material values (every glass material shares them)

| Property | Value | Why |
|---|---|---|
| `_ReflectHeadOn` (F0, linear) | **0.04** | What real glass reflects head-on (n = 1.5). Standard Specular's usual `_SpecColor` 0.09 sRGB is only 0.0083 linear: you can see that much on a sharp reflection, but once the reflection is blurred it fades into nothing, so the glass seems to reflect only at an angle |
| `_ReflectGrazing` | **0.71** | Standard's edge-on cap (smoothness + F0). Matches real glass within a few points out to ~80° (table below) |
| `_Glossiness` | **0.70** | Samples a GGX-convolved mip, so the reflection reads as a smooth blur. At 0.90 or higher it samples mip 0, and a 256 px cubemap shows up magnified into blocks |
| `_Color` | dark neutral, alpha 0.10–0.14 | Tint and coverage. Shower panels about 0.12; steamed or frosted glass up to ~0.38 |

Reflection by viewing angle (the angle is from the glass normal):

| Angle | Real glass | Shader |
|---|---|---|
| 0° | 4% | 4% |
| 45° | 5% | 5% |
| 60° | 9% | 8% |
| 70° | 18% | 17% |
| 80° | 39% | 35% |
| 89° | ~92% | ~69% |

A real double-glazed pane reflects about 8% head-on, so 0.04 is on the gentle side. If the glass looks
too strong or too weak overall, change the probe intensity (section 3), never the curve.

## 3. Probes: what the glass reflects

A renderer picks its reflection probe per renderer, not per pixel. A long pane seen from both sides
therefore needs its faces split up, or garden viewers get a smeared, box-projected room cubemap.

- **Exterior probes, one per facade** (`GLASS_REFLECTIONS/RPX_*`):
  - Captured just outside the facade at standing eye height (or over the drop where nobody stands),
    from the clearest spot within 2.5 m (not inside a tree or a parasol).
  - `Baked`, HDR, **no box projection** (infinite), `blendDistance 0`, **intensity 3.0**, resolution 256,
    clear flags Skybox, far clip large enough to see the backdrop.
  - Move each probe's influence volume (`center`/`size`, 80 m cube) far above the world, one per
    probe, 150 m apart, so that nothing picks the probe up except glass anchored there. Put a child
    `Anchor` at the volume centre.
- **Facade panes** (one side outdoors): one face mesh holding both sides' triangles.
  - Outward triangles go first.
  - `probeAnchor` = the `Anchor` of the exterior probe in front of the face, nearest to a point 4 m out.
  - `reflectionProbeUsage = Simple`, `lightProbeUsage = Off`. Light probes at the far-away anchor would
    be extrapolated garbage, so ambient comes from `ShadeSH9`.
- **Interior partitions** (both sides indoors): cut each side's face at the room boundaries.
  - Each piece gets a `ProbeAnchor` 0.4–1.0 m into its room, clamped inside that room's box-projected
    probe (shrunk by 0.6 m). Otherwise Unity picks another probe.
  - `reflectionProbeUsage = Simple`, `lightProbeUsage = BlendProbes`.
- **Room probe capture origins:** put them at the clearest spot of the room at floor + 1.2–1.5 m, near
  the middle. A box-projected probe spreads whatever sits near its origin (sofa, candle-lit table)
  across the whole box, and the glass then shows it as huge blobs.
- Glass seen from inside mostly reflects through the facade face, so it shows the exterior probe.
  That makes the inside reflection fainter than the outside one; this is expected.

## 4. Flags on every glass renderer

- Clear `ContributeGI`, `OccluderStatic` and `ReflectionProbeStatic`: no GI, no occlusion, and probes
  never bake glass into glass.
- `receiveGI = LightProbes`: never lightmapped.
- `shadowCastingMode = Off`, `receiveShadows = false`.
- Mesh merges (perf) must copy `probeAnchor` and the usage settings from their sources.

Script the whole rig as one idempotent editor builder that re-runs after every shell rebuild. Have it
set the probe intensity itself: a value set by hand and left out of the builder gets reset the next
time the builder runs.

## 5. Tuning and proof

- **Measure:** render the same camera with the glass renderers on and off. Over the pixels where the
  difference is above 2, report the mean and p95 of the positive luma difference and the share of
  pixels. Test four poses: outside head-on, oblique along the facade, near-grazing, and inside looking out.
- **Compare against a reference:** when you change the blur, match against the captures of the
  look the user approved. Rendering the old setup again from the current scene is not a reference.
- **Reload the scene after changing reflection-probe settings from a script.** Changing
  `ReflectionProbe.intensity` and back again left the glass about 2.5× fainter (terrace mean 10.7 →
  4.7) until the scene was saved and reopened. Toggling the probes or a repaint did not fix it.
  Before trusting a drop in numbers after probe edits, reload the scene and render again.
- Rebake reflection probes after every lightmap bake. Judge glass again after the bake and after the
  probe rebake.

## Pitfalls

- Blur and strength are two separate knobs. Blurring spreads the same energy over more of the pane, so
  each pixel gets fainter: raise F0 to real glass when you add blur, and don't push the probe intensity.
- A custom curve such as `pow5` capped at 0.45 under-reflects at oblique angles compared with Standard.
  Keep Standard's Pow4 and its 0.71 cap.
- Push F0 too far (0.45, or probes ×5.5) and the glass turns milky and opaque from outside.
- Mochie Glass behaves differently: any `_Roughness` > 0 turns on a blurred grab pass, which blurs the
  world seen through the glass (SKILL.md F).

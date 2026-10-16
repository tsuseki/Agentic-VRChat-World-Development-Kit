---
name: clip-planes
description: Camera clip planes, depth and float precision, and world extent for VRChat PC worlds — Reference Camera and runtime VRCCameraSettings near/far, the far-clip procedure and skybox overpaint, fog that hides the far cut, the 256/512 m radii from the origin, teleport-island placement, distant scenery (geometry, backdrop cards, skybox bakes) and the z-fighting separation rule. Load when setting near/far clip or fog, placing teleport islands or far scenery, sizing a world's extent, or judging z-fight separation.
---

# Clip planes, precision and world extent

Scope: VRChat PC, Unity 2022.3, Built-in RP, D3D11. Archetypes A1–A5 are defined in `.omp/skills/spatial-design/SKILL.md` §1.
Tags (`[in-house, measured]`, `[INFERENCE]`, `[WORKSPACE RULE]`, named sources) follow the spatial-design
conventions; named sources resolve in [SOURCES.md](SOURCES.md). Derivations, measurements and the
reach-box snippet: [references/clip-planes-and-precision.md](references/clip-planes-and-precision.md)
(cited below as "the research §N").

Stages (`.omp/skills/world-pipeline/SKILL.md`): A.3 shell layouts, B.1 floor plan and B.2 greybox plan the extent, islands, near/far, fog and backdrops (§2–§5);
C.2 sets them up (§7 items 1–7); D.1 checks sky matching and backdrops (§5, §7 items 9–11);
every builder and reviewer applies §6 to z-fighting.

## 1. Facts that drive the numbers
| Fact | Value | Tag |
|---|---|---|
| Where clip planes are set | Scene Descriptor's **Reference Camera** (Inspector minimum near 0.01) | [VRChat Scene Descriptor] [in-house] |
| Runtime override | `VRCCameraSettings.ScreenCamera.NearClipPlane` / `FarClipPlane`; set far first, then near | [VRChat Camera Settings] |
| Near clamp | **0.001–0.05 m**; far ≥ near + 0.1 | [VRChat Camera Settings] |
| Default far / near | 1000 m / ~5 cm | [VRChat Dev Update 2022-08-03] [WildCat Canny 2025] |
| User override | "Forced Camera Near Distance" Off / Dynamic / Forced; Forced = 0.001 always; worlds can detect, not override | [VRChat Dev Update 2022-08-03] [hdorriker Canny 2025] |
| PC depth buffer | **32-bit float, reversed Z** (`D32_SFloat_S8_UInt`, `usesReversedZBuffer = True`) | [in-house, measured] [Unity Platform Differences] |
| Depth precision vs near | Measured separations identical for n = 0.001–0.1: a small near costs no z-fighting on PC | [in-house, measured] [Reed 2015] |
| Real far limit | The skybox paints over geometry whose reversed depth < ε ≈ 5.3×10⁻⁷: **f_eff ≈ n·f / (n + ε·(f−n))**, saturating at n/ε (1.9 km at n = 0.001) | [in-house, measured] |
| Overpaint examples | f = 1000: visible to 684 m at n = 0.001, 950 m at 0.01, 989 m at 0.05. f = 700, n = 0.001: 532 m (users measured 531 m) | [in-house, measured] [WildCat Canny 2025] |

**Near-clip rule:** n ≤ (closest surface that must stay intact) / 2, because the flat near plane clips
off-axis points at up to 1.56 n in a wide VR view. 1 cm is "close enough for head pats and cuddles"; 5 cm
"is too relaxed". [INFERENCE] [WildCat Canny 2025]

## 2. Near, far and fog per archetype
| World | Reference Camera near | Runtime near (Udon) | Far clip | Fog | Max \|coordinate\| reachable | Tag |
|---|---|---|---|---|---|---|
| **A1 intimate interior** (views out through windows) | 0.01 | **0.001–0.003** | smallest covering the longest sightline, typically 300–1000 | optional; sky horizon band = fog colour | **< 256 m** | [INFERENCE] on [in-house, measured] |
| A2 home with garden, terrace or rooftop; A1 + A5 mixes | 0.01 | 0.003–0.005 | 500–1000 | ExpSq, opaque before f_eff | cuddle rooms < 256 m; rest < 512 m | [INFERENCE] |
| A3 venue / A4 cinema indoors | 0.01 | 0.003–0.01 (0.001 if it has cuddle booths) | per sightline | optional | < 512 m (cuddle booths < 256 m) | [INFERENCE] |
| A5 large outdoor or flying | 0.01 | none, or 0.01 | 1000 (a shipped flying world); up to ~2000 | ExpSq, T(far) ≪ 1/255 | < 512 m round the social core | [in-house] [INFERENCE] |

**Far-clip procedure** [INFERENCE] on [in-house, measured]:
1. **Reach box R:** bounds of all enabled non-trigger colliders + 2.5 m headroom (snippet in the research §4).
2. **Content box C:** bounds of every renderer meant to be seen, backdrop cards included, skybox excluded.
3. **Sightline D:** per-axis max(C.max − R.min, R.max − C.min); shorten with a raycast sweep if walls block corners.
4. **Near:** smallest n for which f_req(n, D) = n·D / (n − ε·D) exists (ε = 6×10⁻⁷ for margin). Interiors with
   D ≤ 300 m can use n = 0.001 with f ≈ 370; content out to 1 km needs n ≥ 0.003.

| n \ D | 100 | 300 | 500 | 1000 | 2000 | max D |
|---|---|---|---|---|---|---|
| 0.001 | 106 | 366 | 714 | 2500 | — | 1.67 km |
| 0.003 | 102 | 319 | 556 | 1250 | 3333 | 5 km |
| 0.01 | 101 | 305 | 515 | 1064 | 2273 | 16.7 km |

5. **Far:** f = max(f_req(n, D), 1.05·D).
6. **Fog:** reach T ≤ 1/1020 by the effective far computed for n = 0.001 (Forced users see only ~0.65 f):
   ExpSq ρ ≥ 2.63/f_eff, Exp ρ ≥ 6.93/f_eff, Linear end ≤ f_eff. For f_eff 950 m use ρ ≥ 0.0028. [in-house]
7. Make the sky's **horizon and below-horizon colour equal the fog colour**; overpaint, the far-plane cut and
   ground-edge gaps all vanish. Fog radially in your own shaders so mirrors fog too. [in-house]
8. Sky domes and occluders stay smaller than far, or they are culled silently. [in-house]

## 3. Float precision and world extent
- Float32 spacing grows with distance from the **world origin** (not spawn): 7.6 µm at 100 m, 30.5 µm at
  256–512 m, 61 µm at 512–1024 m, 0.49 mm at 5 km. [Dawson 2012]
- Close-up jitter is what breaks cuddle worlds: a face 2 cm away shimmers 1 px at 250 m, 2 px at 500 m,
  26 px at 5 km. A smaller near clip lets people get closer, so it magnifies this. [in-house, measured]
- PhysBones and UI jitter far from the origin are confirmed float effects. Floating-origin tricks break
  static batching, occlusion culling and object sync: avoid them in social worlds. [Mr. Imagination Canny 2024] [KitKat4191 JetSim FO]
- **Radii (largest per-axis |coordinate| of anything people occupy, eye height included):**
  - **Cuddle zones (any A1 space, cuddle booths, beds) < 256 m.** Below 128 m is better still.
  - **Any occupied space < 512 m.** 512 m is the float exponent boundary where users report problems.
  - Viewed-only scenery may sit anywhere inside the far clip.
  [INFERENCE] on [Dawson 2012] [in-house, measured] [in-house]
- Spawn and the main social area sit at the origin. [in-house]

## 4. Teleport islands inside the limits
- Keep the ≥200 m separation between the main area and each island, and between islands. [WORKSPACE RULE]
- **|island centre| + half-extent < 256 m on every axis for cuddle rooms** (512 m absolute for others).
  Grid that works: centres at (±220, 0, 0), (0, 0, ±220), (±220, 0, ±220) with rooms ≤30 m wide; layers
  at y = ±200 add slots. Every island stays above the Respawn Height. [INFERENCE] [VRChat Scene Descriptor]
- At 200–300 m islands sit inside a 1000 m far clip: seal them (they then occlude with baked occlusion
  culling), put them below the ground plane, or put them on their own layer with `LayerCullDistances` ≈150 m. [VRChat Camera Settings] [INFERENCE]
- Island landings are raycast-checked: floor hit, clear capsule, door ~1.4 m behind the arrival point. [in-house]

## 5. Distant scenery: geometry, backdrops or skybox
| Distance band | Technique | Tag |
|---|---|---|
| Inside reach, to ~3–5× the reach radius | real geometry with LODs | [INFERENCE] |
| Mid band, inside f_eff | backdrop cards or impostors captured from the real assets | [in-house] |
| Beyond the parallax limit | **baked into the skybox** (cubemap or equirect): free, never clipped, fog baked in, correct in mirrors | [INFERENCE] [in-house] |

- **Parallax rule:** a guest moving r metres sees content at distance D shift by r/D; the skybox doesn't
  move. Depicted distance **D_min = r / θ_max**, with θ ≤ 0.25° next to real geometry (a skyline continuing a
  real street) and θ ≤ 1° for isolated silhouettes (mountains, city glow). [INFERENCE]

| Reach radius r | θ 0.25° | θ 1° |
|---|---|---|
| 5 m (room by a window) | 1.1 km | 290 m |
| 20 m (penthouse, terrace) | 4.6 km | 1.1 km |
| 50 m (garden, beach) | 11 km | 2.9 km |

- Stereo disparity drops below one VR pixel beyond ~75 m; past that only motion parallax gives a skybox away. [INFERENCE]
- Put a barrier (water, cliff, fog, glazing) between the reach box and anything baked, so nothing seems
  reachable. [INFERENCE]
- Capture: build far content at true distance, capture from the reach-box centre at eye height with near =
  r + margin and runtime fog on, `RenderToCubemap` to HDR, import at 2048 per face, disable the source,
  point the Bakery sky light at the new cubemap, rebake, then bake reflection probes. [Unity RenderToCubemap] [in-house]
- Match the skybox sun to the baked light in azimuth and elevation; grade geometry, impostors and capture
  together. [in-house]

## 6. Depth separation (z-fighting)
- Never coplanar: joints overlap 1–3 cm, decals stand off ≥1 mm. [in-house]
- PC-only rule: δ ≥ max(1 mm, 2×10⁻⁶·(R + d)), R = largest |coordinate|, d = viewing distance. The kit's
  `ZFightRender` defaults to a float32 reversed-Z depth model matching PC; its 24-bit (D24) model remains
  an option for a conservative cross-platform check. [INFERENCE] [in-house, measured]

## 7. Setup checklist (builder sets, reviewer verifies)
| # | Check | Pass |
|---|---|---|
| 1 | Reference Camera | assigned in the Scene Descriptor, near 0.01 |
| 2 | Runtime near/far | if n < 0.01 is wanted, Udon `Start()` sets far then near via `VRCCameraSettings`; n ≤ closest intact surface / 2; local Camera fallback for editor play mode |
| 3 | Reach extent | max per-axis \|coord\| of the reach box < 256 m (cuddle zones) / < 512 m (any occupied space); spawn and heart near the origin |
| 4 | Teleport islands | each: \|centre\| + half-extent < 256 m (cuddle) per axis; ≥200 m from the main area and each other; above Respawn Height; sealed, underground or layer-culled |
| 5 | Sightline vs far | D measured; far ≥ f_req(n, D) |
| 6 | Fog vs effective far | ExpSq ρ ≥ 2.63/f_eff with f_eff for n = 0.001, **or** sky horizon colour = fog colour |
| 7 | Sky domes and occluders | radius < far |
| 8 | Z-fighting | no coplanar pairs; joints overlap; decals per §6 |
| 9 | Skybox backdrop distance | every baked feature's depicted distance ≥ r/θ; a barrier between reach and backdrop |
| 10 | Backdrop cards and impostors | inside f_eff (n = 0.001) or fogged out before it |
| 11 | Sky matching | sun azimuth and elevation match the bake; Bakery sky light uses the sky cubemap; probes rebaked |
| 12 | Close-up jitter spot test | at the farthest cuddle spot, a camera 2 cm from a surface shows no shimmer while moving |
| 13 | Layer culls | small-prop and island layers culled with `LayerCullDistances` where it helps; reserved layers untouched |

[the research §6]

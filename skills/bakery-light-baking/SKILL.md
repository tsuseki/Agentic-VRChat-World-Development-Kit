---
name: "bakery-light-baking"
description: "Diagnose and fix baked-lighting artifacts (red/green chroma blobs, blue sheen, washed-out bakes) in Unity + Bakery for VRChat worlds; tune emissive fixtures (BakeryLightMesh power, SSS lampshades, lamps that glow but light nothing); includes scripted bake/probe recipes, a two-stage draft/final preset workflow, and the same workflow for Unity's Progressive GPU lightmapper when Bakery isn't installed. Use when: baking lightmaps with Bakery or Progressive, lightmap looks blotchy/noisy/discolored, building or tuning lamps/sconces/emissive props, an emitter's intensity seems to do nothing, iterating on world lighting, setting up fast test bakes, or automating bakes via Unity MCP/editor scripting."
---

# Bakery Light Baking: Artifact Diagnosis & Scripted Bakes

> Turn "why is my lightmap blotchy" from guesswork into a 4-step diagnostic, and drive Bakery bakes/probes reliably from editor scripts.

## Quick Reference

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Soft red/green mottled blobs on dim walls/ceilings | GI Samples too low (e.g. 4; Bakery default 16); denoiser smears chroma noise into blobs | Raise GI Samples to 16, or 32 for clean dim interiors |
| Green/magenta blocky shifts in dark gradients | Encoding/compression artifacts, including platform-specific Android formats | Check actual imported format and High Quality desktop encoding; A/B with an uncompressed importer on the target platform |
| Blobs look huge / low detail | Insufficient effective chart resolution or poor packing | Inspect Checker/Atlas Preview; raise relevant density/group resolution or atlas limit only if actually limiting detail |
| Blue sheen on glossy surfaces after rebake | Reflection probes have NULL bakedTexture → skybox fallback | Re-render reflection probes after EVERY bake |
| Blue tint persists with reflections disabled | Sky-lit hidden exterior faces; UV charts bleed into interior charts | Fix/exclude exterior geometry; re-UV or separate charts |
| Whole bake looks flat and washed out | Shadowless realtime directional light adding over lightmaps | Restrict helper lights via cullingMask to a dedicated layer, or delete before judging |
| Dynamic objects render near-black | Light probe bake silently aborted (geometry changed since full bake) | Bake probes immediately after a full bake; verify with `LightProbes.GetInterpolatedProbe` |
| Contact shading is too weak for the intended style | Missing/weak physical occlusion or desire for extra artistic darkening | Check lighting/geometry first; Bakery AO is optional nonphysical darkening, disabled at intensity 0 |
| A wall bakes solid black with nothing visibly in front of it | Bakery treats **all back-faces as opaque** — an inverted or single-sided face nearby blocks light invisibly | Check normals/winding of neighbouring geometry, not the light |
| Bright fringe / fireflies along shadow edges | Denoiser edge case, not a sample-count problem | Denoise → enable **Fix Bright Edges** |
| Light leaks through a thin wall | Samples landing on the wrong side of the surface | Enable **Adjust Sample Positions** before moving geometry |
| Emitter's `intensity` is a "dead knob" — 3× changes nothing | Almost always **underpowered**, not broken. Intensity is per-AREA, so a number copied from a bigger emitter can be 10–100× under | Compute `worldArea × intensity` and compare to a working emitter |
| Emissive material glows but contributes zero GI | Material export/Meta Pass, `BakedEmissive` flags, UVs, occlusion, samples or stale export | Inspect the material-emission path; use a `BakeryLightMesh` for explicit small/bright emitters, not because material emission is unsupported |
| Emitter object bakes with `lightmapIndex = -1` | **Correct, not a bug** — Bakery hard-skips lightmapping anything carrying a `BakeryLightMesh` | Split emitter and visible body if the body must be lightmapped |
| A glowing lampshade lights nothing | Sealed shell traps the bulb, **or** the glow is the SSS pass — which does not re-radiate | Count boundary edges; add an invisible emitter or open the shade |
| SSS does nothing on a translucent mesh | It's a **per-group** checkbox and needs a closed volume | Give the mesh its own group asset + selector; model real thickness; `shadowCastingMode = On` |
| Glossy surfaces glow/reflect sky inside dark baked corners ("Unity shine") even with correct probes | Standard has no lightmap-driven specular occlusion | Default: lower smoothness / probe intensity on the affected materials. Only if the user approves a shader change: Filamented (Exposure Occlusion), ORL Standard (Reflection Probe Occlusion) or Graphlit Lit; these also support Bakery MonoSH and bicubic lightmaps. Offer, never swap unasked |

## Workspace lighting standard (user rules)

Defaults for every world, Bakery or Progressive. The user may change them for a specific world; the
change and the user's words go in that world's `WORLD.md` Decisions log, and then `WORLD.md` wins.

- **No realtime or Mixed directional light**, even outdoors; lighting is fully baked (no realtime or
  Mixed lights at all). The sun stays in the scene as **Baked** so Bakery can cast from it; aim for
  large-scale shadows only. Bakery if licensed, else Unity Progressive GPU. Anything that moves needs
  `LightProbeGroup` coverage.
- **Cozy/night interiors go darker than instinct.** Deep shadow with small warm pools; when it seems
  done, cut another ~15% before asking, and never raise a level the user approved. "Lamp too bright"
  usually means the spill (emitter intensity), not the shade's own emission; they are separate knobs.
- **Reflection probes immediately after every bake** (hard rule 6; procedure under "Probes after
  every bake" below).

## The Problem

Bakery bakes in dim interiors often come out with soft red/green mottled blotches ("chroma blobs") on flat walls and ceilings. Bounced light carries surface albedo color; at low GI sample counts each texel's color channels converge differently, producing chroma noise. The denoiser (Denoise = on) then smears that grain into large soft colored blobs — it cannot recover detail that was never sampled. Dark scenes are worst: HDR encoding spends little precision there, and human vision is highly sensitive to hue shifts on flat dim surfaces.

The trap is diagnosing from memory or the Bakery UI. The settings that actually produced a bake live in serialized scene data — read those first.

## Solutions

### Diagnostic order (always in this sequence)

1. **Read actual settings from `ftLightmapsStorage`** — the component on the `!ftraceLightmaps` GameObject holds the per-scene render settings that were really used (fields prefixed `renderSettings*`). Do not trust the UI or memory. Script: see `reference/examples.md` (Snippet 1).
2. **Check GI Samples first.** Found at 4 in the diagnosed case; default is 16. Set 16 (good) or 32 (clean dim interiors). The sample number is **the square root of the ray count** — 32 samples = 1024 rays, 64 = 4096 — so cost is **quadratic**, not linear: 16 → 32 is ~4× the GI time, and 16 → 96 is ~36×. If only some areas stay blotchy, raise per-object sample multipliers instead of the global value. Bakery warns above 64 GI samples (`ValidateSamples`) — that is a "you probably don't need this" nudge, not an error.
3. **Check encoding/compression.** For desktop, check High Quality lightmap encoding and the actual imported format (commonly BC6H); Android compression needs its own A/B. Temporarily compare an uncompressed importer. (In the diagnosed case encoding was already fine — check, don't assume.)
4. **Check texel density.** Inspect Checker/Atlas Preview and the receiving renderer's effective chart resolution. `MaxAutoResolution` limits each atlas, but more atlases can be allocated; raising 1024 to 2048 helps only when that limit actually constrains the needed layout/detail. Neither a 1024 atlas nor 20 texels/unit alone diagnoses starvation.

### Scripted bakes (verified recipe)

Static `ftRenderLightmap.RenderLightmap()` **silently does nothing**. The working recipe:

1. `EditorWindow.GetWindow(ftRenderLightmap type)`
2. Invoke `LoadRenderSettings()`
3. Invoke `RenderButton(false)`
4. Poll static field `ftRenderLightmap.bakeInProgress`; completion also rewrites the configured output's lightmaps (`Assets/BakeryLightmaps/*_final.hdr` in the verified project; inspect Output path and format before watching files).

Selective bake: use the installed version's **Render Selected Groups** path with `Selection.objects` set to the area's renderers/roots. **Bakery 1.96 `RenderButton(false)` resets `selectedOnly=false`; setting the flag beforehand silently requests a full bake.** Inspect the native button implementation and verify unrelated atlas hashes/timestamps remain unchanged. Per-area `BakeryLightmapGroup` assets make subset rebakes cheap. Selector fields: `active`, `lmgroupAsset` (NOT `lmgroup`), `instanceResolutionOverride`, `instanceResolution`.

Full code: `reference/examples.md` (Snippets 2–3).

### Two-stage workflow: draft preset → final preset

Iterating lighting at final quality is the single biggest time sink in a world project. Keep **two named settings presets** and switch between them instead of hand-editing the Bakery window each time.

Bakery already has the mechanism: `ftSettingsAsset` ScriptableObjects, exposed in the Bakery window under **Presets** (only visible when Settings Mode = Experimental). Assigning one copies its values into the scene's `ftLightmapsStorage`. Both classes use identical `renderSettings*` field names, so presets can be created and applied by copying fields by name — see `reference/examples.md` (Snippet 6).

Bake cost scales roughly as **(texel count) × (ray count)**, texel count scales with `texelsPerUnit²`, and ray count scales with `giSamples²`. A measured pair from a 6-group VRChat world:

| Setting | FINAL | DRAFT | Why |
|---|---|---|---|
| `renderSettingsGISamples` | 96 | 16 | ~36× fewer rays per texel (samples are √rays) |
| `renderSettingsTexelsPerUnit` | 20 | 5 | ~16× fewer texels |
| `renderSettingsMaxAutoResolution` | 4096 | 1024 | atlases land 1024/512 instead of 4096/2048 |
| `renderSettingsHackAOSamples` | 32 | 8 | AO is a separate pass with its own samples |
| `renderSettingsFixSeams` | true | false | polish, irrelevant to a test bake |
| `renderSettingsBounces` | 4 | **4** | keep identical — see below |

Full render: **22 min → 95 s**.

**Keep `bounces` the same in both presets.** Bounce count changes how bright a sealed room bakes (multi-bounce gain is `1/(1-albedo)`), and judging brightness is the entire point of a test bake. Lowering it makes the draft lie in exactly the dimension you are testing.

**Bakery has a lighter-weight draft knob of its own: "Samples Multiplier".** It is a single slider (displayed inverted, as `1/N`), stored as `renderSettingsSampleDiv` / static `ftRenderLightmap.sampleDivisor`, and applied as `SampleCount(s) = max(s / sampleDivisor, 1)` to **GI samples and every light's sample count** — the manual's own advice is "use this to quickly change between draft and final quality". The crucial difference from a texel-based draft preset:

> `sampleDivisor` does **not** touch texel density or atlas layout, so it never sets `sceneNeedsToBeRebuilt` — *Render selected groups* keeps working across a switch.

So the two knobs serve different loops. Use `sampleDivisor` for the tight inner loop (tweak a light → rebake one area at 1/8 samples, seconds); use the full draft preset when you want the whole world cheap and are willing to pay one full Render. If you only ever rebake single areas, the multiplier alone may be all you need.

Rules that make the two-stage loop actually work:

- **After switching presets the next bake must be a full Render.** Changing texel density or atlas size sets `ftBuildGraphics.sceneNeedsToBeRebuilt`, and *Render selected groups* aborts ~40 s in with `Scene geometry/layout changed since last full bake. Use Render button instead.` Per-area selected bakes work fine **within** one preset — that is the fast inner loop: switch to draft once, then rebake single areas as you move lights.
- **A draft bake overwrites the final atlases.** Both presets write to the same `renderSettingsOutPath`, so the shipped bake is gone until re-baked at final. Giving draft its own output folder is worse than it sounds: the scene rebinds renderers to whatever was baked last, so you end up with half-draft/half-final bindings and no way to restore without baking anyway.
- **Capture FINAL from the live storage, never hardcode it.** Settings get tuned constantly; a hardcoded "final" silently reverts that tuning the first time someone applies it.
- **Applying a preset in play mode is a silent no-op** — the storage is a scene component, so the change is discarded on play-mode exit. Guard on `EditorApplication.isPlaying`.
- **Leave `storage.renderSettingsAsset` null after applying.** If a preset stays assigned, `AreSettingsEnabled()` returns `modifySettingsAsset` and the whole settings UI greys out — it reads like a broken window.

What a draft bake can and cannot tell you:

- **Can**: light placement and reach, leaks, surfaces baking black, occluder mistakes, overall brightness balance, albedo blowouts.
- **Cannot**: shadow crispness, seams, denoiser artifacts, texel-starvation blotches — all of those are resolution-dependent. **Re-render reflection probes immediately after every draft bake too**; otherwise mirrors/glossy surfaces cannot be judged. This workspace requirement has no draft exception.

### Probes after every bake (non-optional)

- **Reflection probes** must be re-rendered immediately after every bake, including drafts and selective bakes (workspace policy). Stale or cleared texture references can produce skybox fallback/blue sheen. Prefer Bakery's own: invoke instance method `RenderReflectionProbesButton(bool showMsgWindows)` on the window. Alternative: `UnityEditor.Lightmapping.BakeReflectionProbe(probe, path)`. The manual's **Always render reflection probes** project setting can automate supported render paths; verify actual completion and custom bindings. Capture geometry needs `ReflectionProbeStatic`, not just `ContributeGI`; exclude glass and video screens from capture. Missing flags produce identical skybox-only cubemaps **without any error**: compare the probe `.exr` checksums (`md5sum`), not just luminance.
- **Light probes can fail SILENTLY.** In the verified workflow `RenderLightProbesButton` aborts if geometry changed since the last full bake (console: "Scene geometry/layout changed since last full bake. Use Render button instead"), leaving `bakeInProgress = false` — indistinguishable from success. L1/L2 normally bake with full lightmaps; Legacy is separate. Verify probe data at deliberately differently lit positions and on a dynamic receiver; identical coefficients alone are not proof of failure in a uniformly lit space. Run any required separate pass immediately after a full bake, never standalone after geometry edits.

Code: `reference/examples.md` (Snippets 4–5).

### Emissive fixtures and SSS

**Intensity is radiance PER UNIT AREA — power is `worldArea × intensity`.** `worldArea` scales with `lossyScale` *squared*, so copying an intensity between emitters of different size silently rescales the light by the area ratio. Solve for it: `newIntensity = refArea × refIntensity × k / newArea`. Independently-tuned emitters in a scene cluster in a narrow power band (one cabin: bulbs 0.19, shade shell 0.29, console glow 0.15, ceiling strips ~0.6) — anything orders of magnitude outside it is the bug. Corollary: **"intensity is a dead knob" means underpowered far more often than broken** (3× of ~nothing is ~nothing). Check the power ratio before hunting mesh/UV/group failures.

**Bakery NEVER lightmaps an object carrying a `BakeryLightMesh`** — `ftBuildGraphics.cs` ~8570 is a hard `continue` in the UV G-buffer pass. Those objects are permanently probe-lit whatever their static flags say, and `lightmapIndex == -1` on them is correct. So anything that must both emit *and* be properly lit has to be split: emitter child carries the light mesh, visible body stays lightmappable.

That split is a knob-layout choice. Light mesh **on the visible surface** → its material emission is a free no-rebake appearance knob, but the face looks flat. Light mesh on a **hidden child** + SSS body → soft gradient, but every appearance tweak costs a bake. If a human is going to say "a bit brighter" three times, pick the first.

**Emitter faces need a gradient, not a flat colour.** Without bloom a flat-emission lamp face reads as a uniform sticker. Give visible emitter faces an emission texture (centre-hot falloff, filament or diffuser pattern) and judge them with post-processing off. For ambient fill prefer concealed cove (lights the ceiling) / cornice (lights the wall) strips whose emitters can't be seen from eye height: they read correctly with or without bloom. [Lura CGWORLD 2024]

**SSS (translucent meshes) — the two requirements that aren't obvious:**

1. **It is a per-lightmap-group checkbox**, so a translucent mesh needs its **own group asset** with `computeSSS` on, assigned via a `BakeryLightmapGroupSelector` on that object. It cannot share a group with the opaque geometry around it — and conversely, turning SSS on for convenience applies the trace to everything else in that group.
2. **The mesh must be a closed volume with real thickness.** Bakery traces light from one side of the volume to the other; a flat polygon does nothing, and even a curtain needs modelled thickness. `shadowCastingMode = On` is likewise a precondition, not a preference — SSS transmits light *through* an occluder, so a non-casting shade lets light pass unimpeded and the pass has nothing to do.

Also: the SSS surface's own material emission must be **~0** or the flat add compresses the gradient into pale cardboard. And SSS **does not re-radiate** — it lights only its own lightmap, so no `sssColor`/`sssScale`/`sssDensity` will make a sealed shade illuminate a room (one group at `sssScale 10` measured *dimmer* than another at `sssScale 1`; the value isn't even a brightness ordering). A sealed shell traps 100% of an interior bulb — count boundary edges (0 = closed) before blaming intensity.

**An SSS shade cannot witness its own bulb** — it's dominated by the SSS pass and nearly deaf to the emitter, so it reads healthy while the room gets nothing. Use a direct-lit witness, and check the witness is actually *reached*: one back-plate read a constant 0.1554 across a 63× intensity sweep and looked like a dead emitter, but was occluded by the shade's own wall and lit purely by bounce. A witness that never moves is either a dead emitter or a bad witness, and those are indistinguishable until you check the geometry.

**Invisible-emitter escape hatch.** To light the room from a surface that must not render (or must stay lightmapped), give a *copy* of it a `BakeryLightMesh` and set `MeshRenderer.enabled = false`. Bakery needs only a MeshFilter — the collector checks `obj.enabled` on the **component**, and a disabled renderer is skipped when gathering traced geometry, so it emits, renders nothing, occludes nothing, and is never lightmapped. Push it a few cm out along its normals and delete faces pointing at anything close.

**Equal power ≠ equal room brightness** across differently-shaped fixtures. A bulb in a vented shade vs a flat slab against a wall measured ~70% delivery at identical power — the fixture read switched-off while its own face was within 2% of the reference lamp. Calibrate on the *rendered* result: 2–3 `(power, frame-mean)` points, fit `frame ≈ base + slope × power`, solve. Related: grade a lamp by **shade-vs-surround ratio**, not absolute luminance (below ~1.2 it reads unlit whatever the number), and to tone down a probe-lit shade turn down **albedo**, not emission — killing emission outright moved one shade 0.699 → 0.671.

### Non-obvious behaviour (from the official manual)

Things that are easy to get wrong because nothing in the UI hints at them:

- **Incremental re-bakes require correct checkbox semantics.** Uncheck *Export Geometry and Maps* only when geometry, textures and lightmap layout/resolution are unchanged (export took ~40 s in a measured world, not universally). Disable *Update Unmodified Lights* to skip unchanged direct-light passes; keep *Update Modified Lights and GI* enabled to recalculate changed lights and GI. Enabling both does not mean "changed lights only."
- **Texels-per-unit values are starting examples, not minimums**: the manual gives 1–5 for large outdoors, 10–20 for smaller outdoors, and 100 for a high-quality interior at 1 unit = 1 m. **20 does not prove an interior is undersampled.** Diagnose from chart density, padding, shadow detail, view distance and a rendered A/B before increasing resolution or blaming texel starvation.
- **`scaleInLightmap = 0` is an occluder switch.** Objects with Scale In Lightmap set to 0 are not baked at all, but **still cast shadows and contribute GI**. That is the clean way to author shadow-only geometry — no ShadowsOnly renderer, no lightmap space consumed.
- **Bakery treats all back-faces as opaque.** Single-sided shells, inverted normals, and "it looks fine in the editor" geometry will block light from behind with no visual warning. This is the root cause behind a whole family of "why is this wall black" bugs.
- **`BakeryAlwaysRender`** bakes an object even when its renderer is disabled — worth knowing if you disable renderers to hide helper geometry and then wonder where the lighting went. **`BakerySharedLODUV`** is Bakery's "lightmap stealing" (LODs reusing LOD0's lightmap).
- **Denoise → "Fix Bright Edges"** specifically targets bright fringes/fireflies around shadow boundaries — a distinct artifact from chroma blobs, and not fixed by more samples.
- **"Adjust Sample Positions"** exists to prevent lighting leaks by relocating samples. Try it before moving geometry when a thin wall leaks.
- **Light Probe Mode matters.** The current manual lists L2 (default, recommended with occlusion probes), L1 and Legacy. L1/L2 bake alongside lightmaps; Legacy gathers cubemaps in a separate, potentially slower pass and can disagree with nonphysical shaders. L2 has project-level ringing removal; shader-only de-ringing is no longer the sole option. Unity 2019.3's Legacy + occlusion-probe issue is historical, not universal.
- **Checker Preview / Atlas Preview validate texel density *before* baking** — the cheapest possible way to catch "this wall got 12 texels", which no amount of sample tuning will fix.
- **RTX mode is mandatory on Ampere and newer** GPUs, and Bakery wants the **Game-Ready** driver, not Studio.
- **Driver R590+ removed OptiX 6 support.** Bakery 1.96's `ftraceRTX.exe` fails with `Error (1546): Failed to load OptiX library`, even with a correctly installed driver. Use an owned newer Bakery with its **OptiX 9** path (1.98 has `ftraceRTX9.exe`), not copied system DLLs. A pre-R590 supported driver is a fallback only if upgrading Bakery is unavailable. Source: [NVIDIA's response to Bakery's developer](https://forums.developer.nvidia.com/t/optix-6-0-0-is-broken-on-driver-591-44/353738). Run the bundled tiny hardware test before committing to a scene bake.
- **Close Unity before a clean GPU-driver installation.** Saving and pausing is insufficient: live replacement produced a fatal D3D11 swapchain-reset dialog. Reopen afterward; restart HWiNFO too if its memory-junction sensor disappears because it retained the old NVAPI.
- **Light meshes: fewer, more complex meshes bake faster than many simple ones**, which is the opposite of the usual draw-call intuition. They also do not receive lighting and occupy no lightmap space. Physical intensity conversions: sun = Lux/π, point = Candela/π.
- The manual itself says *Render Selected Groups* is "currently less convenient than using **Sectors** for partial baking" — if per-area iteration is a core workflow, Sectors is the officially blessed path.

### Washed-out bake debug sequence

A shadowless realtime directional light is additive over lightmaps and penetrates all geometry; ceilings look fine (facing away), which disguises it.

0. **Zero-light baseline (first draft of a new world, or any "glow from nowhere"):** draft-bake with every Light, `BakeryLightMesh` and `BakerySkyLight` disabled. Every non-black pixel is an uncontrolled source: emissive material (intended?), Unlit or toon shader on environment (switch to Standard), skybox reflection on smooth surfaces (add/bake a reflection probe), skybox ambient on probe-lit renderers (add `LightProbeGroup` coverage / rebake probes). Clear the list, then add sources one at a time. [Lura CGWORLD 2024]
1. Sample the `.hdr` atlas directly — is the shadow present in the data?
2. Check renderer `lightmapIndex` / receive-GI settings.
3. Swap to a plain white material: renders flat **BRIGHT** = additive realtime light; flat **DARK** = missing lightmap.

### Without Bakery: Progressive GPU

Worlds without a Bakery licence bake with Unity's lightmapper. Same flow as `.omp/skills/world-pipeline/SKILL.md`
D.1 Lighting: draft bake → mood check → final bake → reflection probes.

**Presets** (`var s = Lightmapping.lightingSettings;` then set fields; create a `LightingSettings`
asset first if the scene has none):

| Field | Draft | Final |
|---|---|---|
| `lightmapper` | `ProgressiveGPU` | `ProgressiveGPU` (`ProgressiveCPU` on very large scenes, see below) |
| `lightmapResolution` (texels/unit) | 4–6 | 12–20 interiors, 2–4 terrain/exterior |
| `directSampleCount` / `indirectSampleCount` / `environmentSampleCount` | 16 / 128 / 64 | 64 / 1024 / 512 |
| `maxBounces` | 2 | 2–4 (keep equal to the draft if you judge brightness from the draft) |
| `lightmapMaxSize` | 1024 | 2048 |
| `filteringMode` | `Auto` | `Auto` |

Keep bounces equal between draft and final so the draft's brightness is trustworthy, exactly as
with Bakery presets.

**Scripted bake and wait.** `Lightmapping.BakeAsync()` returns immediately. Poll from separate
Unity MCP `execute_code` tool calls (never `Thread.Sleep`). `Lightmapping.isRunning == false`
is **not** done: the files land later. Wait for `LightingData.asset`'s mtime to pass the bake's
start time (see `.omp/knowledge/notes/lightmap-files-are-written-after-isrunning-goes-false.md`).
If `buildProgress` sits near 1 % for minutes, grep `Editor.log` for `PathTracer ... 0rpt`: a dead
GPU bake, not a slow one. Cancel (`Lightmapping.Cancel()`) and switch to `ProgressiveCPU`
(`.omp/knowledge/notes/progressive-gpu-lightmapper-zero-rays-hang.md`).

**Reflection probes, immediately after** (hard rule 6), once the lightmaps are on disk:

```csharp
foreach (var rp in Object.FindObjectsOfType<ReflectionProbe>(true)) {
    if (rp.mode != UnityEngine.Rendering.ReflectionProbeMode.Baked) continue;
    string path = rp.bakedTexture ? AssetDatabase.GetAssetPath(rp.bakedTexture)
        : $"Assets/Lighting/Probe_{rp.name}.exr";
    Lightmapping.BakeReflectionProbe(rp, path);
}
```

`Lightmapping.BakeAllReflectionProbes()` does not exist in 2022.3. Then check that the probe
`.exr` timestamps are newer than the lightmaps and that the probe files are not byte-identical
(skybox-only captures: renderers missing `ReflectionProbeStatic`).

## Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| GI Samples 16 | Default quality, moderate bake time | Dim interiors may still show faint chroma noise |
| GI Samples 32 | Clean dim interiors | ~4× the GI time of 16 — samples are √rays, so cost is quadratic |
| Per-object sample multipliers | Fixes only problem areas, cheap | Must identify affected objects manually |
| Higher atlas maximum | Can accommodate larger charts or different packing when the limit is restrictive | Does not automatically improve density; 4× texels per doubled texture dimension pair is not necessarily 4× scene memory |
| Uncompressed lightmap importer | Useful compression A/B test | Higher VRAM; shipping requires a measured target-platform budget, not a blanket prohibition |
| Scripted bake via window reflection | Automatable, supports selective bakes | Internal API — field/method names may change across Bakery versions |
| Draft preset (low texels + low samples) | Order-of-magnitude faster iteration; brightness still trustworthy if bounces are unchanged | Overwrites the final atlases; forces a full Render on the next preset switch |
| Samples Multiplier (`sampleDivisor`) alone | Same speedup lever without touching atlas layout — per-area bakes keep working | Only scales samples; texel starvation and atlas-size problems stay unchanged (and unseen) |
| Uncheck "Export Geometry and Maps" | Skips the entire export stage on unchanged geometry | Silently stale if anything *did* move — the bake looks fine and is wrong |
| Per-area groups + selected-only bakes | Rebake one room in a fraction of the time | Refused after ANY geometry edit or atlas-resolution change — batch edits, then bake |

## Edge Cases

- **An internal light needs an air cavity, not burial in solid SSS material.** Bakery's
  `RenderLMSSS` redistributes existing surface irradiance through the volume; it does not
  directly integrate a point embedded in solid glass. Make a hollow optical shell with an
  inward-facing inner boundary, valid thickness and nonoverlapping UV2, or put the light
  behind the glass in genuinely clear fixture air. Both shell boundaries belong to the
  same SSS group. Check that the ceiling, housing, cable or another surface does not occupy
  the cavity; source spread must fit within clear air. Do not fix this with emission or
  brightness escalation. Controlled Bakery1.98 test at identical source power: solid SSS
  outer meanHDR0.000011; hollow SSS0.22882; hollow without SSS0.001019; flipped-normal solid
  SSS0.000011. Flipping the solid volume is not a substitute for an illuminated inner wall.
- **A rejected geometry-changing selective bake can clear stored texture bindings.**
  Bakery1.98's `ValidateScaleOffsetImmutability` rejects changed atlas layout, but storage
  may already have been mutated. Do not save that partial state as a valid baked scene.
  Retain a pre-attempt snapshot of texture order, renderer IDs/ST and scene data. Reload the
  known-good state or do the required full bake. `ftLightmaps.RefreshFull()` cannot recover
  an empty `ftLightmapsStorage.maps` list; restoring texture paths alone also does not prove
  that renderer chart assignments remain correct. Verify a matched render after recovery.
- **A linear HDR screenshot can falsely make a readable room look black.** Direct `ARGBHalf`
  (`sRGB=false`) render-target → `RGB24 ReadPixels` → PNG does not supply the missing sRGB
  transfer. For ordinary visual-review PNGs, use the verified default
  `RenderTexture.GetTemporary(width,height,24)` (`ARGB32`, `sRGB=true`) while retaining the
  camera's HDR/post-processing settings, or explicitly implement and verify the transfer.
  Compare identical-pose captures before changing exposure or lighting. Floating-point linear
  readback remains appropriate for numeric HDR/irradiance measurements, not display-ready PNGs.
- **Blue tint baked INTO the lightmap** (not from probes): A/B test with `RenderSettings.reflectionIntensity = 0` — if blue persists, it's in the lightmap data (sky-lit hidden exterior faces with UV charts bleeding into interior charts), not a probe issue.
- **ProBuilder `ToMesh()` invalidates Bakery UV2** — always rebake after mesh edits.
- **Scripted scene edits don't dirty the scene** (`SetParent`, rename) — call `EditorSceneManager.MarkSceneDirty` before saving, or a Bakery reload wipes them.
- **Play mode requests revert silently on compile errors** — grep the console for `error CS` before assuming a script change took effect.
- `PlayerSettings.GetLightmapEncodingQualityForPlatformGroup` is **internal in Unity 2022.3** — must be called via reflection (see Snippet 1).
- **Mid-bake, the scene you are querying is not your scene.** Bakery swaps the editor to `Assets/Bakery/_tempScene.unity` for the duration of a render, so `GameObject.Find("…")` returns **null** for objects that plainly exist and every scene query lies. Check `ftRenderLightmap.bakeInProgress` before concluding an object is missing or a component failed to attach — verify after the bake lands, not during it.
- **Output folders and formats are configurable.** `Assets/BakeryLightmaps/` was the verified project's output, not a universal path. Read Bakery Output path, scene-named-output setting and format before watching files. A watcher on the wrong folder reports `baseline=0` and can time out while the bake succeeds.
- **Not every field you remember exists in your Bakery version.** Reflection on a missing field (e.g. `exportTerrainTrees` on `ftRenderLightmap`) fails silently, so a scripted "force this off" pre-bake step can be a no-op that gets cited for months as having done something. Assert the field was found before trusting the step.
- **Chart values move when the atlas repacks.** A renderer's baked-chart mean can change dramatically between bakes with no input change, purely because `lightmapScaleOffset` now points at a different slot. Confirm any surprising chart delta with a render before diagnosing it.

## Related

- `reference/examples.md` — complete copy-pasteable C# editor snippets
- [Silent lighting guides + Bakery manual — reviewed 2026-09-12](reference/silent-lighting-guides.md) — UVs/density, directional shader compatibility, light vs reflection probes, PPv2 setup/VR comfort, bake checklist, and corrections to historical advice.

- **The bundled Bakery source is the authority for anything scripted.** The wiki
  documents the UI, not the fields. Field/method names in this skill were verified
  against `<project>/Assets/Editor/x64/Bakery/scripts/ftRenderLightmap.cs`
  (`LoadRenderSettings` ~13113, `SaveRenderSettings` ~3150, `SampleCount` ~915,
  `sampleDivisor` 244, `ValidateSamples` ~5876). Grep that file before trusting a
  remembered field name — it is the ground truth and it ships with the package.
- Sources: [SOURCES.md](SOURCES.md).

Related lessons: [knowledge index → lighting-baking](../../knowledge/INDEX.md#lighting-baking), [knowledge index → probes-reflection-and-light](../../knowledge/INDEX.md#probes-reflection-and-light)

# Probes, reflection and light lessons

Scope: light probes, reflection probes, probe-lit renderers, runtime lighting states, VRC Light Volumes and measured lighting tuning in baked VRChat worlds.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Reflection probes: capture and persistence

- **Give every renderer a reflection probe should see `ReflectionProbeStatic` (OR it into the existing flags, per object; children aren't reached), then rebake only the probes; leave it off glass, video screens and small props** — `ContributeGI` alone captures pure sky. The tell is byte-identical probe `.exr` hashes across positions (the highest-numbered ambient probe legitimately differs).
- **With Bakery, set reflection probes to `mode = Custom` with `customBakedTexture` = the baked `.exr`; verify by grepping the scene YAML for `m_CustomBakedTexture`, not live `bakedTexture`** — a Baked probe's cubemap lives in the LightingDataAsset, which Bakery doesn't fill, so it goes NULL on reload (blue sky sheen) while same-session screenshots look fine. Box-projection Y range must cover the ceiling; if blue survives `reflectionIntensity = 0` it's baked into the lightmap (see SKILL.md Edge Cases).
- **After moving any landmark or area, sweep every reflection probe against its site and re-seat + rebake the stale ones** — scene-placed probes don't follow code-positioned objects; the symptom shows up as a "glazed" glossy surface reflecting raw sky, misreported as a material defect.
- **Before swapping a skybox, check what it feeds: it's cosmetic only if ambient is Flat and `BakerySkyLight.cubemap` is null; otherwise rebake. Rotate a lat-long HDRI with a closed-form `_Rotation` so its sun matches the baked light** — the bake locks the sun angle; pick a similar sun elevation, find the peak texel via `Blit` to `ARGBHalf` + `ReadPixels` (`GetPixels` fails on BC6H), and don't retry the MCP bridge during 4K HDR reimports.

## Light-probe bake verification

- **Run the Bakery probe pass right after a full Render whenever geometry or layout changed (a probe-only render is fine after editing only `probePositions`), close every `VRCSdkControlPanel` window first, reset a latched `userCanceled`, then verify `bakedProbes` variance and `GetInterpolatedProbe` at 2–3 rooms** — the pass can die silently (geometry-changed abort, or the SDK panel throwing on the temp scene) leaving a full-count but flat probe set and dynamic objects ~20× too dark; completion flags lie.
- **Snapshot the shared `<scene>_probes.asset` before baking an alternate (night) state, restore it after, then reopen the scene** — lightmaps are per state but probes are one asset; `AssetDatabase.Refresh` doesn't rebind the cached probes. Fingerprint: every probe agrees on chromaticity to three decimals; compare brightness with `SphericalHarmonicsL2.Evaluate` over 6 axes, not the DC term.
- **After swapping objects that shaded the probes (e.g. tree crowns), re-bake the probes; until then soften each probe's L1 term so its darkest direction is ≥ 30 % of L0, editing `LightmapSettings.lightProbes` of the open scene only, after saving** — the old crowns baked a downward-pointing L1 that darkens the new crowns' upward leaves; loading a second copy of the LightingData asset crashed Unity inside the light-probe update.

## Probe coverage and placement

- **Enumerate `LightProbeGroup`s scene-wide and judge coverage from world-transformed `probePositions` against room extents** — groups live under a lighting root, so per-room searches find none and you build duplicates; positions are local, so a transform-based AABB is garbage.
- **Place light probes with a raycast grid (floor+0.35 / floor+0.95 / ceiling−0.25, pushed above furniture bounds, sealed pockets dropped) instead of auto-placers; flag probes well below the median** — auto-placers bury probes in roofs and mattresses, which bake near-black and drag dynamic objects dark.
- **When an object blinks between unrelated colours, read the Console's "Light Probe tetrahedron is malformed … at (x,y,z)" first; for far/moving scenery outside the probe hull set `lightProbeUsage` and `reflectionProbeUsage` to Off** — outside the hull Unity extrapolates from degenerate tetrahedra; Off falls back to the uniform ambient probe (no rebake). `UseProxyVolume` without a proxy component silently means BlendProbes.
- **Fix one dark probe-lit prop on a lighting boundary by parking a `Renderer.probeAnchor` where the interpolated SH matches a good sibling, not by adding probes** — the look is the SH evaluated toward the camera, not L0 (9× gap inside a 1.3× L0 gap); new probes near the object sit in its own glow and overcorrect. No rebake.

## Probe-lit vs lightmapped renderers

- **Query `receiveGI` on objects reported as black silhouettes before aiming lights or rebaking; move anything larger than ~0.12 m that has a clean UV2 to `receiveGI = Lightmaps` + `ContributeGI`** — a Baked light never lights a probe-lit renderer directly, so extra lights in a probe dead zone change nothing and each attempt costs a bake. Read `lightmapIndex` only right after a bake.
- **Give furniture with no UV2 `ContributeGI` + `receiveGI = LightProbes` + shadows On, per renderer (enum is `UnityEngine.ReceiveGI`), and assert no lightmapped renderer lacks UV2 before baking** — it then casts contact shadows and occludes GI with no lightmap UVs or atlas space, instead of reading as a sticker; anything that has UV2 belongs on the lightmap instead.
- **On probe-lit scenery, drop `_OcclusionStrength` to ~0.25–0.3, measure decal-vs-ground compensation per site, and dim blown-out glowing props by albedo, not emission; first ask whether it should be lightmap-static at all** — probe-lit objects receive all light as indirect, so AO crushes everything and their albedo-to-render ratio differs from lightmapped neighbours in a site-specific way; rebaking fixes neither. On Bakery maps `ContributeGI` alone gives no lightmap without a group.

## Runtime lighting states

- **In a runtime lightmap swap, query every renderer with `lightmapIndex == -1 && lightProbeUsage != Off` and handle them by type: probes Off only for renderers that gain a lightmap, dim calibrated emission for emitters, synthetic SH for ordinary props** — probes can't be swapped from Udon, so probe-lit props keep the old bake's light; `LightProbeUsage.Off` binds a zero SH probe, not ambient, and renders them black. Avatars have no fix without Light Volumes.
- **Relight ordinary props left with no lightmap and no probe via `LightProbeUsage.CustomProvided` + SH (`unity_SHAr/Ag/Ab` = `(0, grad, 0, base)`) in a property block, scaled per renderer from nearby lightmapped irradiance** — emission ignores normal and albedo, so props pass a luminance check but look like flat cut-outs; one global SH lights props up to ~8× wrong. Find the list by query, not from a reviewer's list.
- **In a lights-off state, judge each fixture against the key light (window/sky) and darken its albedo with a `_Color` property block; keep albedo and emission block lists disjoint** — an albedo authored to be seen under its own bulb still reads "on" with zero emission; `SetPropertyBlock` replaces, so a renderer in both lists keeps only the last; re-check what's beneath after darkening.

## VRC Light Volumes

- **Check that world materials are LV-aware (lilToon/Poiyomi) before relying on VRC Light Volumes; on LV 2.x keep Bakery Compress volumes off, unique names per volume, run one `GenerateAtlas` + `SyncUdonScript` after the bake, invoke `FixLightProbes` manually after probe-only renders, and darkness-clamp buried voxels** — in a Standard lightmapped world volumes only light avatars; voxels in bedding/floors bake near-black unflagged; concurrent atlas runs blow objects out white. Treat LV 3.0 as a migration, not a bump.
- **Set Intensity on both the `LightVolume` authoring component and its instance (authoring is the source of truth); Intensity 0 cleanly excludes a volume** — the ExecuteAlways component re-pushes its value on the next editor update, so an instance-only write reads back fine then reverts and ships enabled (LV 2.x).
- **Measure avatar lighting with a ~0.35 m lilToon sphere at each player pose, frame-diffed enabled vs disabled, in play mode** — a Standard sphere has no light-volume path and edit mode pushes no volume globals, so day/night sweeps return identical values and look like a dead toggle.

## Tuning by measurement

- **Land a target luminance and hue in two renders by solving `C = Z + m·D` per channel (measure the zero-knob render Z, split hue geometrically), isolating pixels by renderer-enable toggle** — trial and error converges on level and leaves hue wrong; solve in linear (`SetColor` converts gamma, `SetVector` doesn't); if the first re-render misses, the knob isn't linear, so find the missing light path instead of iterating.

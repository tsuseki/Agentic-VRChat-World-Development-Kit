---
name: vrchat-world-gotchas
description: >-
  Historical VRChat world diagnostics from Haï~'s Knowledge Index — excessive
  Interact/Pickup reach, canvas raycast lasers, UI scrolling while walking, current
  Maximum vs Recommended Capacity and legacy doubling, portal blocking, Bakery Custom
  reflection-probe references, EditorOnly bake geometry, FBX lightmap-UV packing,
  camera rendering-path troubleshooting, legacy Dynamic Bones and remote IK.
  These 2021–2022 observations require current-version checks.
  Use when debugging a "why is this happening" oddity in a VRChat
  world, sizing Udon player arrays, building menu canvases, blocking portals, or before a
  lighting bake or world publish.
---

# VRChat world gotchas

Non-obvious behaviours from Haï~'s Knowledge Index, filtered down to what is actually
surprising and bites in these projects. Every entry is a **symptom you would otherwise
misdiagnose**. Basics that any Unity/VRChat guide covers are deliberately excluded — see
*Read but not included* at the bottom.

**Read [the dated guide refresh](reference/hai-guides-refresh.md) first** for official
capacity corrections, supported portal blocking, source coverage and historical caveats.
The entries below are diagnostic candidates, not current runtime guarantees.

> Normal Notion URL reads may return only an application shell. The inspected
> `reference/fetch-notion-page.py` retrieves raw `loadPageChunk` blocks; aliases and
> external-object mentions are not fully rendered. See the refresh for access details.

## Quick reference

| Symptom | Candidate cause / status | Next check |
|---|---|---|
| Can grab/use a Pickup or Interact from across the room | Historical intervening-trigger bug; desktop also has extra reach | Compare proximity semantics and trigger-enabled/disabled behavior |
| UI laser hits a menu from any distance | Historical canvas-collider raycast behavior | Test disabling the **Collider**, not just Graphics Raycaster |
| Menu scrolls while the player walks | Movement input may reach UI navigation | Test Navigation=None and Scroll Sensitivity=0 without breaking intended controls |
| Udon player array overflows at a packed event | Recommended Capacity is not Maximum; privileged joins may exceed Maximum | Plan headroom, bounds-check and handle a full pool; no universal 2×+2 rule |
| Mirror-like surfaces black; wrong probe sampled | Historical asset-pack camera rendering-path issue | Inspect assigned Reference Camera and test Use Graphics Settings |
| Custom probe lost its cubemap after probe baking | Historical Bakery reference-loss report | Check/restore intended Custom and Sky Light cubemaps post-bake |
| Lightmap quality dropped after FBX changes | Historical importer/UV-packing report | Compare generated UV2 and isolated export |
| Black squares in a Progressive GPU bake | Historical Double-Sided GI mitigation | Test relevant materials; not a universal cure |
| Off-screen parts of level baked incorrectly | Historical Prioritize View/MIS report | Compare settings on installed Unity; no blanket MIS disable |
| Distant decoration frozen; remote bones inaccurate | Legacy Dynamic Bones / distance-sensitive IK report | Verify at actual viewing distances; do not infer PhysBone behavior |
| Meshes deform/jitter, worst in VR | Built far from world origin | Keep the main play area near (0,0,0) |
| Soft particles, depth-fade water/shoreline or depth fog render flat or hard-edged in a fully baked world | No camera depth texture without a shadowed realtime light | Set `VRCCameraSettings.ScreenCamera.DepthTextureMode` from Udon; never add a dummy realtime light. See `unity-vrc-world-sdk-3/references/lighting.md` § "Camera depth texture without a realtime light" |
| `error CS` for missing Bakery/PPv2 types in an editor tool after uninstalling one of them | Stale `BAKERY_INCLUDED` / `UNITY_POST_PROCESSING_STACK_V2` define symbol | Remove it in Player → Other Settings → Scripting Define Symbols (see below) |

## Interaction & UI

### Excessive Interact/Pickup reach: historical trigger diagnostic
Haï's 2021 guide says an intervening trigger **may sometimes** cause unlimited reach,
not that every trigger always does. Compare with/without the suspect volume before
removing or relayering a functional zone trigger. This has not been reproduced here.

Current Pickup proximity documentation
also applies to Interactables: desktop has scale-sensitive extra reach; VR compares hand
distance to the collider. Proximity 0 requires VR hover inside the collider but still
allows desktop compensation. See the refresh for the accessible official source mirror.

### Canvas raycasting: historical Collider versus Graphics Raycaster distinction
Haï reports that disabling the canvas **Collider** removes both raycast and laser,
while disabling **Graphics Raycaster** stops click events but leaves the laser.
Test both pointer visibility and actual interaction on current desktop/VR clients.
This is a troubleshooting candidate for large generated multi-tab menus (e.g. an 11-tab
menu in SlaveAuction2026), not a verified current behavior.

### UI scrolls when the player moves
The guide's recipe for movement input reaching UI navigation is:
- **Navigation Mode = None** on UI elements.
- **ScrollRect → Scroll Sensitivity = 0**.
These settings also remove those navigation/scrolling routes; preserve a usable intentional
way to operate the menu, and test desktop plus VR input.

## Instance capacity — Maximum and Recommended are different

The current official world-creation guide
distinguishes **Maximum Capacity** (ordinary join limit) from **Recommended Capacity**
(public-listing/discovery threshold). Instance creator, world creator and group owner may
join beyond capacity unless they lack permission to enter/see that instance.

**Legacy worlds only:** without a Recommended Capacity field, the old capacity becomes
Recommended Capacity and twice it becomes Player Capacity. Haï's 2021 `2 × Capacity + 2`,
40/82 cap and speculative staff slots are not current general guarantees.

Never size a player pool from the recommendation alone. Plan for permitted over-capacity
joins, bounds-check each insertion/index and handle exhausted pools without corrupting
state. A guessed fixed role count is not a universally safe maximum. See the
[refresh](reference/hai-guides-refresh.md)
for official repository evidence and access limitations.

## Networking & players

### Legacy Dynamic Bones and remote IK at distance
Haï reports that distant Dynamic Bones stop simulating, including world-side bones,
and that distant remote players have lower-fidelity IK. These are 2021 observations;
do not extrapolate Dynamic Bone behavior to PhysBones or promise current thresholds.
Test at actual viewing/capture distances before building mechanics or RenderTexture
views that depend on bone fidelity.

### Blocking dropped portals
First evaluate the documented **Forbid User Portals** setting on
VRC Scene Descriptor.
Its documented scope is portals opened from the world menu, not every portal source.

[The historical portal recipe](reference/portal-blocking.md) preserves Haï's 2021
Water-layer/`PortalInternalDynamic` relocation and respawn-point alternatives.
Names, layers and the reported collider-buffer crash are not supported current contracts;
do not deploy that workaround without proving the descriptor setting is insufficient and
checking current behavior.

## Lighting & baking

### Bake-only geometry: historical Bakery technique
Haï reports that an **EditorOnly renderer is excluded from GI** and suggests:

1. Set a **parent** GameObject to EditorOnly.
2. Keep the **renderer itself** *not* EditorOnly.
3. Set **Scale in Lightmap = 0** on those renderers so they claim no atlas space.

The guide reports bake-time GI contribution with build-time stripping of the subtree.
Verify on the installed Bakery version and use only for helpers without a runtime
shadow/reflection role; this is not inherently better than every ShadowsOnly occluder.

### Custom probe references after baking: historical Bakery report
Haï reports that baking reflection probes can clear **Custom** probe cubemap references.
Check the intended cubemap assets after every probe bake, including any shared by a
Bakery Sky Light. Do not assume this is the cause of every null probe.

Workspace policy separately requires baking probes immediately after each lightmap bake.
Afterwards check/restore intentional Custom references and Sky Light cubemaps; checking
only for non-null does not establish that the correct cubemap is assigned.

### FBX changes and lightmap-UV packing
Haï reports that adding a mesh to an FBX may reduce existing meshes' generated lightmap
quality, even when the added mesh is absent from the scene. Treat the stronger
cross-mesh/per-FBX sharing claim as historical and importer-dependent.

One mesh's material submeshes use that mesh's UV channels; merely adding a material
does not inherently shrink UV islands. Inspect the actual generated UV2 rather than
assuming every new material or FBX object steals atlas space.

Cheap test before blaming the lightmapper: re-export the mesh alone and compare UV2 packing.
Relevant to the ENV shells (3 submats each) and any Blender export that bundles several
objects into one FBX.

### Progressive GPU artifact candidates (historical)
Haï reports off-screen bake issues with **Prioritize View** and inconsistent results
with **Multiple Importance Sampling**, recommending considering disabling them when
issues occur, especially for final bakes. Compare on the installed lightmapper version;
do not make disabling MIS a universal final-bake preset from this report.

The guide also suggests **Double-Sided Global Illumination** to reduce black squares
and says it is unnecessary with Bakery. Treat this as a relevant-material experiment,
not a guaranteed cure or a blanket instruction for every material.

### Bakery + Realtime GI needed a source patch (historical)
Under Unity 2018 + older SDK3, Bakery's Realtime GI worked in the editor but not in game.
The fix was an early return in `ftLightmapsStorage.Awake()` when the stack trace contains
`PopulateAllPrefabSerializedProgramAssetReferences` — i.e. VRChat's build-time prefab
serialization pass. The author explicitly marks this potentially outdated as of
2022-01-28 and reports Unity 2019-era SDK3 working without it.

Keep only as a diagnostic lead for editor/build divergence. Do not patch vendored
Bakery from the old snippet without reproducing a current failure.

## Authoring

### Rendering Path: historical mirror/probe diagnostic
Haï reports black mirror-like reflections or unexpected probe selection when an imported
asset-pack scene forced Main Camera's Rendering Path; restoring **Use Graphics Settings**
was the suggested fix. It is a 2021 diagnostic candidate, not the universal cause.

Current descriptor docs identify the **Reference Camera** as the settings source. Inspect
that assignment rather than assuming an object named Main Camera is authoritative.
Confirm the actual client result before attributing a reflection problem to this setting.

### Don't build far from the world origin
Float precision makes distant meshes deform or move noticeably, and it is **worst in VR**,
where the stereo baseline makes small errors legible. Keep the main hangout area near
(0,0,0).

Two live cases: Racing's 2400 m circuit (unavoidable — the whole point is a long track), and
SlaveAuction2026's `*_Props` cluster colliders parked ~230 m out in the void (memory
`slaveauction2026-world-colliders`) — that one is fine precisely because nobody stands there.
Distance only hurts where players *are*.

### Stale define symbols after removing Bakery or Post Processing v2
Bakery and Post Processing v2 add `BAKERY_INCLUDED` / `UNITY_POST_PROCESSING_STACK_V2` to Player → Other
Settings → Scripting Define Symbols, and removing the package does **not** remove them. Editor tools that `#if` on
them (VRWorld Toolkit among others) then fail with `error CS` for missing types. Delete the stale symbol rather than
reinstalling the package. [VRWorld Toolkit README, 2026]

### Intro-then-loop audio without mangling the intro
Haï recommends a single WAV containing intro followed immediately by loop body, with
**UniWaveLoop** defining the loop start. This preserves the attack instead of crossfading
across the entire file. Current package/SDK compatibility was not checked.
Whole-file crossfades remain appropriate for steady ambience without a distinct intro.

## Design

### Proactively test colour-dependent features
Colourblind players **may not know** that a feature depends on colour, so silence is not
evidence of accessibility. Haï recommends identifying colour-coded mechanics, telling
colourblind testers which they are, and asking targeted questions rather than relying
only on unsolicited feedback. This is not a claim that testers can never notice an issue.

Derived application: pair important colour states with labels/shapes/icons and ask testers
to distinguish the actual gameplay states. See the refresh for source versus derived advice.

### Japanese font choice is a real design decision
Japanese fonts carry style connotations the same way English fonts do, and JP players have
opinions about the defaults. Ask a localizer which font suits the world instead of taking
whatever ships. Google Fonts has a Japanese subset filter
(https://fonts.google.com/?subset=japanese). Likely true for other languages too.

## Staleness

All three guides are 2021–2022 material, re-read on 2026-09-12, not current runtime tests.
Capacity has been corrected against official documentation. Trigger reach, canvas lasers,
portal internals, EditorOnly GI, probe-reference loss and rendering path remain historical
diagnostic candidates: plausible mechanisms are not compatibility evidence.

## Read but not included

Judged already-known or already-recorded, so future sessions don't need to re-read the
source: minimum near clipping plane for close-up faces (already run at 0.001 via
VRCCameraSettings); Unity V-key vertex snapping;
baked-vs-realtime fundamentals and the Contribute GI / Generate Lightmap UVs / probe
placement checklist from the beginner sub-page; tool recommendations (VRWorld Toolkit — now covered in
`unity-vrc-world-sdk-3/references/community-world-tooling.md`, CyanEmu — now ClientSim, UdonSharp, Pumkin,
CyanTrigger); listing your own worlds via the VRChat profile page rather than the Worlds page.

Tool status 2026-10 (from each repo's README / archived flag): CyanTrigger deprecated by its author (no new
features; learn the official tools); CyanPlayerObjectPool archived — use SDK `VRCPlayerObject` (3.7.4+);
NetworkedEventCaller superseded by `[NetworkCallable]` with parameters (3.8.1+); z3y/shaders archived — successor
Graphlit; USharpVideo unmaintained since 2023 and its README suggests realtime GI (conflicts with the fully baked
rule); MerlinVR/UdonSharp 0.x is legacy — UdonSharp ships bundled with the Worlds SDK.

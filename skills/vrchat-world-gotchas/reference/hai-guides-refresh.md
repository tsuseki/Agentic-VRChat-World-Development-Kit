# Haï world guides — refresh 2026-09-12

Documentation research, not Unity/VRChat runtime verification. These are third-party observations and recommendations, not user preferences or compatibility guarantees. This note records corrections and decision points rather than duplicating the main skill.

## Source coverage and vintage

All three supplied pages were read, including their direct text, lists, toggles and the portal code. Normal URL reads returned only Notion's application shell; the existing `fetch-notion-page.py` was inspected and its `loadPageChunk`/render functions used in memory successfully. All content descendants of each target page were present. Embedded media were represented by links, not visually inspected; linked guides/tools were not recursively audited. The helper does not render alias blocks or resolve `eoi` external-object mentions, so a blank “See:” is not evidence of a missing recommendation.

| Guide | Notion root created (UTC) | Root last edited (UTC) | Coverage |
|---|---|---|---|
| [World Lighting](https://hai-vr.notion.site/World-Lighting-abc870d06dd647ac9fcd60fe60af05d9) | 2021-11-30 | 2022-01-28 | 40 reachable blocks: beginner-page link, old Realtime GI patch, Double-Sided GI, EditorOnly bake helpers, Custom probes, FBX UVs, Progressive GPU options |
| [Miscellaneous World Tech](https://hai-vr.notion.site/Miscellaneous-World-Tech-ad2f49c88f444ec58c1cab3c33d469e4) | 2021-11-30 | 2021-12-12 | 71 reachable blocks: audio intro loops, profile listing, origin precision, Interact/Pickup reach, canvas laser, clipping, scrolling, snapping, rendering path, toolkit, capacity, Dynamic Bones/IK, portal alternatives and code |
| [World Design](https://hai-vr.notion.site/World-Design-6a6b0f4a447e44078cd62422a886c203) | 2021-12-02 | 2021-12-11 | 22 reachable blocks: colourblind testing and Japanese font/localizer advice |

Root metadata establishes guide vintage, not a promise that every descendant last changed on that date. The World Lighting text itself explicitly dates its Bakery/Realtime GI warning as potentially outdated by 2022-01-28. No newly authored 2026 advice was found; the useful refresh is correcting how strongly the existing notes stated these historical observations.

## Capacity: retire the universal `2 × Capacity + 2` rule

Haï's 2021 guide describes a website soft cap, doubling, two privileged slots, a normal 40/82 limit, and speculation about staff slots/~130-player events. **Do not use those as current numeric guarantees.**

The official [Creating Your First World, step 4](https://creators.vrchat.com/worlds/creating-your-first-world/#step-4---configure-your-world-in-the-sdk-build-panel), read from its [official repository source](https://raw.githubusercontent.com/vrchat-community/creator-docs/main/Docs/docs/worlds/creating-your-first-world.md), says:

- **Maximum Capacity** limits ordinary joins; **Recommended Capacity** is a separate public-listing/discovery threshold.
- The instance creator, world creator, or group owner can join beyond capacity **unless they lack permission to enter/see the instance**. This is not a fixed two-slot guarantee.
- **Legacy only:** worlds uploaded without Recommended Capacity map their old capacity to Recommended Capacity, and twice that value to Player Capacity.

Action: distinguish the actual maximum from the recommendation when planning player pools. Budget for permitted over-capacity joins, bound every insertion/index, and handle exhausted pools without corrupting game state. Do not derive a universally safe array size from either the recommendation or a guessed fixed role count. Numeric platform maxima and special event arrangements were not established by this refresh.

## Interaction and portal corrections

- **Trigger/infinite reach:** Haï says Interacts/Pickups *may sometimes* have infinite range with an intervening trigger. The old skill incorrectly strengthened this to “any trigger always does it.” Keep it as an A/B diagnostic hypothesis, not a current API rule or reason to remove functional zone triggers blindly.
- **Current proximity semantics:** [official VRC Pickup docs](https://creators.vrchat.com/worlds/components/vrc_pickup/) ([repository source](https://raw.githubusercontent.com/vrchat-community/creator-docs/main/Docs/docs/worlds/components/vrc_pickup.md)) apply their Proximity rules to Interactables too. VR ray distance is measured from the hand to the collider; desktop subtracts scale-sensitive extra reach. At proximity 0, VR hover requires the hand inside the collider, but desktop still has compensation. This can explain apparently excessive reach without the historical trigger bug.
- **Canvas/input:** the collider-versus-Graphics-Raycaster distinction and Navigation=None/Scroll Sensitivity=0 remain historical troubleshooting recipes. Test pointer visibility, clicks and intended scrolling on desktop and VR before adopting them; setting sensitivity to zero deliberately removes that scrolling route.
- **Portal blocking:** the current [VRC Scene Descriptor docs](https://creators.vrchat.com/worlds/components/vrc_scenedescriptor/) ([repository source](https://raw.githubusercontent.com/vrchat-community/creator-docs/main/Docs/docs/worlds/components/vrc_scenedescriptor.md)) document **Forbid User Portals**, described as preventing portals opened from the world menu. Prefer evaluating that supported setting for this need. Do not infer that it blocks every possible portal source.
- The Water-layer/`PortalInternalDynamic` detection, respawn-point relocation, and collider-buffer reallocation recipe in [portal-blocking.md](portal-blocking.md) is retained as **2021 historical implementation evidence**, not a current supported contract. The source only reports an unexplained crash in its own setup; it does not establish that modern OverlapBoxNonAlloc always crashes. Moving a respawn transform can affect its actual spawning purpose, so it is not a harmless substitute for a descriptor setting.

Workspace policy, separately: explicitly requested pickups use proximity 0.1 and no Auto Hold; props otherwise receive no colliders, and stations are not added unless asked. None of these policies are inferred from Haï's recommendations.

## Lighting and camera qualifications

- **Rendering Path:** Haï reports that restoring Main Camera → Use Graphics Settings fixed black mirror-like reflections/wrong probe selection in reused asset-pack scenes. Treat this as a 2021 diagnostic candidate. Current descriptor docs identify the **Reference Camera** as the settings source; inspect which camera is actually assigned rather than relying on the GameObject name. Neither source proves that rendering path is the cause of every black mirror or that every camera field is copied into every current client.
- **Progressive GPU:** Haï recommends *considering* disabling Prioritize View and Multiple Importance Sampling when artifacts occur, especially for final bakes. The old blanket “turn both off” instruction was stronger than the source. Compare on the installed Unity/lightmapper version; do not globally disable MIS merely because of the 2021 report. Double-Sided GI is likewise a proposed black-square mitigation, not a universal cure or a setting to enable indiscriminately.
- **Bakery:** retain EditorOnly-parent bake helpers and Custom-probe-reference checks as diagnostics; verify installed-version behavior. Only remove bake helpers from builds if they have no runtime shadow/reflection role. Do not infer a Custom-probe wipe as the proven cause of every null cubemap. Workspace policy still requires probe baking after every lightmap bake, followed by checking/restoring intentional Custom cubemaps and Sky Light references.
- **FBX UVs:** a mesh's material submeshes share that mesh's UV channels, but merely adding a material does not inherently shrink UV islands. Haï's stronger cross-mesh/per-FBX packing claim is historical and importer-dependent; inspect generated UV2/re-export separately before committing a split.
- **Realtime GI patch:** explicitly obsolete/potentially outdated per the author in Unity 2019-era SDK3; do not patch vendored Bakery from the Unity 2018 snippet without reproducing an actual current failure.
- **Near clipping:** the source limits its “minimum possible” advice to small chill worlds and warns about large open spaces. Keep this scene-dependent; verify close faces together with far depth precision rather than copying a tiny universal near plane.

## Accessibility, design and remaining tech

The design page contains only the two topics already captured in the skill, not a broader accessibility checklist. Useful application of those topics:

- **Source advice:** proactively tell colourblind testers which mechanics use colour and ask targeted questions; absence of complaints is not proof of accessibility. Avoid the categorical claim that colourblind people can never notice/report an issue. The linked talk is [Douglas Pennant, Solving an Invisible Problem](https://www.youtube.com/watch?v=KbFs9ghIIEI), with the guide pointing to [27:20](https://www.youtube.com/watch?v=KbFs9ghIIEI&t=1640s).
- **Derived design action, not a quoted source claim:** pair important colour-only states with readable labels/shapes/icons, then ask testers to distinguish the actual gameplay states. This turns proactive review into an actionable acceptance check.
- **Source advice:** ask a Japanese localizer about font style, not just whether glyphs display; [Google Fonts Japanese filter](https://fonts.google.com/?subset=japanese) is the linked discovery route. **Derived action:** check actual localized strings for glyph coverage, size and layout; font discovery does not itself establish the font's redistribution license.
- **Tech retained without duplication:** keep main hangout geometry near the origin; assess distance-sensitive bone/IK data at the distances actually used; retain single-WAV intro+loop as Haï's UniWaveLoop technique, with present package/SDK compatibility unverified. Dynamic Bone advice is explicitly legacy, not evidence of identical PhysBone behavior. Toolkit installation advice belongs to the source author, not a user instruction to install it. Website profile-listing UI and vertex-snapping tips add no new workspace requirement.

## Access limitations

Creators-site reads for the scene descriptor and world-publication tips returned HTTP 403; their official `vrchat-community/creator-docs` raw GitHub files were readable. Capacity and pickup rules above were read from that same official source repository. A guessed `worlds/udon/players/get-players.md` raw path returned 404 and was not used as evidence. No access failure remains for the three assigned Haï guide bodies. No installation, scene change, build, tests, or in-client verification was performed.

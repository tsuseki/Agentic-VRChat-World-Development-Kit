# Sources: vrchat-world-gotchas

Bibliography and attribution for `.omp/skills/vrchat-world-gotchas/SKILL.md`. Not needed to use the skill; open it only to check
where a claim or tag came from. Sections are grouped by the file that cites them.

## `SKILL.md` — Haï guides

Source: Haï~'s Knowledge Index — [World Lighting](https://hai-vr.notion.site/World-Lighting-abc870d06dd647ac9fcd60fe60af05d9),
[Miscellaneous World Tech](https://hai-vr.notion.site/Miscellaneous-World-Tech-ad2f49c88f444ec58c1cab3c33d469e4),
[World Design](https://hai-vr.notion.site/World-Design-6a6b0f4a447e44078cd62422a886c203).
All three main guides re-read 2026-09-12; their last-edit metadata is December 2021–January 2022.
The beginner sub-page was read in the earlier 2026-08-05 pass, not refreshed here.

## `reference/portal-blocking.md`

Source: [Haï's Miscellaneous World Tech](https://hai-vr.notion.site/Miscellaneous-World-Tech-ad2f49c88f444ec58c1cab3c33d469e4),
last edited December 2021; re-read 2026-09-12. This is archived implementation evidence,
not a current supported API contract or a runtime-verified recipe.

## `SKILL.md` — stale define symbols, tool status (added 2026-10-13)

Sources: [VRWorld Toolkit README "Troubleshooting"](https://github.com/oneVR/VRWorldToolkit#troubleshooting),
[VRWorldToolkit issue #34](https://github.com/oneVR/VRWorldToolkit/issues/34) (2025-09);
tool status from each repo's README / GitHub archived flag, read 2026-10-13:
[CyanTrigger](https://github.com/CyanLaser/CyanTrigger), [CyanPlayerObjectPool](https://github.com/CyanLaser/CyanPlayerObjectPool),
[NetworkedEventCaller](https://github.com/Miner28/NetworkedEventCaller), [z3y/shaders](https://github.com/z3y/shaders),
[USharpVideo](https://github.com/MerlinVR/USharpVideo), [MerlinVR/UdonSharp](https://github.com/MerlinVR/UdonSharp).
Depth-texture row points to `unity-vrc-world-sdk-3` (official [VRC Camera Settings](https://creators.vrchat.com/worlds/udon/vrc-graphics/vrc-camera-settings)).

## `SKILL.md` — official docs, colour-blindness, further reading (moved from inline 2026-10-16)

- Pickup proximity (also applies to Interactables): [vrc_pickup](https://creators.vrchat.com/worlds/components/vrc_pickup/).
- Maximum vs Recommended Capacity: [Creating your first world, step 4](https://creators.vrchat.com/worlds/creating-your-first-world/#step-4---configure-your-world-in-the-sdk-build-panel).
- Forbid User Portals: [VRC Scene Descriptor](https://creators.vrchat.com/worlds/components/vrc_scenedescriptor/).
- Colour-blindness section: Douglas Pennant, *Solving an Invisible Problem: Designing for Color-Blindness in Games*, https://www.youtube.com/watch?v=KbFs9ghIIEI
- Further reading (was in "Staleness"): Silent's advanced light-baking guide, Bakery-era, good on mixed baking and shadowmask (mixed/Shadowmask is off the table in these projects): https://gitlab.com/s-ilent/SCSS/-/wikis/Other/Light-Baking

## `reference/portal-blocking.md` — Forbid User Portals (moved from inline 2026-10-16)

[VRC Scene Descriptor](https://creators.vrchat.com/worlds/components/vrc_scenedescriptor/)
([official source mirror](https://raw.githubusercontent.com/vrchat-community/creator-docs/main/Docs/docs/worlds/components/vrc_scenedescriptor.md)).

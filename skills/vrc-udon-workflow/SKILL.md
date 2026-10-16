---
name: vrc-udon-workflow
description: >-
  Complementary VRChat UdonSharp project workflow: Builder First reusable modules,
  Runtime/Editor responsibility split, project-owned specifications and handoff,
  deliberate optional Fukuro Udon evaluation, Unity MCP-assisted authoring,
  safe Windows text editing, and texture import versus download/VRAM decisions.
  Use for module architecture, scene-generation contracts, knowledge transfer,
  or these workflow decisions; not as a second Udon API or World SDK manual.
  Networking, persistence, UI, DataLists, runtime performance, and downloader
  lifecycle route to unity-vrc-udon-sharp; scene components, platform rules,
  lighting, build validation, and upload route to unity-vrc-world-sdk-3.
license: MIT
metadata:
  author: sechiro; workspace adaptation
  version: "1.0.0"
  upstream-commit: "1a19d149b1730cae4dbde9dd5d9a4e4aa50d0c0f"
  tags: vrchat, udonsharp, builder-first, editor, workflow, specifications, fukuro, texture-memory
---

# VRChat Udon project workflow

A selective adaptation of [sechiro/VRCUdonSkills-for-Codex](https://github.com/sechiro/VRCUdonSkills-for-Codex), not an installation of its twelve overlapping skills. See [provenance and topic dispositions](references/provenance.md) and the retained [MIT license](LICENSE).

## Governing rules come first

Read workspace `.omp/AGENTS.md` and `.omp/RULES.md`, then the target project's own `AGENTS.md`, `DESIGN.md` and `TASKS.md` when present. This skill does not relax them or grant permission to create packages, docs, scaffolds, colliders, seats or pickups.

- Ordinary props remain collider-free; remove primitive auto-colliders. Movement barriers use the workspace's simple-box/ramp rules, never walkable MeshColliders.
- No stations or pickups without explicit request. Requested pickups retain workspace proximity `0.1f`, `AutoHoldMode.No`, gravity and networking, including imported prefabs and platform overrides. Follow the workspace's existing-pickup audit requirement when modifying a scene.
- Drive the open Editor through the mounted Unity MCP tools, not scene/asset YAML. Mark scripted hierarchy mutations dirty before saving; read the console after script changes and resolve `error CS` before proceeding.
- Built, generated, placed, textured or lit content needs the stage reviewer (`dressing-reviewer` before the bake, `final-reviewer` after it) returning **SHIP IT**. `dressing-reviewer` approval is not final lighting sign-off. Bake reflection probes immediately after each lighting bake.
- Reuse existing project conventions. Do not install Fukuro, UdonSharp, MCP or other packages automatically; do not edit global agent settings. Never push local backup repositories.

## Load only the relevant guidance

| Task | Authoritative route |
|---|---|
| Builder First, reusable module boundaries, regeneration ownership | [Module and project contract](references/module-and-project-contract.md) |
| Project-owned specs, external handoff, import/export knowledge | [Module and project contract](references/module-and-project-contract.md) |
| Evaluate an existing or explicitly requested Fukuro integration | [Optional Fukuro adoption](references/module-and-project-contract.md#optional-fukuro-adoption) |
| MCP-assisted Builder/Editor workflow; Windows editing hazards | [Editor and editing workflow](references/editor-and-editing.md) |
| Bundled images versus downloads, texture residency, World Space mipmaps | [Texture decisions](references/texture-decisions.md), after the World SDK performance reference |
| Udon constraints, APIs, networking/ownership/late joiners | `.omp/skills/unity-vrc-udon-sharp/SKILL.md`; follow its routing guide, not imported sechiro networking rules |
| Persistence/PlayerData/PlayerObject, UI/input, DataList/DataDictionary, heavy runtime work | `.omp/skills/unity-vrc-udon-sharp/SKILL.md` and its relevant persistence, UI, constraints/API or performance reference |
| Custom inspectors, Udon program assets, assembly definitions | `.omp/skills/unity-vrc-udon-sharp/SKILL.md` and `references/editor-scripting.md` / `references/assembly-definitions.md` |
| Download APIs, cleanup, stock/streaming caches and crossfades | `.omp/skills/unity-vrc-udon-sharp/SKILL.md` and `references/web-loading.md` / `references/image-loading-vram.md` |
| Components, layers, platform optimization, lighting, validation/upload | `.omp/skills/unity-vrc-world-sdk-3/SKILL.md` and its task-specific references |
| Measured world performance or baked-lighting diagnostics | Existing `vrchat-world-optimization` or `bakery-light-baking` skill as appropriate; do not substitute texture arithmetic for profiling |

Do not load all references by default. The two established Udon/SDK skills remain the implementation authorities; this skill adds workflow decisions, not competing API recipes.

## Smallest useful workflow

1. Inspect current code, scene and project-owned requirements; establish what is user-authored versus generated.
2. Define module inputs, outputs, source of truth, editable fields and regeneration boundary. For a small hand-authored feature, do not invent a Builder.
3. Choose Editor-time wiring versus actual runtime work. Use the established Udon skill for any runtime design or API choice.
4. Change only the authorized objects/files. Keep package choices, external guidance and documentation conditional on the task.
5. Prove the changed path: inspect Editor output, compile/console, run the interaction, and use VRChat Build & Test when client behavior matters. Editor inspection alone cannot prove networking or persistence.
6. Update the existing project record when required by the task/governing workflow. Report observed results and remaining verification limits; create no automatic documentation pack.

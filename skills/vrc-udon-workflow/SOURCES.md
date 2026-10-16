# Sources: vrc-udon-workflow

Provenance and selection record. Not needed to use the skill.

## Source snapshot

- Repository: [sechiro/VRCUdonSkills-for-Codex](https://github.com/sechiro/VRCUdonSkills-for-Codex).
- Default branch observed: `main`.
- Pinned commit: [`1a19d149b1730cae4dbde9dd5d9a4e4aa50d0c0f`](https://github.com/sechiro/VRCUdonSkills-for-Codex/commit/1a19d149b1730cae4dbde9dd5d9a4e4aa50d0c0f), authored 2026-04-17T03:26:33Z.
- Inspected for this integration: 2026-09-27. All twelve `skills/*/SKILL.md` entrypoints and `guides/texture-and-vram-optimization.md` were read, with the relevant core/module/documentation/MCP/Fukuro/transfer references.
- License: MIT, copyright (c) 2026 sechiro; the full upstream notice is retained in [LICENSE](LICENSE).
- Local adaptation version: `1.0.0`. It is a selective English-language synthesis with workspace-specific boundaries, not an upstream release or full mirror.

## Disposition of all twelve skill entrypoints

All source paths below are relative to the pinned repository's `skills/` directory. Only **one** new entrypoint, `vrc-udon-workflow`, is installed.

| Source skill | Disposition | Local authority / reason |
|---|---|---|
| `vrc-udon-core-module` | Adapted | [Module contract](references/module-and-project-contract.md): Builder First where justified, Runtime/Editor split, inputs/outputs, generated versus authored ownership. No mandatory scaffold or reorganization. |
| `vrc-udon-project-docs` | Adapted selectively | [Project-owned information roles](references/module-and-project-contract.md#project-owned-documentation-without-a-documentation-pack), merged into existing records only as authorized. No automatic docs pack, configuration or Editor-code installation. |
| `vrc-udon-fukuro-udon` | Adapted as an opt-in decision | [Optional Fukuro adoption](references/module-and-project-contract.md#optional-fukuro-adoption). No default Manual Sync migration, package install or pickup-setting override. |
| `vrc-udon-knowhow-transfer` | Adapted | [Knowledge transfer](references/module-and-project-contract.md#knowledge-transfer): temporary external references versus adopted project facts; optional import/export, provenance and redistribution boundaries. |
| `vrc-udon-unity-mcp` | Adapted | [Editor workflow](references/editor-and-editing.md): Editor-only assistance and reproducibility, current mounted tools, exact instance pinning and workspace safety. No foreign configuration template. |
| `codex-edit-stability-windows` | Adapted selectively | [Windows editing](references/editor-and-editing.md#windows-text-editing): encoding/BOM preservation, small current-content patches, avoid shell expansion hazards. Existing `edit`/`write`/syntax-aware tools replace upstream `apply_patch` assumptions. |
| `vrc-udon-networking-rules` | Routed; not installed | `unity-vrc-udon-sharp` networking/ownership/late-joiner references. Design decisions can live in existing project specs without duplicating generic rules or requiring `NETWORKING_RULES.md`. |
| `vrc-udon-persistence-sync` | Routed; not installed | `unity-vrc-udon-sharp` persistence and context-preservation guidance, including local/synced/PlayerData/PlayerObject selection and restoration design. |
| `vrc-udon-ui-menu` | Routed; not installed | `unity-vrc-udon-sharp` UI/events and `unity-vrc-world-sdk-3` components. No duplicate menu framework or new pickup/collider permissions. |
| `vrc-udon-heavy-runtime` | Routed; not installed | `unity-vrc-udon-sharp` performance guidance already covers rebuild/replay/reset/cancel and bounded work. |
| `vrc-udon-data-lists` | Routed; not installed | `unity-vrc-udon-sharp` constraints/API selection. Do not import a competing rule that forbids DataLists unless explicitly named; use the existing authoritative collection guidance. |
| `vscode-file-links` | Omitted | Codex/VS Code-only absolute `@` path formatting conflicts with a portable harness workflow; no file-link policy is installed. |

## Cross-cutting guide

`guides/texture-and-vram-optimization.md` contributes [texture-decisions.md](references/texture-decisions.md): delivery size versus GPU residency, format-quality distinctions, actual simultaneous residency, CPU-readable copies, World Space mipmap decisions and dated streaming/DPID provenance.

Boundaries and corrections:

- The World SDK skill remains authoritative for overall performance, platform recommendations, texture overrides, scene components, lighting, build validation and upload. Its local community-tooling additions are untouched.
- The Udon skill remains authoritative for download APIs, request limits, lifetime/cleanup, crossfades, cache implementations and runtime performance. No alternative cleanup implementation or second `Dispose`/`Destroy` recipe is included.
- Upstream nominal RGB24 VRAM/break-even arithmetic is not copied. Unity's directly reviewed 2022.3 format table describes RGB24 conversion to RGBA32 on the GPU; the adaptation explicitly budgets the actual resident format.
- Historical DPID beta/opt-in findings are attributed as upstream research, not asserted as current SDK status. Streaming release facts are dated; no universal memory-savings percentage is promised.
- Upstream `Automatic` import preference does not replace existing project/SDK platform overrides. The adaptation adds tradeoff reasoning rather than another blanket format policy.

## Templates, attribution and deliberate omissions

No upstream assets, executable templates, agent YAML, `.mcp.json` or documentation scaffolds were copied. In particular, the nemurigi-derived `UdonSharpProgramAssetAutoGenerator.cs` and its separate MIT notice were **not** duplicated: program-asset generation routes to the existing Udon skill, which owns its template and attribution. If that code is imported elsewhere in a later task, retain its own required license; this repository's sechiro MIT notice is not a substitute for third-party notices.

The installed files contain adapted guidance covered by the retained sechiro MIT notice. No Unity project, scene, package, global agent configuration or existing niaka skill is changed by this complementary integration.

## Verification boundary

This is documentation/skill integration, not a Unity feature execution. It does not certify Fukuro, DPID settings, Editor scripts, downloaded-image lifetime behavior or any world on a device. Parent integration verification owns skill discovery, reference/link integrity and final conflict checks after both skill updates land. Future Unity work must exercise the actual changed path and meet workspace visual acceptance rules.

## `references/texture-decisions.md`

- [sechiro texture/VRAM guide at the pinned revision](https://github.com/sechiro/VRCUdonSkills-for-Codex/blob/1a19d149b1730cae4dbde9dd5d9a4e4aa50d0c0f/guides/texture-and-vram-optimization.md)
- Unity 2022.3: [supported formats and bpp tables](https://docs.unity3d.com/2022.3/Documentation/Manual/class-TextureImporterOverride.html), [Texture Import Settings](https://docs.unity3d.com/2022.3/Documentation/Manual/class-TextureImporter.html), [Mipmap Streaming](https://docs.unity3d.com/2022.3/Documentation/Manual/TextureStreaming.html)
- Streaming and DPID: [VRChat 2024.4.2 release](https://docs.vrchat.com/docs/vrchat-202442)

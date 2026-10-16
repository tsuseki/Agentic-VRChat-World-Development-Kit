# VRChat skill synchronization — 2026-09-27

## Sources and scope

- niaka3dayo: https://github.com/niaka3dayo/agent-skills-vrc-udon/commit/f6dc6c020a09a930dde92e31e2b593e96fe68235 (`dev`, package/skills 4.1.1).
- Three-way baseline: https://github.com/niaka3dayo/agent-skills-vrc-udon/tree/v2.5.4 (commit `2e84a0635d65590c7f24f1c15788c6248404320a`). Both previous local skills identified as 2.5.4.
- sechiro: https://github.com/sechiro/VRCUdonSkills-for-Codex/commit/1a19d149b1730cae4dbde9dd5d9a4e4aa50d0c0f (`main`). All twelve skill entrypoints considered; selected complementary material adapted, not blindly installed.

## Integration

Updated `../skills/unity-vrc-udon-sharp/` and `../skills/unity-vrc-world-sdk-3/` with a three-way comparison against 2.5.4. No textual merge conflicts. Preserved local AVPro/Unity/Android URL-resolution and preview guidance, layer corrections, community tooling references, and licenses. The local-only community tooling reference remains present.

Workspace/project rules explicitly override upstream examples: no ordinary prop colliders, no unsolicited stations/pickups, requested pickups at 0.1 proximity with AutoHold No, MCP Editor mutation, console checks, reflection probes immediately after lightmap bakes, and scene-reviewer acceptance (since split into layout/style/dressing/final reviewers). Removed automatic installation requirements for the Udon program-asset generator; program-asset wiring still uses the existing project workflow. No hooks were registered and no Unity SDK/packages upgraded.

Added `../skills/vrc-udon-workflow/` for module/Builder ownership, Runtime/Editor boundaries, conditional project specifications, knowledge transfer, optional Fukuro evaluation, compatible MCP/Windows editing practices, and complementary texture residency/delivery decisions. Its `references/provenance.md` records dispositions for all twelve upstream skills. Overlapping Udon/SDK topics route to the existing skills. No imported Codex configuration, doc packs, auto-generator duplicates, or forced package adoption. Retained sechiro's MIT license. Corrected the upstream RGB24 GPU-memory assumption rather than copying its obsolete estimate.

The existing Udon skill links directly to the complementary entrypoint, so it remains reachable even when the running session's skill catalog has not refreshed.

## Observed verification

- Installed inventories: Udon 50 files, World SDK 14 files (including one preserved local-only reference), complementary workflow 6 files.
- Checked 288 relative Markdown file targets across all three skill trees: zero missing targets. This checks target files, not Markdown heading anchors or external URLs.
- Exercised the installed PowerShell validator with temporary C# fixtures: clean runtime code, runtime generic collection usage, and blocked-looking text inside comments/string literals. Clean/masked cases emitted no warnings; the runtime collection case emitted the expected unsupported-runtime advisory. All three exited zero and preserved stdin payload bytes exactly.
- Initial smoke assertion expected the old `BLOCKED` label; updated upstream intentionally emits a generic-collection `WARNING` distinguishing runtime from Editor-evaluated initializers. Corrected the fixture expectation; no validator change was needed.
- `.omp/skills/vrc-udon-workflow/SKILL.md` was not recognized by the already-running session's skill catalog. Direct filesystem reading succeeded. Start a new session to refresh catalog discovery; automatic trigger discovery in a new session has not been exercised.
- No Unity scripts/scenes/assets were changed. No Unity compilation or visual review claimed; C# files here are reference templates, not imported project scripts. The Bash validator was not exercised.

## Backup and repository boundary

Original installed skill files were retained in a temporary local folder (a recovery copy, not a durable Git checkpoint).

At the time the workspace was not a Git repository. No repository was initialized, no project repository was modified, and no commit or push was performed.

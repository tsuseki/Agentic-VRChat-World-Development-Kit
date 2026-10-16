# Editor and Windows editing workflow

Selective adaptation of sechiro's unity-mcp and Windows editing guidance. Mounted tool schemas and workspace rules take precedence over upstream tool names, configuration examples and link conventions.

## MCP is Editor assistance, not a runtime dependency

Use Unity MCP to inspect scenes, prefabs, assets, package state and Builder results, and to execute authorized Editor operations. Do not add runtime dependencies on an MCP server, claim an Editor observation proves VRChat behavior, or treat the MCP transcript as the networking specification.

1. **Resolve the target.** Read `mcpforunity://instances`, select the exact intended `Name@hash` with the mounted instance-selection tool, and inspect current scene/Editor state. Do not rely on a remembered port, active scene or previous session's selection.
2. **Inspect before mutation.** Query hierarchy/components/assets with paging and summaries first. Obtain actual object identities and ownership scope. Reflect unfamiliar Unity APIs; consult current documentation and the installed SDK for version-sensitive behavior.
3. **Use the current harness.** Read each Unity MCP tool's schema/docs as your agent host exposes them before first use, and call the tools through the host. Prefer specialized scene/prefab/component tools; use the Unity MCP `execute_code` tool for scoped Editor operations they do not cover. Do not copy another host's tool names or assume their argument schemas.
4. **Serialize global Editor actions.** Scene loads, refresh/compilation, play-mode changes and bakes need one integration owner when multiple agents/sessions are working. Worktrees do not isolate the Editor. Parallelize only independently owned objects/assets without conflicting global operations.
5. **Preserve Editor state.** Never patch open scene/asset YAML on disk. Use supported Editor operations and appropriate Undo/dirty handling for interactive authoring; scripted hierarchy changes require `EditorSceneManager.MarkSceneDirty` before saving. Do not save unrelated dirty scenes or discard unsaved user changes.
6. **Compile before use.** After any script change, allow import/compilation to complete, read the console and resolve `error CS` before instantiating changed types or entering Play mode. Consult `unity-vrc-udon-sharp` for Udon compile/program-asset issues; do not introduce a second asset generator.
7. **Inspect and exercise.** Confirm generated objects, wiring and saved state through the Editor; then exercise actual interactions. Use ClientSim/Play mode for what they can prove and VRChat Build & Test for client/network/persistence/platform behavior. Apply the workspace's stage-reviewer gate (`dressing-reviewer` before the bake, `final-reviewer` after it) to visual changes.
8. **Retain reproducibility.** Put repeatable setup in the owned Builder/code and the necessary project-specific decisions in the existing specification. Avoid recording a fragile chain of manual MCP mutations as the only reconstruction method.

### Connection and package changes

The upstream `.mcp.json`/localhost example is intentionally not distributed. This workspace already supplies MCP routes and connection guidance; do not overwrite them, edit global agent settings, or install/upgrade Unity MCP automatically. Diagnose existing connection state and follow workspace recovery instructions first. If configuration or installation is explicitly in scope, verify the actual Unity/package/client versions and use the governing package workflow; make only the authorized project-scoped change. Do not assume the upstream Unity `2022.3.22f1` example is an SDK support guarantee.

## Windows text editing

These safeguards apply to source and documentation, not to permission for filesystem scene edits.

- Discover and read the real file before editing. Keep patches small and anchored to current content; reread after a failed patch or intervening change rather than retrying stale line numbers.
- Use this harness's `edit` for surgical changes and `write` for new files or genuinely required whole-file replacements. Prefer the appropriate syntax-aware edit tool for structural code changes. Do not require upstream `apply_patch` or fall back to shell rewrites when a dedicated edit tool is available.
- Preserve existing encoding, BOM policy and newline conventions unless changing them is part of the task. For new text, use the project convention; do not introduce a BOM accidentally through a Windows shell default.
- Avoid passing Markdown, Japanese text, URLs or C# through expansion-heavy PowerShell here-strings and replacement expressions. Dollar signs, backticks, quotes and backslashes can be interpreted by more than one shell layer. Use structured tool arguments; follow the workspace's Eval/subprocess guidance for genuinely necessary quote-heavy shell commands.
- If an edit produces mojibake, replacement characters, an unexpected BOM or truncated text, stop and restore the affected authored content from a known-good source without overwriting concurrent user changes. Do not repeatedly transcode the whole file hoping to repair it.
- At the task's authorized verification point, inspect the changed output for encoding damage, unresolved template tokens and unintended changes, then exercise the changed path. Compilation proves neither correct text encoding nor correct VRChat behavior. Do not add permanent tests for incidental source wording.

No VS Code-only `@absolute-path` chat-link format is imposed. Use the active harness's path/link conventions and the user's requested output format.

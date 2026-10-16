---
title: Drive the live editor through Unity MCP instead of editing scene YAML; setup pitfalls
topic: unity-editor-scripting-mcp
tags: [Unity MCP, MCP for Unity, uvx, scene YAML, setup, read_console]
summary: Hand-edited .unity YAML needs a reload, gets clobbered when Unity saves and cannot add DLL-based components; use the MCP tools, and note the uvx --offline start failure and fresh-session requirement.
---
**Why:** editing an open scene's YAML by hand (a) needs a manual scene reload, (b) is clobbered when Unity saves its in-memory state, (c) can't add DLL-based components (e.g. `VRCUiShape`). The CoplayDev "MCP for Unity" tools (`manage_gameobject`, `manage_components`, `manage_scene`, `execute_code`, `read_console`) act on the live editor.

**Setup pitfalls:**
- A server entry started with `uvx --offline` can fail to start when a dependency isn't in the local uv cache ("Failed to connect"); run `uvx --from mcpforunityserver==<version> mcp-for-unity` without `--offline`.
- Newly added MCP servers only expose tools in a **fresh agent session**; restart (continuing the conversation if your client supports it).
- The Unity-side bridge must be running (Window → MCP For Unity shows "Session Active").

**Usage idioms:**
- Target GameObjects by instance ID (`search_method: "by_id"`); read components via the `mcpforunity://scene/gameobject/{id}/components` resource.
- Exit play mode before relying on edits — edits made during play revert.
- `read_console`'s type filter has mislabeled ordinary logs as exceptions in some versions; filtered output alone isn't proof of compile errors — read the messages.
- For previews, simulate and render atomically in one call; never save throwaway preview clones into the authored scene.

See also [unity-mcp-routing-busy-and-autostart](unity-mcp-routing-busy-and-autostart.md).

---
title: Unity's official CLI/MCP agent features need Unity 6 — use CoplayDev unity-mcp on VRChat's 2022.3
topic: unity-editor-scripting-mcp
tags: [Unity CLI, MCP, unity-mcp, Unity 2022.3, tooling]
summary: The official Unity CLI's editor features go through com.unity.pipeline, which requires Unity 6000.0+, so it cannot drive VRChat-supported 2022.3 projects; CoplayDev unity-mcp supports 2021.3 through 6.x.
sources: [https://creators.vrchat.com/roadmap, https://creators.vrchat.com/sdk/upgrade/current-unity-version]
---
**When:** Choosing how an agent drives the Unity Editor for a VRChat world.

**Facts (at time of writing):**
- Unity's official CLI (beta) offers `unity eval` (Roslyn C# eval, no domain reload), `unity command`, and a built-in MCP mode, but all editor interaction goes through the `com.unity.pipeline` package, whose published versions (all experimental) require **Unity 6000.0 minimum** per packages.unity.com metadata.
- VRChat worlds are locked to the VRChat-supported Unity 2022.3 LTS, so the official CLI/MCP can't connect.
- CoplayDev unity-mcp ("MCP for Unity") supports 2021.3 → 6.x.

**Rule:** use CoplayDev unity-mcp. Re-evaluate the official CLI only if VRChat moves its supported editor to Unity 6 — reload-free eval and first-party MCP would then be worth a look.

**Status 2026-09-01:** VRChat's roadmap lists "Unity 6 VRChat SDK" as **In progress**; 2022.3.22f1 remains the current supported editor, and VRChat warns that upgrading the editor makes uploads fail to load. Recheck the roadmap before each new world.

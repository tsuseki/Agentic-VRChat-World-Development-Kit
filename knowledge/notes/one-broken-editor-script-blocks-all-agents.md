---
title: One compile error in an Editor script blocks every parallel agent
topic: agent-workflow-verification
tags: [parallel agents, Editor folder, compile error, assembly, ownership]
summary: Unity compiles Assets/Editor as one assembly, so a single error CS there stops all editor tooling project-wide; give each parallel agent exclusive ownership of its own script and never stub someone else's.
---
**Symptom:** While several agents build in parallel in one Unity project, every menu item and every agent's editor tooling stops working for ~20 minutes at a time. Agents report being blocked by compile errors in other agents' files.

**Cause:** `Assets/Editor/` compiles as **one assembly**. One `error CS` in any file there stops the whole assembly building. The natural reaction, stubbing out the broken file so your own work proceeds, clobbers the owner's half-finished edit without them knowing.

**Fix / rule:**
- When fanning out parallel agents over one project, give each **exclusive ownership of its own Editor script** and forbid editing anyone else's.
- When blocked by a foreign compile error, check the file's modification time: if it is the current minute, or the reported error line drifts between reads, someone is actively typing. **Wait; don't stub.**

Related: [parallel-agent-sessions-in-one-unity-editor](parallel-agent-sessions-in-one-unity-editor.md), [play-mode-silently-refuses-on-compile-errors](play-mode-silently-refuses-on-compile-errors.md)

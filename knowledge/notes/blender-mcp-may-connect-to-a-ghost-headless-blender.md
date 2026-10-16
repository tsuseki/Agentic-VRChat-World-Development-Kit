---
title: The Blender MCP bridge can silently talk to a headless or wrong Blender instance
topic: blender-modeling
tags: [blender-mcp, headless, socket, port-9876, background-blender, multi-instance]
summary: The Blender MCP add-on listens on a TCP port inside whichever Blender process bound it first, so an orphaned headless Blender or a second GUI window can capture the bridge and the agent edits a scene the user cannot see.
---
**Symptom:** The agent "connects to Blender" and reads/edits a scene, but nothing changes in the user's open window.

**Cause:** Blender MCP servers are two parts: an add-on that runs a TCP socket server inside Blender (commonly `localhost:9876`), and the stdio MCP server the agent launches, which connects to that port. Tools that launch `blender --background` for one-shot/CLI jobs can leave a hung headless `blender.exe` that keeps squatting the port; later sessions then reach this ghost. With two GUI Blender windows open, the bridge reaches whichever one won the port.

Related facts:
- The MCP server connects and lists tools even when Blender is closed; tool *calls* then fail with connection refused.
- Some add-ons need Blender's "Online Access" preference enabled or the socket silently never starts.
- MCP env/config is read at agent-session start; changes need a fresh session.

**Fix / rule:**
- Detect (Windows PowerShell): `Get-Process blender | select Id,StartTime,MainWindowTitle` (empty title = headless) and `Get-NetTCPConnection -LocalPort 9876 -State Listen` for the owning PID.
- Before killing, confirm the ghost's file is saved and not dirty; then `Stop-Process -Id <pid> -Force` and reopen the `.blend` in the GUI so the add-on binds the port in the user's window.
- For live co-editing keep exactly one GUI Blender open and avoid background/CLI Blender tools during the session. After headless batch runs, check no stray process lingers.

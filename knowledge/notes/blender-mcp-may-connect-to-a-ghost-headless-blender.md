---
title: The Blender MCP bridge can silently talk to a headless or wrong Blender instance
topic: blender-modeling
tags: [blender-mcp, headless, socket, port-9876, background-blender, multi-instance]
summary: The Blender MCP add-on listens on a TCP port inside whichever Blender process bound it first, so an orphaned headless Blender or a second GUI window can capture the bridge; agents work headless only, so kill stray background Blenders after batch runs.
---
**Symptom:** The agent "connects to Blender" and reads/edits a scene, but nothing changes in the user's open window.

**Cause:** Blender MCP servers are two parts: an add-on that runs a TCP socket server inside Blender (commonly `localhost:9876`), and the stdio MCP server the agent launches, which connects to that port. Tools that launch `blender --background` for one-shot/CLI jobs can leave a hung headless `blender.exe` that keeps squatting the port; later sessions then reach this ghost. With two GUI Blender windows open, the bridge reaches whichever one won the port.

Related facts:
- The MCP server connects and lists tools even when Blender is closed; tool *calls* then fail with connection refused.
- Some add-ons need Blender's "Online Access" preference enabled or the socket silently never starts.
- MCP env/config is read at agent-session start; changes need a fresh session.

**Fix / rule:** Agents do not drive the GUI bridge at all: the `blender-modeler` agent is headless only (`blender -b --factory-startup -P script.py` or `execute_blender_code_for_cli`), so this trap matters only when the user explicitly runs a live GUI co-editing session.
- After every headless batch run, check no stray `blender.exe` lingers; kill hung background processes.
- Detect (Windows PowerShell): `Get-Process blender | select Id,StartTime,MainWindowTitle` (empty title = headless) and `Get-NetTCPConnection -LocalPort 9876 -State Listen` for the owning PID.
- Before killing, confirm the ghost's file is saved and not dirty; then `Stop-Process -Id <pid> -Force`. In a user-requested GUI session, have the user reopen the `.blend` so the add-on binds the port in their window, and keep exactly one GUI Blender open.

---
title: Unity MCP: per-call instance routing, busy editors and bridge autostart
topic: unity-editor-scripting-mcp
tags: [Unity MCP, MCP for Unity, unity_instance, timeout, stdio, EditorPrefs, port]
summary: With several Unity editors open pass unity_instance on every MCP call; a tool timeout usually means Unity is busy importing, not disconnected; the stdio bridge auto-starts and cannot be permanently stopped with End Session.
---
Applies to the CoplayDev unity-mcp server ("MCP for Unity").

- **Routing:** `set_active_instance` sets a session default that does not reliably stick; later calls can land in the wrong editor and silently edit the wrong project. Pass `unity_instance` on each call instead (`"MyGame@abc123"`, a hash prefix, or a port number in stdio mode). List instances via the `mcpforunity://instances` resource. Confirm the project before editing by querying `Application.dataPath`.
- **Timeouts:** a tool timeout usually means Unity is **busy**, not disconnected. Check the Unity window title for a progress/import state (a long reimport of a heavy model can block the main thread for ~5 min). Waiting is correct; reconnecting or restarting mid-import causes damage.
- **Interrupted compiles:** `refresh_unity` reporting `recovered_from_disconnect` means the compile was interrupted; treat resulting UdonSharp programs as stale ([udonsharp-stale-program-after-edit](udonsharp-stale-program-after-edit.md)).
- **Autostart in stdio mode is already automatic.** `StdioBridgeHost` is `[InitializeOnLoad]` and retries via an `EditorApplication.update` watchdog until the port binds whenever HTTP transport is off. The "Auto-Start on Editor Load" toggle only affects HTTP transport.
- MCP preferences are **EditorPrefs**, i.e. machine-wide (Windows: `HKCU\Software\Unity Technologies\Unity Editor 5.x`), not per project. A bridge that seems not to have started is usually a discovery miss: `PortManager.GetPortWithFallback()` skips a busy port and writes a per-project port file, so the editor may be on a different port than configured. Force a rebind with `StdioBridgeHost.StartAutoConnect()`.
- **"End Session" is not sticky.** It calls `StdioBridgeHost.Stop()`; the bridge revives on the next recompile, play-mode toggle or editor launch. To keep MCP off, switch the transport or quit Unity.

Related: [verify-which-project-unity-has-open](verify-which-project-unity-has-open.md), [parallel-agent-sessions-in-one-unity-editor](parallel-agent-sessions-in-one-unity-editor.md)

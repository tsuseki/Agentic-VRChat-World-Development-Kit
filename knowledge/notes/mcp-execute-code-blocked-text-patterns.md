---
title: execute_code rejects deletes, process starts and endless loops by text pattern
topic: unity-editor-scripting-mcp
tags: [execute_code, safety check, File.Delete, Process.Start, blocked pattern]
summary: MCP for Unity's execute_code refuses any body containing System.IO.File.Delete, Directory.Delete, FileUtil.DeleteFileOrDirectory, AssetDatabase.DeleteAsset/MoveAssetToTrash, EditorApplication.Exit, Process.Start/Kill, while(true) or for(;;); do those outside the call.
---
**Symptom:** calls came back "Blocked pattern detected" for scratch-file cleanup, running a tool exe, and a polling loop.

**Cause:** a case-insensitive substring check over the code text before compiling (MCP for Unity `ExecuteCode.cs`).

**Fix / rule:** delete files and folders from the shell, assets with the Unity MCP `manage_asset` tool's `delete`
action; run exes from the shell or PowerShell; replace endless loops with bounded loops or an `EditorApplication.update`
job polled across calls. Methods inside a compiled editor script are not scanned, so a project tool may delete its own
generated assets.

**Verify:** the reply is a result, not "Blocked pattern detected".

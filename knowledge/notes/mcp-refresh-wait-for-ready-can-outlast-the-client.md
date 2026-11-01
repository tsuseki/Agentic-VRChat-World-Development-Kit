---
title: refresh_unity with wait_for_ready can block past the client timeout
topic: unity-editor-scripting-mcp
tags: [refresh_unity, compile, timeout, isCompiling]
summary: A refresh_unity call with wait_for_ready true blocked past the client timeout and took the calling kernel with it; request the compile without waiting, then poll isCompiling in short calls and read the console.
---
**Symptom:** after a script change, the refresh-and-compile call never returned and the eval kernel driving the MCP
client had to be killed.

**Fix / rule:** send the Unity MCP `refresh_unity` tool `{"compile": "request", "wait_for_ready": false}`, then poll
`return EditorApplication.isCompiling + " " + EditorApplication.isUpdating;` from separate short `execute_code` calls
until both stay false, then `read_console` for `error CS`. Same shape for `AssetDatabase.ImportAsset(path,
ForceUpdate)`: issue it in one call, check type availability or the asset in later calls.

**Verify:** the new type resolves (or `Shader.Find(...)` returns it) in a later call and the console has no `error CS`.

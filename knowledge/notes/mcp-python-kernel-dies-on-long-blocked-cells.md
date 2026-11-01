---
title: Keep MCP helper code in files: a blocked eval cell can kill the kernel and every definition
topic: unity-editor-scripting-mcp
tags: [eval kernel, Python, recompile, timeout, helpers]
summary: An eval cell that blocks ~30 s on a Unity recompile or MCP reconnect killed the Python kernel and every helper defined in it; keep helpers in a file, re-exec it at the top of each cell, and pass explicit timeouts.
---
**Symptom:** after a recompile, helper functions defined earlier in the session were suddenly undefined.

**Cause:** a cell waiting on the MCP bridge during a recompile or reconnect blocked past the kernel's limit; the kernel
restarted and lost its state.

**Fix / rule:** write helpers (MCP client wrapper, pose tables, capture and diff code) to a file and
`exec(open(path).read())` at the top of each cell; pass a `timeout` to every MCP call; issue the compile or import in one
call and poll readiness in short later calls.

**Verify:** a fresh kernel runs the next cell unchanged.

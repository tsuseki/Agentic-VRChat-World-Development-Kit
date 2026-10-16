---
title: An MCP timeout on a bulk mutation means 'unknown', not 'did not run'
topic: unity-editor-scripting-mcp
tags: [mcp, timeout, execute_code, batching, idempotent, mesh merge]
summary: A bulk Unity edit that exceeds the MCP request window can finish halfway without rollback; query the resulting state, batch small, and make batches resumable.
---
**Symptom:** A single `execute_code` merging 63 groups hit "Request timeout after 30000ms … outcome is unknown". Some groups had both the combined mesh and the source instances — 3.74 M tris where 2.00 M was expected, no error.
**Fix / rule:**
1. Never assume a timeout means nothing ran. Query counts (objects, renderers, triangles) first.
2. Batch under the window (~6 heavy items per call) and loop until the call reports `remaining 0`.
3. Make batches idempotent and resumable with a marker (e.g. rename finished groups `<name>__M`).
4. Re-running a non-idempotent operation over a half-done state hides the damage (it merges the duplicate in). Regenerate from scratch instead.

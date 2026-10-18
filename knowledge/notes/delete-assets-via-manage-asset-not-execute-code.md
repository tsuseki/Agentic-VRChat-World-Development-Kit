---
title: AssetDatabase.DeleteAsset inside an MCP execute_code call can hang and kill the caller; use manage_asset delete
topic: unity-editor-scripting-mcp
tags: [AssetDatabase, DeleteAsset, MoveAssetToTrash, execute_code, manage_asset, hang, MCP]
summary: Deleting assets with AssetDatabase.DeleteAsset inside the Unity MCP execute_code tool hung and killed the calling agent; delete through the Unity MCP manage_asset tool's delete action.
---
**Symptom:** An agent deleted assets with `AssetDatabase.DeleteAsset(path)` inside the Unity MCP `execute_code` tool; the call never returned and the calling session died.

**Cause (likely):** `DeleteAsset` runs an asset-database refresh inside the request, which can block the bridge until the caller times out; the `manage_asset` action handles deletion outside user code. (`AssetDatabase.MoveAssetToTrash` can also trip the server's safety blocklist.)

**Fix / rule:** Delete assets with the Unity MCP `manage_asset` tool's `delete` action, one call per asset or a small batch, and confirm in a later call that the paths are gone. Before deleting an asset the open scene references, read [deleteasset-recreate-nulls-scene-references](deleteasset-recreate-nulls-scene-references.md).

**Verify:** in a later call, `AssetDatabase.LoadMainAssetAtPath(path) == null` for each deleted path and the console shows no import errors.

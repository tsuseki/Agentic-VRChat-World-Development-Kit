---
title: A refused selected-groups render raises a modal dialog that freezes the editor
topic: lighting-baking
tags: [Bakery, selected groups, modal dialog, MCP timeout, unattended bakes]
summary: Bakery's 'Scene geometry/layout changed since last full bake' refusal is a modal DisplayDialog: the editor main thread blocks and every MCP call times out until someone presses Enter.
---
**Symptom:** ~40 s after a scripted Render Selected Groups, every Unity MCP call timed out at 30 s for ~10 minutes.

**Cause:** Bakery refused the selected render ("Bakery error — Scene geometry/layout changed since last full bake. Use
Render button instead.") through a modal `EditorUtility.DisplayDialog`. It also happened in a scene with no Bakery
output of its own (sharing another scene's lightmaps).

**Fix / rule:** run a full Render whenever geometry, layout or atlas settings changed, or the scene has never had its
own full bake. Find a suspected modal with a desktop screenshot (PowerShell `CopyFromScreen`); dismiss it by sending
Enter to the editor's foreground window. Unattended bakes: a PowerShell watcher that polls the editor process's
window titles ("Bakery", "Bakery error", "Lightmap overwrite") and sends Enter.

**Verify:** after dismissing, MCP calls answer again and `bakeInProgress` is false; nothing was baked.

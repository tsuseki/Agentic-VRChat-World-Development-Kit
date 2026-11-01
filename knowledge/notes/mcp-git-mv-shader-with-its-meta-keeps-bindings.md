---
title: Move or rename a shader with git mv of the file and its .meta to keep every material bound
topic: unity-editor-scripting-mcp
tags: [shader, GUID, .meta, git mv, materials]
summary: Materials reference a shader by GUID; moving the .shader with its .meta keeps the GUID, so renaming the Shader "A/B" line too keeps every material binding.
---
**When:** moving a project shader to a shared folder and renaming its menu path (`Shader "A/B"`).

**How:** `git mv` the `.shader` and its `.meta` together (a move without the `.meta` gives the shader a new GUID and
unbinds every material), edit the `Shader "..."` name, refresh, and request a compile.

**Verify:** in a later call, every user material's `material.shader.name` is the new name and
`Shader.Find("<new name>").isSupported` is true; no material fell back to the error shader.

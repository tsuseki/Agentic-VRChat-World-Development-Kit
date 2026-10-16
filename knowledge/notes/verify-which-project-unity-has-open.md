---
title: Confirm which project and scene the running Unity editor has open before editing
topic: unity-editor-scripting-mcp
tags: [Application.dataPath, active scene, multiple projects, LastSceneManagerSetup, MCP]
summary: Library/LastSceneManagerSetup.txt exists in every project and goes stale, and projects can share scene names — query Application.dataPath and the active scene path from the editor first.
---
**Symptom:** You edit files in one project based on "the open scene", but the editor actually had another project open — easy when several projects contain same-named scenes and props.

**Cause:** `Library/LastSceneManagerSetup.txt` records only what *that* project last had open; it is not evidence the project is running now. A hierarchy screenshot names the scene, not the project. Another agent may also have switched project/scene since your last turn.

**Fix / rule:** one call (Unity MCP `execute_code`) before any edit:
```csharp
return "dataPath=" + UnityEngine.Application.dataPath
     + " | scene=" + UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene().path;
```
Do this before any grep-driven guess about which project is in play.

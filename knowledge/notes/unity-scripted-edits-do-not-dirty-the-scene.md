---
title: Scripted reparent/rename edits do not dirty the scene, so saves silently skip them
topic: unity-editor-scripting-mcp
tags: [MarkSceneDirty, SaveScene, isDirty, scripted edits, Bakery reload, revert]
summary: SetParent and rename via script leave scene.isDirty false, so SaveScene returns true without writing; always MarkSceneDirty first and verify on disk.
---
**Symptom:** A scripted hierarchy reorganization (`Transform.SetParent` + `.name` changes via the Unity MCP `execute_code` tool) is "saved" with `EditorSceneManager.SaveOpenScenes()` (returns true), but the `.unity` file never changes, and the next scene reload (e.g. Bakery's post-bake reload) wipes the work.

**Cause:** Scripted transforms/renames without Undo registration do not set the scene's dirty flag. `SaveOpenScenes()`/`SaveScene()` skip non-dirty scenes and still return true. `scene.isDirty == false` means "Unity doesn't know anything changed", not "saved". Creating/destroying objects seems to dirty the scene on its own; reparent/rename are the silent ones.

**Fix / rule:** After scripted scene edits: `EditorSceneManager.MarkSceneDirty(scene)` then `SaveScene(scene)`.

**Useful flip side:** if scripted work goes wrong (e.g. meshes destroyed) and `scene.isDirty` is still false, the file on disk is still good: `EditorSceneManager.OpenScene(path, OpenSceneMode.Single)` is a free undo. Once anything calls `MarkSceneDirty`, that escape hatch is gone, so do risky mesh work before the first dirty.

**Verify:** Check the `.unity` file itself (LastWriteTime, and search it for a renamed object's `m_Name:`), not the SaveScene return value.

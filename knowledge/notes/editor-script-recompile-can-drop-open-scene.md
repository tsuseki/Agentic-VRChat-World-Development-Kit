---
title: An Editor-script recompile can leave Unity on an empty untitled scene — reopen and assert before measuring
topic: unity-editor-scripting-mcp
tags: [domain reload, recompile, empty scene, OpenScene, Bakery, prefab override]
summary: After editing an Editor script, the domain reload may land on an unnamed empty scene where every query returns a plausible lie (0 lights, 0 lightmaps, 0 probes); save first, reopen, and assert scene identity.
---
**Symptom:** After editing a script under `Assets/Editor/`, `GameObject.Find` returns null, `FindObjectsOfType<Light>()` returns 0, `LightmapSettings.lightmaps` is empty, there are 0 `LightProbeGroup`s — it looks like the bake and probes are gone. Screenshots are blank or uniformly white. Sometimes the scene holds only a Bakery temp object (`!ftraceLightmaps`).

**Cause:** The domain reload left the editor on an unnamed empty scene (`name == ""`, `rootCount == 0`) instead of restoring the open scene.

**Fix / rule:**
- Save the scene before editing any Editor script; expect to reopen it.
- After any recompile: `EditorSceneManager.OpenScene(path, OpenSceneMode.Single)` and assert `scene.name` and the expected `rootCount` before measuring. Cross-check `Application.dataPath` if several editors may be running ([verify-which-project-unity-has-open](verify-which-project-unity-has-open.md)).
- Right after `OpenScene`, `LightmapSettings.lightmaps` can read 0 briefly before Bakery's binding lands — re-query before concluding the bake is lost.

**Pitfalls:** setting a prefab **instance's** `localScale` to the value the prefab already has records **no override**, so regenerating the prefab silently resets it. Put size corrections in the importer/prefab source, not on instances.

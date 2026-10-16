---
title: GameObject.Find cannot find what you just disabled
topic: unity-editor-scripting-mcp
tags: [GameObject.Find, inactive, toggle restore, editor script, positive control]
summary: GameObject.Find and transform.Find skip inactive objects, so a disable-then-restore pass silently no-ops and the scene ships with the object off.
---
**Symptom:** A script disables an object (e.g. post-processing for a neutral screenshot), later "restores" it with `GameObject.Find(...)`; the restore logs nothing, the `if (x != null)` guard swallows it, and the scene is saved with the object off.
**Cause:** `GameObject.Find`, path Find, and `transform.Find` on an inactive branch only search active objects.
**Fix / rule:**
- Cache the reference (or full path) at disable time; never re-Find afterwards.
- To locate inactive objects, use `Resources.FindObjectsOfTypeAll<Transform>()` and match by name/path (filter to scene objects; it also returns assets), or walk the scene roots:
```csharp
var sc = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
System.Action<Transform> WALK = null; var found = new List<GameObject>();
WALK = t => { if (t.name == "PostProcessing") found.Add(t.gameObject); foreach (Transform c in t) WALK(c); };
foreach (var r in sc.GetRootGameObjects()) WALK(r.transform);
```
- Prefer `enabled = false` on the component over `SetActive(false)` on the GameObject when the object must stay findable.
- Every toggle-and-restore pass must print a positive control: `found = N (must be >= 1)` and the resulting `activeInHierarchy`. An absent log line is not proof.

**Verify:** Read the restored state back through an inactive-safe lookup, never through `Find`: an audit using `Find` inherits the same blindness and reports the object "missing".

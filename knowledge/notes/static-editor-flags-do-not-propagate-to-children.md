---
title: SetStaticEditorFlags affects one GameObject — iterate the renderers, not prefab roots
topic: lighting-baking
tags: [ContributeGI, static flags, SetStaticEditorFlags, prefab, editor scripting]
summary: GameObjectUtility.SetStaticEditorFlags only flags the object passed; imported prefabs keep renderers on children, so tagging the root silently leaves them out of the bake.
---
**Symptom:** You tag 20+ imported furniture prefabs `ContributeGI` so they cast baked shadows; after baking, no furniture casts any shadow.

**Cause:** `GameObjectUtility.SetStaticEditorFlags(go, ...)` affects **that GameObject only**. The Inspector's "change children too?" prompt is editor UI, not API behaviour. Imported prefabs usually have an empty root with every `MeshRenderer` on a child.

**Fix / rule:** iterate renderers:
```csharp
foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) {
    if (!r.enabled) continue;
    GameObjectUtility.SetStaticEditorFlags(r.gameObject,
        GameObjectUtility.GetStaticEditorFlags(r.gameObject) | StaticEditorFlags.ContributeGI);
}
```

**Verify (before the bake):** count renderers with the flag, split into lightmapped vs probe-lit:
```csharp
foreach (var r in FindObjectsOfType<MeshRenderer>(false)) {
  if ((GameObjectUtility.GetStaticEditorFlags(r.gameObject) & StaticEditorFlags.ContributeGI) == 0) continue; ...
}
```
Expected: lightmapped + probe-lit == every renderer you meant to include. If the count didn't change after tagging, the flag didn't take.

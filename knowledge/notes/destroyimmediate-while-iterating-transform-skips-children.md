---
title: DestroyImmediate inside a foreach over a Transform skips every other child
topic: unity-editor-scripting-mcp
tags: [destroyimmediate, transform, iteration, editor-script, rebuild, duplicates]
summary: Destroying children while enumerating a Transform reindexes the list mid-loop, so half the old set survives and a rebuild stacks duplicates; collect first, destroy after, and assert against a re-query of the scene.
---
**Symptom:** A rebuild script logs "12 placed, 0 overlaps", while a bounds measurement of the same parent finds 16 objects, some at identical positions, some overlapping art.

**Cause:** `Transform`'s enumerator walks by index. `DestroyImmediate` removes the child immediately and shifts later siblings down, so the next `MoveNext()` skips one. Half the old set survives; the new set is added on top, and a self-check that inspects only what it just created reports success.

**Fix / rule:**
```csharp
// WRONG - reindexes mid-iteration
foreach (Transform c in parent)
    if (c.name.StartsWith("Fin_")) Object.DestroyImmediate(c.gameObject);

// RIGHT - collect first, destroy after
var doomed = new List<GameObject>();
foreach (Transform c in parent)
    if (c.name.StartsWith("Fin_")) doomed.Add(c.gameObject);
foreach (var g in doomed) Object.DestroyImmediate(g);
```
- Same applies to `DestroyImmediate` inside `GetComponentsInChildren` loops that can destroy parents.
- **Assert against a re-query of the scene, not your loop counter.** `placed == 12` describes the generator; a fresh `FindObjectsOfType(...)` count describes the scene. Only the second catches a failed purge.

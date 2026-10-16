---
title: Choose furniture prefabs from a rendered contact sheet, not from names
topic: assets-sourcing
tags: [asset pack, prefab selection, style, contact sheet, screenshot]
summary: Pack prefab names say nothing about period or style; render 7–9 candidates in a row at 3/4 view far from the scene and choose by eye before placing anything.
---
**Symptom:** A modern interior gets a button-back Chesterfield and carved Louis-XVI chairs because they were picked by name and triangle count ("couch set", "accent chair 3"). Mixed-period packs do this every time.
**How:**
```csharp
var root = new GameObject("__CONTACT__");
float x = -200f;                                   // far from the real scene
foreach (var n in candidates) {
  var go = (GameObject)PrefabUtility.InstantiatePrefab(Load(n), root.transform);
  go.transform.position = new Vector3(x, -60f, 0f);
  go.transform.rotation = Quaternion.Euler(0, 205, 0);  // 3/4 view reads style best
  foreach (var c in go.GetComponentsInChildren<Collider>(true)) DestroyImmediate(c, true);
  x += 2.8f;
}
// two realtime directionals (key + cool fill), shadows off
```
Shoot a positioned screenshot from in front of the row centre. With the ~60° positioned-capture lens, `halfWidth ≈ dist × 1.026`, so `dist = rowSpan / 2 / 1.026`. Shoot 7–9 items per frame, not 16 (unreadable; the skybox eats the contrast). Delete `__CONTACT__` afterwards.
**Pitfalls:**
- A prop that reads wrong needs different geometry, not a different material; diagnose style clashes from the asset family, never the filename.
- Real examples of misleading pack names: `bookshelf office` was a 30k-tri Victorian mahogany armoire, `dresser 2/3` French-provincial commodes, `plant 5` a salmon-terracotta urn with dried branches.
- **Skybox ambient blows a rig out.** A rig in open world space is lit by `RenderSettings` ambient at full strength (in the real rooms walls occlude it), so prefabs can render as white silhouettes and dimming the rig's lights barely helps. Box the rig in a 5-face dark enclosure (ceiling + 4 walls, ~13 m, matte RGB 0.16) instead of editing `RenderSettings`, which you would then have to restore.
- To find each prefab's front automatically, a per-face **depth-variance ray scan** works: the open/detailed side has the higher depth standard deviation. Flat slab boxes score 0 on every face; read those off the sheet.
- When a reviewer names an object whose description does not match its geometry, trust the description: find the offender by matching the described look to a mesh, not by the name.
- The rig carries realtime lights; tear it down before any bake or light audit.

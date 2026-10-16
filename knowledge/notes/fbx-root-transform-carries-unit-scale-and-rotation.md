---
title: An imported FBX's unit scale and axis rotation live on the prefab root transform
topic: import-fbx-prefabs
tags: [FBX, localScale, unit conversion, prefab root, LOD swap, bounds, placement]
summary: Assigning localScale or rotation absolutely on an instantiated FBX wipes the importer's unit conversion (often x100) and axis fix, and the prop silently becomes about 1 cm tall.
---
**Symptom:** A scripted placement pass places hundreds of props; the instances exist, meshes are valid, triangle counts are right, positions look sane, and every render shows an empty garden. Or: after swapping placed instances for a decimated version, all of them are 1 cm tall and still correctly positioned.

**Cause:** Unity puts an imported FBX's unit-conversion factor (and often a -90 degree X axis fix) on the **model root Transform**, not in the mesh. Roots like `scale 82.43`, `scale (211.3, 211.3, 151.9)` (non-uniform), or `scale (100,100,100), rot (270,0,0)` are normal. `localScale = Vector3.one * s` destroys it. An exporter's claim of "identity root, true metres" is about the file, not what the Unity importer does.

**Fix / rule:** Multiply, never assign:
```csharp
go.transform.SetParent(par, false);   // before scaling, so a scaled parent doesn't re-derive it
go.transform.localScale = src.transform.localScale * s;   // src = loaded prefab asset
```
When swapping an instance for a different asset (e.g. decimated LOD), strip the old root and re-apply the **new** asset's root:
```csharp
float s = instance.localScale.x / oldSrc.transform.localScale.x;
Quaternion yaw = instance.rotation * Quaternion.Inverse(oldSrc.transform.rotation);
newGo.transform.localScale = Vector3.Scale(newSrc.transform.localScale, new Vector3(s,s,s));
newGo.transform.rotation   = yaw * newSrc.transform.rotation;
newGo.transform.position  += bOld.center - bNew.center;   // land on the outgoing object's bounds centre
```

**Verify:** Instantiate the imported prefab and measure `renderer.bounds` before writing placement code. Assert one sample's `bounds.size` is in metres; a cubic `(0.02, 0.02, 0.02)` on a non-cubic prop is the tell. For yaw-only placement, `bounds.size.y` should equal natural height per unit root scale times `localScale.y` (0 % error when right, ~99 % when wrong). Do not use "height < 0.55 x footprint means it fell over" on rosette-shaped plants; they false-positive.

Related: [compose-fbx-root-rotation-never-assign](compose-fbx-root-rotation-never-assign.md).

---
title: Assigning rotation on an FBX prefab instance wipes its Z-up correction
topic: import-fbx-prefabs
tags: [fbx, z-up, rotation, scripted-placement, blender-export, prefab-root]
summary: Z-up FBX prefabs carry a -90 degree X rotation on their root, so a scripted placement that assigns Quaternion.Euler(0, yaw, 0) lays every prop on its side; compose the yaw with the source rotation instead.
---
**Symptom:** After a scripted placement pass, props are present, the right size and seated on the surface, but lying on their side. From a low camera a planting bed just reads as "a bit sparse". Caught by a plant measuring 0.42 m tall and 1.25 m deep.

**Cause:** A Z-up FBX (Blender exports, most plant/prop packs) imports with a -90 degree X rotation (e.g. `(270, 0, 0)`) on the model root Transform. `go.transform.rotation = Quaternion.Euler(0, yaw, 0)` destroys it. Unit scale correction lives on the root `localScale` the same way.

**Fix / rule:** compose, never assign. Safe pattern for any scripted FBX placement:
```csharp
go.transform.SetParent(parent, false);
go.transform.localScale = src.transform.localScale * s;
go.transform.rotation   = Quaternion.Euler(0, yaw, 0) * src.transform.rotation; // src = prefab asset
// then position by measured renderer bounds
```

**Verify:** For anything that should stand upright, assert `bounds.size.y > 0.55 * max(size.x, size.z)` and print the failure count in the pass itself. A few genuinely flat items (rosette plants) is normal; most failing means a wiped rotation.

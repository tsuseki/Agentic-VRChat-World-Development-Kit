---
title: Surface occupancy scans must exclude rails, structure and wall art
topic: placement-layout-design
tags: [occupancy, shelf, dressing, bounds, false positive]
summary: A 'this surface is full' scan counts shelf lips and pictures hanging behind as occupants, so genuinely empty surfaces get skipped.
---
**Symptom:** Filling bare shelf boards, some boards report `largest gap = 0.00 m` and are skipped as full, but they are empty.

**Cause:** Geometry near the surface that is not sitting on it: a 50 mm shelf lip whose z-span covers the whole bay, and a 1.13 m picture on the wall behind whose bounds reach into the board's z-range and whose `min.y` falls inside the occupancy window.

**Fix / rule:** Filter occupants:
```csharp
if(n.StartsWith("Shelf_Board")||n.StartsWith("Shelf_Up")||n.StartsWith("Shelf_Rail")) continue; // the shelf itself
bool art=false; var pp=r.transform; while(pp!=null){ if(pp.name=="ART"){art=true;break;} pp=pp.parent; }
if(art) continue;                       // wall art group
if(ob.size.z > zSpan*0.85f) continue;   // spans the whole bay -> structure, not a prop
if(ob.size.y > bayHeight)   continue;   // taller than this bay's measured opening (0.55 m here) -> not sitting here
```

**Verify:** A zero-gap result is a red flag, not an answer. Print the occupant list before believing it.

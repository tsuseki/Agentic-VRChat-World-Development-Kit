---
title: Scripted free-spot searches: exclude your own subtree and test renderer bounds, not physics
topic: placement-layout-design
tags: [placement, grid search, IsChildOf, CheckSphere, colliders, bounds]
summary: A "find a free spot" grid search silently fails when the moved object matches its own name filter through child transforms, and passes through props when it relies on Physics.CheckSphere in a world where props have no colliders.
---
**Symptom:** Relocating a plant, the search returns a clean `NO SPOT FOUND` with a plausible rejection histogram; after one fix, it drops the plant 0.6 m inside another plant.

**Cause 1 — self-match:** a "no other `plant_17*` within 6 m" rule that only skips the root matches the prefab's own child transforms (distance 0), so every cell fails:
```csharp
if (t == p) continue;                       // WRONG - only excludes the root
if (t == p || t.IsChildOf(p)) continue;     // RIGHT
```

**Cause 2 — collider blindness:** decorative props deliberately have no colliders, so `Physics.CheckSphere` / `Raycast` report "clear". Build occupancy from renderer AABBs; keep physics only for floor height, and only where the floor collider is the visible surface (a separate flat proxy needs the visible mesh, see seat-props-on-visible-floor-not-collider-proxy):
```csharp
var occ = new List<Bounds>();
foreach (var r in FindObjectsOfType<MeshRenderer>()) {
  if (r.transform.IsChildOf(p)) continue;
  var b = r.bounds;
  if (b.max.y < 0.10f || b.min.y > 2.00f) continue;   // body-height band
  if (b.size.x > 8f && b.size.z > 8f) continue;       // ignore slabs
  occ.Add(b);
}
var cand = new Bounds(new Vector3(x, 1.02f, z), new Vector3(w + 0.14f, 2.0f, d + 0.14f));
bool blocked = occ.Any(b => b.Intersects(cand));
```

**Verify:** after the move, run an explicit, independently written AABB overlap pass and require 0 — if the search constraint and the verification share code, a bug hides itself. Note `Renderer.bounds` inflates for rotated props: [renderer-bounds-inflate-with-rotation](renderer-bounds-inflate-with-rotation.md).

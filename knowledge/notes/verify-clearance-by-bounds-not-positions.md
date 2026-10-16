---
title: Verify clearance with renderer bounds, never transform positions
topic: agent-workflow-verification
tags: [bounds, clearance, overlap, pivot, verification, text]
summary: A transform position is an anchor, not an extent; a position difference reported 0.12 m clearance while the renderer bounds overlapped by 1.6 cm.
---
**Symptom:** A text-overlap fix was "verified" as 0.12 m clearance from transform positions; the reviewer found the same overlap. By `Renderer.bounds` the labels overlapped 1.6 cm in Y and fully in Z.

**Cause:** For TextMesh the position is the anchor of a string whose size depends on `characterSize` and glyphs; for a mesh it's wherever the pivot sits. Same false pass for props seated by pivot, art hung by anchor, panels spaced by position.

**Fix / rule:** never report a clearance derived from `transform.position`. Use `Renderer.bounds` (or bounds encapsulated over `GetComponentsInChildren`), test `Intersects` and print the gap on **every** axis:
```csharp
var a = A.GetComponent<Renderer>().bounds;
var b = B.GetComponent<Renderer>().bounds;
bool hit = a.Intersects(b);
float gapY = Mathf.Max(b.min.y - a.max.y, a.min.y - b.max.y);   // < 0 == overlap
```
The first fix moved Y while Z stayed fully overlapped.

**Verify:** after the real fix the same objects read gap 0.061 m and `Intersects == false`.

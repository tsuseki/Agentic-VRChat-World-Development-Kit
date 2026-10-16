---
title: Detect emissive strips buried inside other geometry
topic: lighting-baking
tags: [emission, buried emitter, bounds containment, glow material, albedo]
summary: An emissive strip fully enclosed in another mesh contributes nothing and looks like a deliberate design choice; test emissive bounds for containment.
---
**Symptom:** None, which is the problem. Glow strips around a pool podium were authored 0.10 m tall entirely inside 0.60 m slabs: zero pixels visible, zero light contributed, and four review passes never flagged it, because a missing glow looks like a designer choosing not to have one. A distance-to-nearest-Light sweep cannot see it either, since a strip emitter needs no Light.

**Fix / rule:** In the pre-bake emissive sweep, also test whether each emissive renderer's AABB lies fully inside another renderer's AABB:
```csharp
if (other.bounds.Contains(r.bounds.min) && other.bounds.Contains(r.bounds.max)) Report(r, other);
```
When an emitter is exposed, check its **albedo** too: a near-white base (0.62/0.74/0.75) reads as white plastic rather than light. Glow materials want a near-black albedo (~0.02) and do their work through `_EmissionColor`.

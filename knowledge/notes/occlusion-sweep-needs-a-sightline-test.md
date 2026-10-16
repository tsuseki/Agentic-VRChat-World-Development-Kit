---
title: A "what blocks this view" sweep must test the sightline and exclude ceiling and room-spanning objects
topic: placement-layout-design
tags: [occlusion, sweep, Linecast, sightline, bulk edit, undo]
summary: Written as an XZ bounding-band test, an occluder sweep shoves corridor-length ceiling lights and the very downlight that lights the target; use a linecast, a height cut and a size cut, and log deltas.
---
**Symptom:** A plant hides a door nameplate. A sweep "move everything in front of the door sideways" moves 11 objects; only 4 (plants) were right. A corridor-spanning ceiling light (40 m wide) jumped +20 m with all its downlights, and the downlights centred above the doors moved off-centre.

**Cause:** The test was a bounding band — "shares an X range and is in front" — which isn't the occlusion question.
```csharp
bool xOverlap = b.max.x > zone.x0 && b.min.x < zone.x1;
bool inFront  = b.max.z > zFront;
```

**Fix / rule — three cheap guards:**
1. **Test the sightline:** `Physics.Linecast` from eye height to the target centre, or a depth test against the target plane. (Note: decorative props without colliders need a renderer-bounds ray test instead.)
2. **Exclude by height:** `if (b.min.y > eyeY + 0.6f) continue;` removes ceiling fixtures.
3. **Exclude room-spanning objects:** `if (b.size.x > zoneWidth * 3f) continue;` — that's architecture, not clutter.

**Verify:** log every delta (`moved {dx:+0.00;-0.00} m`) and read them before saving; exact logged deltas make the sweep reversible. Any bulk predicate over a whole scene needs a positive control and an exclusion list *before* it runs.

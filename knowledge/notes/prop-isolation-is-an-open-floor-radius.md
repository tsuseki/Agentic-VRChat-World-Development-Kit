---
title: Measure "orphaned prop" as open-floor radius, not neighbour distance
topic: placement-layout-design
tags: [set-dressing, isolation, raycast, layout, metrics]
summary: Whether a prop looks orphaned is a free-space property; cast rays outward from the prop and rank by mean clear distance instead of comparing centre or edge distances to neighbours.
---
**Symptom:** Reviewer: "a single small potted plant sits alone in the middle of a large empty floor." Distance metrics can't find it.

**Cause:** Centre-to-centre distance flagged 7 innocents (plants beside a large object score badly because half the neighbour's size counts as separation). Edge distance said nobody was isolated (worst 1.68 m) - it can't see that the one neighbour is the only thing within 8 m. Neither found the actual plant.

**Fix / rule:** From the prop centre at ~0.45 m height, cast 24 rays outward and record min and mean hit distance:
```csharp
Vector3 o = new Vector3(pb.center.x, pb.min.y + 0.45f, pb.center.z);
for (int i = 0; i < 24; i++) {
    float a = i * Mathf.PI * 2f / 24f;
    Vector3 d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
    float dist = 8f;
    if (Physics.Raycast(o + d * 0.35f, d, out var h, 8f)) dist = h.distance + 0.35f;
    // accumulate min / mean
}
```
The offender: min 2.10 m, mean 7.21 m. A dressed prop reads low mean; an orphaned one reads high mean regardless of min.

**Pitfall:** Exclude outdoor sets before ranking (garden/terrace pots legitimately sit in the open, mean 7-8 m). Filter by room or "has a ceiling above" first.

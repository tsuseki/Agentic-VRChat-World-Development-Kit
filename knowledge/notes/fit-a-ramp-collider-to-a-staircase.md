---
title: Fit one rotated ramp box to a staircase from tread noses
topic: colliders-physics
tags: [stairs, ramp, BoxCollider, raycast, tread]
summary: Raycast the stair run, fit a plane through the tread noses lifted so nothing pokes through, and end the ramp where the plane meets each landing.
---
**When:** replacing per-tread or mesh collision on stairs with one smooth rotated box (measured examples: 23°, 30°, 32° ramps).

**How:**
1. Raycast the run every 0.05 m and split it into constant-height runs (treads).
2. Take each tread's **nose** — the sample adjacent to the drop.
3. Slope = first nose → last nose.
4. Intercept `b = max(y_i - slope * z_i)` so no nose pokes through the plane.
5. End the ramp where the plane meets each **landing height**, not at the landing edge. Anchoring at the edges makes the line dip under the last nose and leaves a ~0.2 m lip at both ends.

**Pitfalls:** a planar ramp always floats up to one riser above a tread — that is expected, not a bug. Keep the visible treads; the ramp box floats over them. Porch steps can get the same treatment (one rotated box, e.g. 25°).

---
title: Verify world collision with physics sweeps and a capsule flood-fill, never screenshots
topic: colliders-physics
tags: [collider, verification, CheckCapsule, OverlapCapsule, flood-fill, raycast]
summary: Colliders render nothing, so prove walkability with a capsule-grid flood fill diffed before/after and name every lost cell with OverlapCapsule.
---
**When:** after any collider rework (box replacement, deleting MeshColliders, adding ramps), or to check a room is sealed.

**How:**
- **Grid coverage:** cast down a grid over the floor. Filter hits to the ground colliders by name — a plain `Physics.Raycast` from above hits the **ceiling** first and reports "no floor anywhere".
- **Reachability flood:** sample `Physics.CheckCapsule(y 0.35 → 1.55, r = 0.2)` on a 0.5 m grid, flood-fill from street/spawn seed points, and diff the reachable set before vs after the change.
- **Multi-level areas:** per 0.5 m column `RaycastAll` downward, keep every up-facing surface where a 0.2 m capsule fits, then 3D flood-fill with a 0.5 m step-up limit.
- **Name the blocker:** run `Physics.OverlapCapsule` on each newly lost cell.
- **Containment:** a 16-ray fan at chest height from inside an enclosure, or a 0.1 m 3D flood from the interior (expect 0 leaks, 0 protrusion past the visible mesh).
- **Snag sweep:** `OverlapCapsule` along walk paths.
- To probe visible geometry that has no collider, temporarily add `MeshCollider`s to it (with the real collider root disabled), scan, then destroy them. Inward-facing shells (e.g. a roof) only register from the side their faces point to.

**Pitfalls:**
- Hollow facade buildings dominate "reachable lost" once they become solid boxes. Classify each lost cell against the new box footprints **inflated by the capsule radius**, or you chase phantom losses.
- Don't reason about openings from mesh vertices: vertical bars have no vertices at mid-height, so a vertex histogram shows gaps that don't exist. A/B the real collider instead.
- After rebuilding meshes, MeshColliders can keep stale zero-size bounds in edit mode; reassign (`mc.sharedMesh = null; mc.sharedMesh = m;`) before any raycast tooling.
- Check adjacent solid boxes for newly opened player-width slots (≥ 0.45 m gap with ≥ 0.3 m overlap on the other axis).
Related: [clientsim-scripted-walkability-verification](clientsim-scripted-walkability-verification.md), [physics-synctransforms-before-reading-collider-bounds](physics-synctransforms-before-reading-collider-bounds.md).

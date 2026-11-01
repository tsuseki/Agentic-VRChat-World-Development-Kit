---
title: Multi-stem trees read as an X on screen unless exactly two planar stems share one vertical plane
topic: blender-modeling
tags: [trees, multi-stem, grove, silhouette, stem crossing, merge, acceptance ring, positive control]
summary: A mesh with no bark clash can still show one stem crossing another on screen; two stems in one vertical plane whose merged continuations stay in that plane never cross from any eye, three stems from separate feet always cross from some direction, and the acceptance test is an all-round eye-height ring plus the real in-world cameras, never one set camera.
---
**Symptom:** A multi-stem grove tree with 0 bark clashes in 3D read as one trunk passing through another ("an X") from the in-world cameras. A three-stem version tuned to its vignette camera passed only inside a 3° yaw window: 24 stem crossings over 112 eye-height views, 1 at a world camera, 0 at the tuned camera.

**Cause:**
- Three stems from separate feet always overlap in projection from some azimuth.
- The fork merge continues each stem into its best-aligned child. A limb wave can make a side limb the best-aligned one, so the stem's continuation swings sideways across its neighbour (one seed: 23 crossings, all stem 0 × stem 1).

**Fix / rule:**
- Use exactly two stems in one vertical plane, each a planar curve, with continuations that stay in that plane. The picture of a plane seen from any eye outside it is a projective image of that plane, so the two stems never cross on screen. Builder: `stem_plane=dict(az=…)` (stems evenly round from `az`, no azimuth jitter, no sideways noise) plus level-0 `plane_mid=True` with an odd whorl and `fan_jitter` 0 (the middle limb grows in the stem's plane at the steeper `mid_ang`, so the merge prefers it).
- `fan=<deg>` opens off-centre stems' whorls away from the tree centre, so no limb heads back over the centre.
- Accept on an all-round ring: 36 azimuths × 8, 12 and 20 m at eye 1.3 m, plus every real in-world camera (cameras converted into the tree's frame). Never accept on one set camera.
- Seed scans of the fix: 4 of 4 valid seeds 0 crossings over 112 views.

**Verify:** `bark_clash.py` `silhouettes(bm, az_step=10, dists=(8, 12, 20), views=…)` → 0 stem-axis crossings, plus a by-eye look at the in-world frames.

**Pitfalls:**
- Run every new metric on the version the reviewer flagged first (positive control) and state what it misses. The axis-crossing metric does not flag a stem rising from behind another: their projected axes never cross (an overlap, not an X); the flagged version scored 0 at one camera while its screen gap was tiny. Review in-world frames by eye too.

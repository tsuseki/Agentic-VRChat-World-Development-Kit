---
title: Keep props clear of tree trunks and their visible roots
topic: placement-layout-design
tags: [trees, trunk, CapsuleCollider, props, clearance, sweep]
summary: Sweep every prop under 3.6 m against all trunk capsules within 12 m and flag gaps under 0.5 m; trunk capsules do not cover prop roots or flared bases, so placement keeps at least 1.0 m from the trunk axis.
---

**Symptom.** An outdoor shower had been placed straight through a pandanus trunk; nobody noticed from the wide shots.

**Cause.** Placement avoided trunk colliders only, and the trunk capsule (radius 0.45 m) doesn't cover the visible prop roots or a flared base. Wide eye-height shots hide the clash behind foliage.

**Fix / rule.**
- Placement: spot searches keep ≥ 1.0 m from every trunk axis.
- Review sweep: for every renderer under 3.6 m tall, every trunk `CapsuleCollider` within 12 m; sample heights 0.05 m to min(height, 2.6 m) in 0.25 m steps; take `ClosestPoint` on the capsule and the 2-D gap from the prop's box; flag gaps under 0.5 m. Skip ropes or cables meant to touch a trunk (hammock lines).

**Verify.** The moved shower measured 1.34 m from the trunk axis; a re-sweep over about 2,800 capsules flagged nothing new.

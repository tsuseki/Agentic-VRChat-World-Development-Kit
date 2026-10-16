---
title: When a marking exists twice, keep the one the gameplay trigger sits on
topic: placement-layout-design
tags: [duplicate, ground marking, trigger, checkpoint, shader-drawn, visual review]
summary: Between two duplicate markings, the canonical one is where the trigger/checkpoint/spawn is — move the better-looking marking onto that anchor rather than deleting the ugly one.
---
**Symptom:** A start/finish line exists twice, 6 m apart: an ugly flat-white mesh decal and a handsome shader-drawn checker band. A visual reviewer recommends deleting the ugly decal.

**Cause:** The lap-timing trigger sits on the **ugly** one. Deleting it would put the visible line 6 m from where timing fires. A visual reviewer cannot see trigger volumes, so it ranks duplicates on looks alone.

**Fix / rule:**
- Before removing either duplicate, find what gives it meaning — trigger collider, checkpoint, spawn point, respawn volume — and move geometry to match it. Here: move the shader band's world-position property onto the trigger's X, retire the decal.
- Treat "delete X, keep Y" from a visual review as a claim about appearance, not correctness.
- Shader-painted markings hide in **material properties** (world-position properties on a terrain/splat shader), not the hierarchy — no GameObject search finds them. Inspect the shader's properties when a marking has no obvious owner.

**Pitfalls:** hiding a shadow-casting decal leaves its **baked shadow** on the ground until the next rebake — that's not the fix failing.

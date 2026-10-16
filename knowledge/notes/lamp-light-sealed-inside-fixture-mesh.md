---
title: A baked light placed inside a lamp mesh's bulb lights nothing
topic: lighting-baking
tags: [lamp, point light, occlusion, bulb, raycast, baked light]
summary: Asset-pack lamps are often one solid mesh with a closed bulb, so a light placed "in the bulb" is sealed in a cavity and contributes nothing; find free volume with a ray sweep and use several lights there.
---
**Symptom (not "too dim"):** a glowing shade over a **completely unlit** tabletop (no pool, no falloff); the lamp's own base unlit; raising point-light intensity changes nothing; all visible light is a flat directionless wash from the shade's emissive surface. Lamps in different spots look inconsistent because each depends entirely on bounce.

**Cause:** The baker traces the lamp mesh as an occluder; the light sits inside a sealed cavity a few cm across.

**Fix / rule:**
- **Diagnose with a ray sweep, not by eye:** Möller–Trumbore from the light position against the lamp's own mesh over ~400 Fibonacci-sphere directions; report the fraction of the downward hemisphere that escapes. **Always include a control point in open air** — a buggy test can report "100% blocked" everywhere.
- Sweep candidate positions; the axis may be solid from table to bulb (0% escape at every height). Typical free volume: the annulus between neck and shade inner wall.
- Fix used: **four symmetric point lights** in that annulus (~0.10 m off-axis, just above the shade's bottom rim), intensity split four ways, **shadow casting left on** so the base keeps its contact shadow. Four rather than one so the pool isn't lopsided.
- Don't just turn off the mesh's shadow casting — it loses the base's contact shadow and leaks light through the base.
- Don't treat it as a balance problem between lamps with fill lights or hotter shade materials.

**Verify:** check for enclosure **before** touching intensity, colour or fill lights; confirm the pool appears in a render.

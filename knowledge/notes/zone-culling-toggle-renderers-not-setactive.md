---
title: Zone culling: toggle Renderer.enabled per area, never SetActive the area root
topic: performance
tags: [culling, zones, UdonSharp, Renderer.enabled, SetActive, networking]
summary: A local U# script that box-tests the player against area footprints and toggles only renderers and lights keeps synced game logic alive and halved worst-case visible tris.
---
**When:** a world made of separate areas (islands, floors, rooms far apart) whose combined triangles exceed the budget but any single area fits.

**How:**
- One local behaviour (sync `None`) tests the local player's XZ against each area's box every frame; on change, toggle `Renderer.enabled` / `Light.enabled` for the area left and the area entered (first run sweeps all).
- Cache only renderers/lights **already enabled at Start**, so deliberately disabled ones (inactive button states, FX) stay off.
- Fallback when the player is in no box: **keep the current zone**, not "show all" (that is a full-scene spike). Ignore Y if no area is above another; a falling player still maps somewhere.
- Measured: 3.30M scene tris → worst visible 1.67M; ~4.5k renderers + ~200 lights cached.

**Pitfalls:**
- Never `SetActive(false)` an area root that contains synced UdonBehaviours (games, locks, managers): disabled objects stop receiving network events and break on late deserialization. Renderer-level toggling leaves behaviours, colliders and stations alive.
- Auditing "is each renderer inside its zone": `renderer.transform.position` is (0,0,0) for meshes authored in world coordinates (floors, shells, combined chunks). Use `renderer.bounds`, and skip renderers that are inactive or have zero-size bounds (they report degenerate bounds at the origin).
- Static batching inflates per-renderer tri counts in play mode; count in edit mode.

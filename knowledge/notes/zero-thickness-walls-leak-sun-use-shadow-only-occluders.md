---
title: Single-face walls leak sunlight; add thick ShadowsOnly occluders
topic: lighting-baking
tags: [shadows, single-sided, TwoSided, ShadowsOnly, light leak, interior]
summary: One-sided faces cast no shadow from behind, and even TwoSided zero-thickness walls leak a bright band at wall/ceiling seams; re-enable the blockout boxes as ShadowsOnly occluders.
---
**Symptom:** In an interior built from single-face meshes, sun leaks through ceilings as bright stripes. After setting TwoSided, a bright "hole"-looking band still runs along the top of interior walls.

**Cause:** One-sided faces don't cast shadows from behind. With `TwoSided`, the remaining leak is shadow-map aliasing at the grazing seam of zero-thickness faces; lowering the light's shadow bias / normal bias does **not** cure it.

**Fix / rule:**
1. `shadowCastingMode = TwoSided` on every single-face environment renderer.
2. Re-activate the original thick blockout boxes as occluders: `SetActive(true)`, `shadowCastingMode = ShadowsOnly`, disable their colliders.
3. Only do this for **structural** boxes (floors, ceilings, walls). Skip non-structural blockout (stage, bars, furniture) or you get phantom shadows.

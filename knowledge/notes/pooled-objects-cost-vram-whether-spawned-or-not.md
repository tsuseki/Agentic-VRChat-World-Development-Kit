---
title: Udon cannot instantiate prefabs: every pooled object's textures load whether used or not
topic: performance
tags: [pool, VRAM, instantiate, vehicles, submission spec, triangle budget]
summary: Pools live in the scene permanently, so unique models drive VRAM (20 cars at 4K ≈ 1.3 GB, at 2K ≈ 320 MB) while duplicates are nearly free; set submission caps and start pool members hidden.
---
**Rules:**
- Udon can't instantiate arbitrary prefabs at runtime, so every pooled object sits in the scene and its textures load regardless. 20 vehicles with 4K textures ≈ 1.3 GB VRAM; at 2K ≈ 320 MB. Publish a submission spec (triangle + texture caps) **before** collecting user-made content.
- Duplicates of the same model are nearly free: meshes and textures are shared, so the 40th clone costs no extra VRAM or download. A rack of identical house vehicles is the cheap way to seat people without their own.
- Every pooled object needs a physical home slot (its respawn target), but don't show them all: ~20 detailed cars parked ≈ 2M tris. Author them in their bays, start them hidden, let the selection panel (with rendered thumbnails) spawn them. Empty bays with signage read fine.
- Vehicle prefabs often contain more than the vehicle (race system, cameras, UI at the origin), so their bounds span the map — see [seat-objects-by-downward-raycast-not-bounds](seat-objects-by-downward-raycast-not-bounds.md).

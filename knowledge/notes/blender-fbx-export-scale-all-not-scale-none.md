---
title: Blender FBX export with FBX_SCALE_NONE can import into Unity at 1/100
topic: import-fbx-prefabs
tags: [Blender, FBX, export, scale, apply_scale_options, Z-up]
summary: Use apply_scale_options=FBX_SCALE_ALL (copy a known-good sibling export call verbatim); FBX_SCALE_NONE looked correct in Blender but imported at exactly 1/100.
---
**Symptom:** A new Blender exporter reports correct metres (bbox z 0..2.55) but Unity imports mesh bounds of (0.006, 0.006, 0.0255) — exactly 1/100 — with `useFileScale=True`, `globalScale=1`, same importer settings as a working sibling.

**Cause:** The new script used `apply_scale_options='FBX_SCALE_NONE'`. `FBX_SCALE_ALL` bakes the unit scale into the file so Unity reads it 1:1. The difference is invisible in Blender's own report.

**Fix / rule:** when a sibling exporter already produces correct assets, copy its export call verbatim instead of writing a plausible new one.

**Pitfalls:** this exporter ran without `bake_space_transform`, so its Z-up model imported with an X=270 stand-up correction on the root: compose yaw onto it (`Euler(0, yaw, 0) * src.rotation`, i.e. `Euler(270, yaw, 0)`), never assign `Euler(0, yaw, 0)`. See [compose-fbx-root-rotation-never-assign](compose-fbx-root-rotation-never-assign.md). With the full flag set in [blender-fbx-export-and-modeling-recipes](blender-fbx-export-and-modeling-recipes.md) (`bake_space_transform=True`) the root arrives unrotated.

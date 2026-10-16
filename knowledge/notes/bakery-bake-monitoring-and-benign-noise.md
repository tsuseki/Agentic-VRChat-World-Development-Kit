---
title: Monitoring a Bakery bake: benign fallback lines, red-herring exceptions, and cancel recovery
topic: lighting-baking
tags: [Bakery, ftracelog, OptiX, monitoring, cancel, bindings, console noise]
summary: The non-RTX → OptiX6 → OptiX9 fallback chain in the log is normal; poll bakeInProgress instead of grepping verbose logs, and know that a cancelled bake can persist empty bindings.
---
**Rules:**
- Log lines `Non-RTX lightmapper failed - trying RTX OptiX6 version` → `... trying RTX OptiX9 version` followed by a normal render are **not** errors; only treat it as a failure if the last tracer also fails (see [bakery-tracer-choice-depends-on-gpu-and-driver](bakery-tracer-choice-depends-on-gpu-and-driver.md)).
- Bakery's own log `Assets/Editor/x64/Bakery/.ftracelog.txt` is far more informative than Editor.log.
- Don't grep Editor.log for `ftBuildGraphics` — at verbose log level it appears in every stack frame. Poll static `ftRenderLightmap.bakeInProgress` / `progressBarText` across separate calls; watch group `.hdr` mtimes and ftrace process count; grep only new log lines for `Sharing violation|IOException|OutOfMemory|ftrace error|Reloading assemblies`.
- Installing Bakery reimports every model (`ftModelPostProcessor`) and can flood the console with `ArgumentNullException ... unityObject` from VRChat's serializer on UdonSharp prefabs — benign import noise, not a compile error. The import also kills any running bake.
- `RenderButton` has no re-entry guard: check `bakeInProgress` before launching, or two exports fight over `%TEMP%\frender` files and wedge with IOException. Never launch via `delayCall` (it can fire minutes later and collide).
- Render settings set by script don't survive domain reloads — re-set them right before every launch.
- Export clears the lightmap storage bindings at the start and saves the scene, so a cancelled/killed bake can persist **empty bindings** (renderers keep `lightmapIndex`/`scaleOffset`). Recovery steps are in [bakery-bake-killed-by-domain-reload](bakery-bake-killed-by-domain-reload.md) ("Rebinding without a rebake").
- If someone else works in the editor during a blocking bake, they may cancel the progress bar. Batch edits, announce the bake with an ETA, then launch one bake.
- The official manual (geom.io/bakery/wiki) documents the UI only; for scripted field names read the bundled `ftRenderLightmap.cs`.

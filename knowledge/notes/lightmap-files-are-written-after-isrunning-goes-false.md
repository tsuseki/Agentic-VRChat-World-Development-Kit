---
title: Lightmap EXRs land on disk after the bake's completion signals
topic: lighting-baking
tags: [lightmapping, isRunning, LightingData.asset, md5, bake verification, reflection probes]
summary: Lightmapping.isRunning == false and the PathTracer completion line do not mean the output is on disk; hashing in that window makes a good bake look like it produced nothing.
---
**Symptom:** You verify a Unity Progressive GPU bake by hashing lightmaps and reflection probe files before and after, and get every file unchanged with on-disk mtimes from the previous bake. It looks exactly like a failed bake.

**Cause:** The check ran too early. None of these mean the output is written:
- `[PathTracer] Total bake time: ...` in `Editor.log` (pathtracing done, writing not started).
- `Lightmapping.isRunning == false`.
- `LightmapSettings.lightmaps` populated and `Renderer.lightmapIndex` already correct (in-memory only).

After the completion line Unity still convolves a cubemap for every reflection probe, then collects Enlighten data, imports `LightingData.asset`, and only then rewrites the `.exr` files. Re-running the same hash comparison ~40 s later showed nearly every file changed.

**Fix / rule:** Use a real completion oracle instead of `isRunning`:
- `LightingData.asset` mtime advances past the bake's start time, or
- `Editor.log` shows `Asset Pipeline Refresh ... Initiated by StopAssetImportingV2` after the `Total bake time` line, or
- re-measure after a delay and require the hash set to actually differ.

Ignore very short `Total bake time: 0.36`-style entries when watching the log; those are no-op passes. A single probe `.exr` that never changes across bakes may be an orphan file (more files than live probes) rather than a broken probe.

**Verify:** Confirm the `LightingData.asset` mtime moved first, then compare hashes. Never re-run a 10-minute bake on the strength of one hash pass taken right after the completion signal; it will "fail" the same way every time.

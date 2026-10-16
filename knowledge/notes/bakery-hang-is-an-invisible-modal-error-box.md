---
title: A Bakery bake that hangs forever is often the tracer blocked on an invisible error dialog
topic: lighting-baking
tags: [bakery, optix, nvidia-driver, ftrace, hang, win32-dialog]
summary: When a Bakery bake stalls with Unity idle, the ftrace tracer has usually raised a modal error box nobody can see, because Bakery launches it windowless and its fallback chain waits for an exit code that never comes.
---
**Symptom:** The bake sits forever at `Adjusting sample points for <group>...`, Unity at 0% CPU, `ftraceRTX.exe` parked at ~12 MB, process `Responding=True`, all threads in `Wait`.

**Cause:** `ftraceRTX.exe` (OptiX 6) raised a modal `Error (1546): Failed to load OptiX library`. Bakery launches tracers with `CreateNoWindow = true`, so no one can see or click OK. Bakery picks the tracer from a hardware probe cached once in `Assets/Bakery/ftGlobalStorage.asset` (`ftraceExe = gstorage.runsRTX6 ? "ftraceRTX.exe" : "ftraceRTX9.exe"`) and never rechecks it. A late-2025 NVIDIA driver dropped the OptiX 5/6 ABI, so a cached `runsRTX6 = true` became wrong. Because the process never exits, it never returns the exit code 1 that Bakery's `TryExes()` fallback waits for, so the automatic fallback to OptiX 9 never fires. Which tracer works is GPU + driver dependent - see [bakery-tracer-choice-depends-on-gpu-and-driver](bakery-tracer-choice-depends-on-gpu-and-driver.md).

**Fix / rule:**
- Bakery -> Utilities -> Detect optimal settings re-probes and fixes the cache.
- Or pin from an editor script before baking (on a machine where OptiX 9 is the working tracer): `gstorage.runsRTX6 = false`, force `ftraceExe = ftraceExe9`, `rtxMode = true`, and `ftBuildGraphics.exportTerrainAsHeightmap = false` (left true, Bakery forces rtxMode off and falls back to `ftrace.exe`).
- The progress-bar phase names the *first* group in the list, not the culprit - don't chase it.

**Diagnosing any "hung" windowless child process:** enumerate its windows with `EnumWindows`/`EnumChildWindows` filtered by PID. Window class `#32770` is a Win32 dialog; the `Static` child's text is the hidden error message. Near-zero CPU with all threads waiting is the tell. The same pattern applies to any editor tool that pops a modal dialog while driven headlessly (e.g. package import prompts blocking an MCP bridge).

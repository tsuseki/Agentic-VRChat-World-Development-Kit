---
title: Bakery tracer/denoiser compatibility depends on GPU AND driver; test by replaying logged ftrace commands
topic: lighting-baking
tags: [bakery, ftrace, optix, rtx, denoiser, oidn, vram, gpu]
summary: Which Bakery tracer (OptiX 5/6/9) and denoiser work flips between GPU generations and driver branches; replay a logged ftrace command against each exe to find out in seconds without Unity.
---
**Symptom:** Bakery bakes crash, assert or hang after a GPU or driver change; a config that worked on one card fails on another.
**Cause:** Compatibility is per GPU + driver branch. Measured on two machines: on an older non-RTX card (Pascal, R560 driver) `ftrace.exe` (OptiX 5) and `ftraceRTX.exe` (OptiX 6) worked while `ftraceRTX9.exe` access-violated and CUDA `denoiserOIDN2.exe` failed; on an RTX card with a newer driver the opposite held (only RTX9 worked). `ftraceRTX9` loads `nvoptix.dll` via `LoadLibrary`; some driver installs never stage it into System32, and copying it in did not fix the crash.
**Fix / rule:**
- On a non-RTX card: `rtxMode = false` (→ `ftrace.exe`), `renderSettingsDenoiserType: 100` (CPU OIDN). RTX mode on a card without RT cores is driver emulation and slower.
- Don't hardcode a tracer in bake scripts; derive it from the live adapter (`SystemInfo.graphicsDeviceName` containing "RTX" ⇒ rtxMode, then OptiX 6 vs 9 from Bakery's capability cache).
- After a GPU swap, Bakery notices (`gpuName_2 != SystemInfo.graphicsDeviceName`) and offers *Detect optimal settings* — re-run it rather than trusting stored capability fields.
- VRAM is often the real constraint on 6 GB cards: SteamVR Home alone held 2 GB, leaving Bakery ~428 MB and every trace crashing. Close SteamVR and spare browser windows before baking. Per-process VRAM: perf counter `\GPU Process Memory(pid_*)\Dedicated Usage` (`nvidia-smi` reports N/A under WDDM).
- Unity serializes an empty string with a trailing space (`gpuName_2: `); scripts that rewrite these assets must not `rstrip()` lines or they create spurious diffs.
**Verify (no Unity needed):** `Assets/Editor/x64/Bakery/.uvgblog.txt` logs every `Running ftrace… <args>` line of the last bake and `%TEMP%\frender` holds its export. Replay a logged command with a different exe — a replayed pass reproduced a previous output byte-for-byte. A replay overwrites files in `frender`, so the next bake must be a full Render, not an incremental one.

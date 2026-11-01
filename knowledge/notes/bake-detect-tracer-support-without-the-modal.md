---
title: Detect Bakery tracer support from a shell instead of the modal Detect dialog
topic: lighting-baking
tags: [Bakery, ftraceRTX9, OptiX, ftGlobalStorage, detect optimal settings]
summary: Bakery's Detect optimal settings ends in a modal dialog; run its hardware tests from PowerShell in the Bakery folder (exit 0 = works) and write the results into ftGlobalStorage yourself.
---
**Symptom:** *Detect optimal settings* blocks the editor on a modal dialog, which an agent driving the editor through
MCP cannot press; `execute_code` also refuses `Process.Start`.

**Fix / rule:** run each test from PowerShell, `Start-Process -WorkingDirectory <project>/Assets/Editor/x64/Bakery`
with the argument lists in `ftDetectSettings.cs` (e.g. `ftraceRTX9.exe /sun hwtestdata light 4 0 0 direct0.bin`,
`denoiserOIDN2 c hwtestdata/image.lz4 hwtestdata/image.lz4 16 0`); exit code 0 means it works. Running the exe
directly from a bash tool or through a `.cmd` file failed; PowerShell worked. Then write `ftGlobalStorage`:
`foundCompatibleSetup`, `gpuName_2`, `runsRTX6`/`runsRTX9`, `runsOptix5/6/7`, `runsOIDN`/`runsOIDN2`,
`renderSettingsRTXMode = true`, `renderSettingsExportTerrainAsHeightmap = false`, the denoiser type, and save it.
On an Ampere RTX card with an R590+ driver: RTX9, OptiX 7 and OIDN2 passed; RTX6, OptiX 5 and OptiX 6 failed.

**Related:** [bakery-tracer-choice-depends-on-gpu-and-driver](bakery-tracer-choice-depends-on-gpu-and-driver.md).

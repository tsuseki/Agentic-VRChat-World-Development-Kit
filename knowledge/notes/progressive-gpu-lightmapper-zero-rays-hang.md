---
title: Progressive GPU lightmapper '0rpt' = dead bake, not a slow one
topic: lighting-baking
tags: [progressive gpu, lightmapper, editor hang, Editor.log, PathTracer]
summary: On a large scene the Progressive GPU lightmapper can fail to schedule any rays and hang the editor while the progress bar sits at ~1%; grep Editor.log for PathTracer '0rpt' and stay on Progressive CPU.
---
**Symptom:** After switching to `ProgressiveGPU` on a large scene (~2.6k ContributeGI renderers, 3 km, 2048 atlases), `Lightmapping.buildProgress` sits at ~1% for half an hour, GPU 5–37%, Unity holds GBs of VRAM, `Responding` goes False and the MCP bridge times out.
**Cause:** `Editor.log` shows `[PathTracer] Failed to render lightmap with hash: … scheduledDirect: 0rpt, scheduledGI: 0rpt, scheduledEnv: 0rpt` — the work queue was never built.
**Fix / rule:** Keep `LightingSettings.lightmapper = ProgressiveCPU` for such scenes (or use Bakery). Diagnose slow bakes by grepping `Editor.log` for `PathTracer` rather than trusting `buildProgress`; check process `Responding` and GPU load.
**Pitfall:** Never `Thread.Sleep` inside `execute_code` to sample progress — it blocks the main thread and looks exactly like this hang. Sample across separate tool calls.
**Related:** a bake that cycles 0 → 99 % → 0 and never finishes is a different trap: a `VRCMirrorReflection` (or video screen) flagged Contribute GI. See the pre-bake sweep in [scripted-lightmap-prep-traps](scripted-lightmap-prep-traps.md).

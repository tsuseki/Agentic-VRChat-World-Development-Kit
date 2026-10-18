---
title: Concurrent headless Blender runs freeze a busy workstation; run one machine-wide, capped threads, low priority
topic: agent-workflow-verification
tags: [blender, headless, threads, CPU, priority, agents, workstation, parallel builds]
summary: Each headless Blender takes every core; two at once plus ~16 agent sessions froze a 16-thread PC, so run one Blender machine-wide with -t 6 at below-normal priority and keep ~4 builder agents active.
---
**Symptom:** During a parallel tree-pack production run the workstation froze: two headless Blender builds were running alongside ~16 agent sessions.

**Cause:** Each headless Blender uses all cores by default. The editor hosting the agent UIs alone drew ~6.5 of 16 cores, so two Blenders on top starved everything, including the UI and the MCP bridges.

**Fix / rule:**
- One Blender machine-wide, started with `-t 6` threads at below-normal process priority. The kit's `tool.py` wrapper enforces this via `blender.max_parallel` (1), `blender.threads` (6) and `low_priority` in the local tools config.
- About 4 builder agents at a time; the others do remote work (image generation, writing configs) until a build slot frees.
- Limit expensive sweeps: at most 3 cull fracs per tree.

**Verify:** Task manager / `Get-Process blender` shows a single Blender at BelowNormal priority and the machine stays responsive while it builds.

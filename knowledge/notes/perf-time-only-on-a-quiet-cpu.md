---
title: Time editor perf only while no other heavy process runs
topic: performance
tags: [PerfSample, noise, contention, Blender, gpuFrameMs, A/B/A]
summary: Background jobs (headless Blender renders, other agents) inflate editor timings by milliseconds; check the process list before every timing block, hold launches for the whole window, and discard runs whose gpuFrameMs jumps.
---
**Symptom:** identical baselines of one pose read 9.43 and 7.82 ms while sibling agents' Blender jobs used ~7 of 16
threads; a run's editor `gpuFrameMs` jumped from ~0.15 ms to 2.6–4.7 ms partway through.

**Fix / rule:**
- Before every timing block: no `blender` process (`Get-Process blender`) and a quiet
  `Get-Counter "\Process(*)\% Processor Time"`. One check is not enough (jobs relaunch): the coordinator holds all
  GPU/CPU-heavy launches for the whole timing window (45 min covered three worlds × two states). Do builds, captures
  and bundles outside that window.
- Discard any run whose `gpuFrameMs` leaves its floor; use contended runs only to rank roots (±1 ms).
- Noise floor on a quiet machine: back-to-back baselines 0.01–0.47 ms apart; the same pose 6.79–8.07 ms across
  sessions. Compare only within one session, final before/after as interleaved A/B/A passes, each pose twice.

**Verify:** two baselines per pose (`now`, `now2`) inside the noise floor before any variant is quoted.

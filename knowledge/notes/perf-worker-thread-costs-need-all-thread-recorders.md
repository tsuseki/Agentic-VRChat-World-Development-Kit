---
title: Worker-thread costs are invisible to main-thread samples; use all-thread recorders
topic: performance
tags: [Recorder, profiler markers, worker threads, CollectFromAllThreads]
summary: Probe sampling and other job costs run on worker threads; Recorder.FilterToCurrentThread hides them, so collect those markers from all threads, and use marker breakdowns for composition only.
---
**Symptom:** a lever saved 12.5 ms per frame of worker time on a 16-thread CPU, yet main-thread PerfSample runs
showed no change.

**Fix / rule:** read job markers (`CalculateLightProbeSamplingCoordinates`, `GetLightProbeInterpolationWeights`) with
`Recorder.Get(m).CollectFromAllThreads()`; use `FilterToCurrentThread()` only for main-thread attribution. Sum
`elapsedNanoseconds` per frame from an `EditorApplication.update` hook over 200 frames, return through `SessionState`,
then disable and reset to all threads. Template: `.omp/skills/vrchat-world-optimization/scripts/marker_profile.cs.txt`.

**Pitfalls:** recorder overhead swamps deltas: with ~25 recorders enabled `Camera.Render` read 10.5 ms against 6.4
lean. Take ms deltas from separate PerfSample runs; use breakdowns for what the frame is made of.

**Verify:** the marker you expect to move does, and the lean PerfSample `mainThreadMs` agrees in direction.

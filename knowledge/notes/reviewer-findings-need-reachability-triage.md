---
title: Triage reviewer findings by player reachability before acting
topic: agent-workflow-verification
tags: [review, reachability, flood-fill, sealed-volumes, camera-pitch, triage]
summary: A reviewer agent places cameras at arbitrary positions and will report real defects inside sealed, unreachable volumes; check each cited pose against a reachability model and re-measure from the nearest reachable pose.
---
**Symptom:** A reviewer reports blocker-class "black ceilings" and "see-through facade shells". The ceilings genuinely are black - but every cited camera sits inside a sealed volume no player can enter (decorative shells are sealed on purpose).

**Cause:** Confirming a defect exists is not confirming it matters. Acting on the raw report means re-baking or re-modelling permanently hidden geometry; dismissing it wholesale misses real findings.

**Fix / rule:**
- Build a reachability model: raycast-down grid + `Physics.OverlapCapsule` for player clearance + 4-connected flood fill (jump/step threshold ~1.0 m), keep the largest component. Check whether each cited position is reachable; re-measure from the nearest reachable pose.
- **Sweep with pitch up, not just level.** A level sweep structurally cannot see undercroft/overhang ceilings. A sweep at pitch -22 degrees (looking up), 4 yaws, over every reachable cell found the real dark spots in seconds.
- Heuristics like "`b >= r` means sky" false-positive on grey stone; confirm suspected sky bleed by viewing the capture.
- Genuinely dark narrow light wells (2-3 m gaps between tall buildings with overhangs) can be physically correct. Lowering Bakery AO there barely moved anything (meanDark 0.60% -> 0.51%) - treat as accept-or-seal, not a bake-settings problem.

Related: [interior-brightness-sampling-must-require-a-ceiling](interior-brightness-sampling-must-require-a-ceiling.md)

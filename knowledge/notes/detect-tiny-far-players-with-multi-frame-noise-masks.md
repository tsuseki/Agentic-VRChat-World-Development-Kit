---
title: Detecting a player a few pixels tall needs a multi-frame noise mask and a geometry check
topic: agent-workflow-verification
tags: [screenshots, pixel diff, positive control, mirrors, multi-client tests, false positives]
summary: A present/absent screenshot diff with a two-frame noise map reported a far player that was really the observer's own idle sway; take ~10 frames per state, mask every pixel whose range moves, park the absent subject out of sight, and check the hit lands where geometry predicts.
---

**Symptom.** In a two-client mirror test a "positive control" found 34-38 changed pixels at the same
spot twice, and a distant player was reported visible. Zoomed crops later showed the spot was the
observer's own reflection (sleeve edge swaying in the idle animation).

**Cause.** The noise map came from two frames ~1 s apart; slow idle sway, flickering fires and video
screens changed between the present and absent captures but not between the two noise frames.
Other false hits: the absent subject parked where it was visible straight through a see-through
(players-only) mirror, or parked on the observer (collision shoved the observer, the whole frame changed).

**Fix / rule.**
- Capture ~10 frames over ~4 s per state; compare the medians, and mask every pixel whose
  max-min range in **either** set exceeds the noise threshold.
- Turn video screens off; keep the target 15-20 deg off the mirror axis so it is not behind the
  observer's reflection.
- Park the absent subject where it is visible neither directly nor in the mirror, never on the observer.
- Predict the target's screen position (x = 0.5 + 0.5 tan(angle)/tan(hfov/2)) and accept a hit only
  there; save zoomed present|absent crops of the same box for a human to judge.

**Verify.** The positive control (far clip raised past the distance) gives a small cluster at the
predicted spot in every repeat; the negative state gives zero; the crops show it. Tool:
`.omp/scripts/e2e/scenarios/mirror_presence.py`.

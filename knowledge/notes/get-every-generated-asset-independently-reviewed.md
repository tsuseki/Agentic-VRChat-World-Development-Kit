---
title: Get every generated or placed asset independently reviewed before calling it done
topic: agent-workflow-verification
tags: [review, placement, scripted-placement, screenshots, self-check]
summary: Scripted placement passes "succeed" while producing obvious visual defects, so every asset or placement must be screenshot-checked and then rated by an independent reviewer before it is reported finished.
---
**Symptom:** A scripted seating pass reported success while chairs were buried up to 99% inside picnic tables and a tabletop had no texture. Any single screenshot would have caught it.

**Cause:** Scripted placement is exactly the case where nobody looks at the result - the script returned without error, so it was assumed correct.

**Fix / rule:**
- Treat review as a standing gate for modelled props, imported/scanned props, scripted placement passes and material work - not a per-task option.
- Screenshot-verify your own work first so the reviewer is not catching trivial issues, then hand it to an independent reviewer (e.g. the `dressing-reviewer` agent before the bake, `final-reviewer` after it) with: the art direction, the exact objects/area, and specific concerns. Act on its findings before declaring done.
- Self-check every placement for: prop-vs-prop interpenetration (AABB overlap sweep), floating or sunken props, and materials with no albedo texture.
- Triage reviewer findings by player reachability (see [reviewer-findings-need-reachability-triage](reviewer-findings-need-reachability-triage.md)).

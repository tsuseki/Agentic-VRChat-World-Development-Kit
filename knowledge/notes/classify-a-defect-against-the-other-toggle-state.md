---
title: Measure a defect in the other toggle state before fixing it
topic: agent-workflow-verification
tags: [lighting-states, regression, review-triage, night-mode, variants]
summary: Before fixing a defect found in one state of a toggle (night/day, on/off, variant A/B), measure the same object in the other state - many turn out pre-existing, and fixing those inverts the feature.
---
**Symptom:** Every review of a newly added state (night lighting mode, theme, variant) surfaces defects, and the reviewer - who can only see the new state - cannot tell a regression from something that was always like that.

**Example:** in a lights-out mode, three of five findings dissolved on measurement:
- a speaker cabinet "reading as a flat black cut-out" measured 0.00155 linear in the shipped day state too - a near-black prop by design;
- its grille was actually *brighter* at night (0.00032) than in day (0.00021);
- shelf boards measured 0.00143 day vs 0.00147 night - unrelated to the feature.

**Fix / rule:**
- For each finding, capture the metric in both states and quote both. Fix only what differs in the direction the feature caused; report the rest as pre-existing, with numbers, so nobody re-raises it.
- **Inversion test:** if a proposed fix would make the new state better than the baseline state on that object (e.g. a prop more visible with lights off than on), the finding is almost certainly pre-existing and the fix is backwards.
- When a reviewer says "I could not measure the other state", treat that as an assignment: you can toggle the state, so do it and report the classification.

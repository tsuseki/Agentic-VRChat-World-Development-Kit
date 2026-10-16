---
title: Re-audit ambient-only lighting exceptions after any global dim pass
topic: lighting-baking
tags: [ambient, emission, dim pass, exceptions, black object]
summary: An object decided to need no emission because ambient lights it goes pitch black when later global passes cut ambient; re-check every such exception after dimming.
---
**Symptom:** One object (e.g. a hero tree) renders pitch black after several scene-darkening passes, while similar objects survive.

**Cause:** An earlier decision ("receives ambient, so no emission") was correct when made, but it was a dependency on the ambient's *current* level. Global dim passes cut ambient to near zero without revisiting dependents. The survivors got their night tone from baked-in emission, not ambient. Nothing measures the break; the object still renders, just black.

**Fix / rule:** After any global lighting/ambient dim pass, enumerate the scene's recorded lighting exceptions (ambient-only objects, probe-lit props next to tuned probes, "no emission" calls) and re-render each; they are exactly what the pass can zero out. When diagnosing a "pitch black object" report, check whether it is the lone dependent of a source that was later dimmed before blaming its mesh or material (an A/B mesh swap can exonerate the mesh).

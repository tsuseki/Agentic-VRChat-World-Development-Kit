---
title: Name failing cases in a subagent brief as examples, not as the scope
topic: agent-workflow-verification
tags: [delegation, subagent, brief, verification scope, review]
summary: When a brief names the specific camera, object or value to check, the subagent verifies exactly that and the defect survives elsewhere; ask for the defect class to be swept.
---
**Symptom:** A builder reports "verified", then the review gate finds the same defect elsewhere — on other camera bearings, on a piece never treated, or at a second site where a copied constant was wrong.
**Cause:** A named camera/object/value reads as the definition of done; builders optimise to the stated check.
**Fix / rule:**
- Name the failing case as an EXAMPLE: "sweep a full ring of bearings, including X where it failed" and "apply to every piece, not only the ones the gate named".
- Ask for the whole class of defect to be swept.
- Pass measured constants with the measurement method and an instruction to re-measure locally, never as a number to match.
- Encourage builders that generalise past the brief and find unrequested problems.

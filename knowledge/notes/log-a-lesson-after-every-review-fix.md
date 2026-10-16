---
title: Record a lesson every time a review failure is fixed
topic: agent-workflow-verification
tags: [review loop, lessons, scene reviewer, knowledge, documentation]
summary: Whenever a reviewer verdict below SHIP IT is fixed and passes re-review, write down symptom, cause and rule before moving on.
---
**When:** Something fails a reviewer pass (dressing-reviewer, final-reviewer, ...) (NEEDS WORK / MINOR FIXES) and you then fix it to SHIP IT.

**How:** Before moving to the next task, append one entry: *symptom -> cause -> rule*, i.e. what the defect actually was, why the first build produced it, and the rule that stops it recurring. Not just "fixed it". Project-specific lessons go to that project's agent instructions (a "Review lessons" section works well). A shared knowledge note or skill change follows the "Lessons capture" rule in `.omp/AGENTS.md`: only the user's verdict, not a reviewer's, makes a lesson shared. Do it as part of closing the issue, not in a batch at the end.

**Why:** The review loop is where a world's real art-direction knowledge gets made. A fix that is not recorded gets rebuilt wrong in the next room and costs another bake and another review pass.

Related: [get-every-generated-asset-independently-reviewed](get-every-generated-asset-independently-reviewed.md)

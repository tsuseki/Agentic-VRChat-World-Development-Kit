---
title: Judge furniture facing by render, not by vertex density
topic: agent-workflow-verification
tags: [facing, orientation, furniture, metric, render, false positive]
summary: Counting vertices on each side to find a prop's front gives confident false positives on fluted, ribbed or wrapped furniture; open a render before rotating anything.
---
**Symptom:** After one genuine 180 degree error (a bookcase showing its blank back), a sweep that calls the vertex-denser side of each console its "front" reports four sideboards as turned around. All four were correct.

**Cause:** A fluted console's ribbing wraps the whole body, so vertex mass is symmetric front to back and the winner is noise. Overall triangle mass belongs to whatever surface treatment the model has. What distinguishes a front is small, localised, asymmetric features: handles, pulls, door/drawer gaps, plinth reveals, inset panels.

**Fix / rule:** Facing is a question about appearance, so answer it with a render: place an inspection light and shoot the piece head-on from the room side. Use geometry only for what geometry can answer, such as whether the back is flush with the wall plane. (Seating with a clear backrest can be measured; see [reviewer-rotation-values-are-inferred](reviewer-rotation-values-are-inferred.md).)

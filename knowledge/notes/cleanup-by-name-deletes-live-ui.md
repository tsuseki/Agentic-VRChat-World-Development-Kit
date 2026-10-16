---
title: Cleanup lists keyed by bare names delete live UI children
topic: unity-editor-scripting-mcp
tags: [cleanup, hierarchy path, UI, VRCUrlInputField, Placeholder, references]
summary: A stray-object cleanup queue of bare names deleted the Placeholder Text of a VRCUrlInputField; record full hierarchy paths and check incoming references before deleting.
---
**Symptom:** After a "stray objects" cleanup, a `VRCUrlInputField` loses its prompt text at runtime. Nothing errored.

**Cause:** The queue recorded only names (`BlockoutCam`, `Placeholder`, ...). `Placeholder` looked like blockout scaffolding but was `.../UrlCanvas/UrlInput/Placeholder`, the field's placeholder Text; deleting it set `field.placeholder = null`. Generic names that are almost always live UI: `Placeholder`, `Text`, `Caret`, `Background`, `Fill`, `Handle`, `Viewport`, `Content`, `Label` (Unity's UI templates create all of them).

**Fix / rule:** Record cleanup items as full hierarchy paths. Before deleting, print the full parent chain and component list, and for UI objects check whether a parent component references it. If a delete breaks a reference, recreate the child and re-assign the field, copying the sibling Text's RectTransform, font and alignment.

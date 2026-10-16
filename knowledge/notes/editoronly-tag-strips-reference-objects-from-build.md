---
title: Tag in-scene reference objects EditorOnly so the build strips them
topic: performance
tags: [EditorOnly, VRAM, scale reference, build size, inactive objects]
summary: Inactive objects still ship and still load their textures; the EditorOnly tag removes an object and its children at build time while keeping it in the editor.
---
**Symptom:** build texture memory far higher than anything visible. One audit found an inactive full avatar prefab parked in the world scene as a scale reference: 229 MB of textures, 36 renderers, 270k tris.

**Cause:** `SetActive(false)` does not exclude an object from the build; its referenced assets are packed and loaded.

**Fix / rule:** tag scale references, measuring capsules, reference avatars, debug cameras and old particle systems **`EditorOnly`**. Unity strips the object and all its children at build time; the editor keeps it. No pre-publish deletion step.

**Verify:** compare build texture memory before/after (that audit went 619 → 339 MB, −45 %, with no visual change, together with removing an orphaned texture reference left on several materials).
Related: [orphaned-material-texture-slots-still-cost-vram](orphaned-material-texture-slots-still-cost-vram.md), [editoronly-objects-are-null-at-runtime](editoronly-objects-are-null-at-runtime.md).

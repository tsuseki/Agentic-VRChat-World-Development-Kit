---
title: EditorOnly-tagged objects become null entries in wired arrays at runtime
topic: vrchat-sdk-upload-components
tags: [EditorOnly, clientsim, build-stripping, udonsharp, serialized-arrays, reflection-probe]
summary: ClientSim and the VRChat build strip EditorOnly-tagged GameObjects, so arrays wired to them in the inspector read null in play mode and in the shipped world.
---
**Symptom:** A `ReflectionProbe[]` or `Renderer[]` on an UdonSharp behaviour looks fully wired in the inspector but has null entries in play mode. Re-wiring and re-serializing changes nothing.

**Cause:** Both ClientSim and the VRChat build strip `EditorOnly`-tagged objects. The tag isn't shown anywhere near the array, and the objects work in the editor. Same class of trap: an `EditorOnly` audio source silently missing from the build.

**Fix / rule:**
- Before concluding a reference is broken, check the target's `tag`.
- When building wired arrays from an editor script, skip `gameObject.CompareTag("EditorOnly")` so the shipped array matches what exists.
- Mirror the stripping in any edit-mode preview of a runtime state: disable `EditorOnly` reflection probes etc., or the preview (and any reviewer judging it) shows lighting no player ever sees.

Related: [editoronly-tag-strips-reference-objects-from-build](editoronly-tag-strips-reference-objects-from-build.md)

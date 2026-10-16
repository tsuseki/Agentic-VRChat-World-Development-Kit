---
title: After a U# edit the VM can run the old program while exposing new variables
topic: udonsharp-networking
tags: [UdonSharp, CompileSync, stale program, play mode, CopyProxyToUdon, recovered_from_disconnect, UI wiring]
summary: After editing a U# script the UdonBehaviour can keep running the previously compiled program while already exposing the new public variables; confirm behaviour in play mode and force CompileSync when stale.
---
**Symptom:** After editing an `UdonSharpBehaviour` (adding a `float[]` field plus logic that consumes it) and recompiling, `ub.TryGetProgramVariable(...)` in play mode returns the new array with correct values, and an edit-mode preview of the same logic looks right, but the VM applies the pre-edit code path. Tell: two entries that should get *different* computed values come out identical, and equal to what the previous code produced.

**Cause:** The compiled Udon program is stale although the domain reload finished with no console error, and every inspector and edit-mode check passes. Observed right after a Unity MCP `refresh_unity` that reported `recovered_from_disconnect`. It cost a full misdiagnosis round (wiring, nulls, `CopyProxyToUdon`, EditorOnly stripping) before the program itself was suspected.

**Fix / rule:**
- Treat any interrupted or recovered compile as "program probably stale".
- Force a real rebuild: `UdonSharpCompilerV1.CompileSync(new UdonSharpCompileOptions())` (reflect for the type; the overload exists), then `UdonSharpEditorUtility.CopyProxyToUdon(proxy)`.
- Brand-new scripts: without a compiled program every serialization call dies with `ArgumentNullException: key` in `UdonSharpBehaviourFormatterEmitter.GetHeapData`; create the program asset and compile before adding components (see [udonsharp-add-component-from-editor-script](udonsharp-add-component-from-editor-script.md)).
- Wiring a UI button to a U# method from an editor script: `UnityEventTools.AddStringPersistentListener(btn.onClick, new UnityAction<string>(backingUdon.SendCustomEvent), "EventName")`, with the backing behaviour from `UdonSharpEditorUtility.GetBackingUdonBehaviour(proxy)`.

**Verify:** Confirm every U# behaviour change by observing its effect in play mode (see [drive-udonsharp-in-play-mode-through-the-udonbehaviour](drive-udonsharp-in-play-mode-through-the-udonbehaviour.md)). Reading a value back proves serialization, never execution.

---
title: Adding and inspecting UdonSharp behaviours from editor scripts
topic: unity-editor-scripting-mcp
tags: [udonsharp, editor script, AddUdonSharpComponent, proxy, CopyProxyToUdon, GetProgramVariable]
summary: Use UdonSharpComponentExtensions.AddUdonSharpComponent (or UdonSharpUndo.AddComponent) after the program asset exists and compiles; proxy fields are the source of truth in edit mode.
---
**Symptom:** Scripting a U# component onto a GameObject fails: `UdonSharpEditorUtility.AddUdonSharpComponent` does not exist; `CreateBehaviourForProxy` throws `ArgumentNullException: key`; `ConvertToUdonBehaviours` is obsolete.
**Fix / rule:**
- Working calls observed: `UdonSharpEditor.UdonSharpComponentExtensions.AddUdonSharpComponent(GameObject, Type)` and `UdonSharpEditor.UdonSharpUndo.AddComponent(GameObject, Type)`.
- The program asset must exist first; compile with `UdonSharpCompilerV1.CompileSync(new UdonSharpCompileOptions())` before adding.
- Set proxy public fields, then `UdonSharpEditorUtility.CopyProxyToUdon(proxy)` if values must reach the UdonBehaviour now; otherwise they are copied at play/build.
- `TryGetProgramVariable` returns nothing in plain edit mode — not a wiring bug.
- `GetComponent<UdonBehaviour>()` on an object with several U# behaviours returns the first; `SetProgramVariable` on the wrong one silently no-ops. Iterate `GetComponents<UdonBehaviour>()` and match `b.programSource.name`.
- `CompileSync()` returns normally even with compile errors; clear the console, recompile, re-read.
- If a method name isn't confirmed, reflect over the UdonSharp editor assemblies (`AppDomain.CurrentDomain.GetAssemblies()` → types under `UdonSharpEditor` → public static methods) instead of guessing. Remove half-built components before retrying.
- `TextMesh.text` is not exposed to Udon; runtime text set by U# must be UGUI `Text`/TMP.

**Also observed:**
- Creating the program asset by script: `ScriptableObject.CreateInstance<UdonSharp.UdonSharpProgramAsset>()` (namespace **`UdonSharp`**, not `UdonSharpEditor`) → set `sourceCsScript` → `AssetDatabase.CreateAsset` → `UdonSharp.UdonSharpProgramAsset.CompileAllCsPrograms(true, false)`. The class→asset map is not queryable in the same `execute_code` call (`GetProgramAssetForClass` returns null → `ArgumentNullException: key`); add the component in a later call.
- A scripted add came up `SyncMethod: Continuous` despite `[UdonBehaviourSyncMode(Manual)]`, which breaks `RequestSerialization`. Set `ub.SyncMethod` explicitly from the program asset's `behaviourSyncMode` (`None` → `SyncType.None`; `Manual`/`NoVariableSync` → `SyncType.Manual`).

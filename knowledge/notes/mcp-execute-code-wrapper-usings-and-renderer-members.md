---
title: execute_code C# traps: the wrapper's usings and members that aren't on Renderer
topic: unity-editor-scripting-mcp
tags: [execute_code, C#, ambiguous reference, MeshRenderer, compile errors]
summary: The Unity MCP execute_code wrapper imports System, System.Collections.Generic, System.Linq, System.Reflection, UnityEngine and UnityEditor, so Object and Random are ambiguous, sub-namespaces need qualifying, and receiveGI / scaleInLightmap live on MeshRenderer.
---
**Symptom:** eight compile-error round trips in one session: "ambiguous reference between UnityEngine.Object and
object", `Renderer` has no `receiveGI`, `EditorSceneManager` not found, `System.Tuple` ambiguous, double-to-float errors.

**Cause:** the wrapper compiles the body inside a class with `using System; System.Collections.Generic; System.Linq;
System.Reflection; UnityEngine; UnityEditor;` and nothing else.

**Fix / rule:**
- `UnityEngine.Object.FindObjectsOfType<...>()`, `UnityEngine.Random` (both names exist in `System`).
- Qualify sub-namespaces: `UnityEditor.SceneManagement.EditorSceneManager`, `UnityEngine.Rendering.*`, and package
  types (`AWDK.AgentTools.ZFightScan`, `.WorldAudit`).
- `System.Tuple` is ambiguous (a second definition ships in an editor assembly): use value tuples `(a, b)` or `KeyValuePair`.
- `receiveGI` and `scaleInLightmap` are `MeshRenderer` members: cast (`r as MeshRenderer`) or use `SerializedObject`
  `m_ScaleInLightmap` (prefab instances also need `PrefabUtility.RecordPrefabInstancePropertyModifications`).
- Float parameters take `f` literals; C# never converts double to float implicitly, lambdas included.
- A `//` comment in a body sent as one line swallows the rest of the line (and can hide the error): use newlines or `/* */`.

**Verify:** the call compiles first time; read the full compiler message when it doesn't.

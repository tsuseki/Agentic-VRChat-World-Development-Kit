---
title: Revert one geometry pass by reading transforms from the old scene YAML in git
topic: unity-editor-scripting-mcp
tags: [git, scene YAML, revert, fileID, transform, restore]
summary: To undo one change in a large scene that also holds work you must keep, read the old transforms out of the committed .unity YAML and re-apply them through the editor.
---
**When:** A geometry change (e.g. narrowing a stair) must be undone, but `git checkout` of the scene would also throw away other work in the same file.

**How:** Dump the pre-change scene and index it by fileID:
```python
subprocess.run(["git","-C",PROJ,"show", f"{OLD_COMMIT}:Assets/Scenes/Scene.unity"], stdout=f)
docs = re.split(r"\n--- !u!", open(out, encoding='utf-8', errors='ignore').read())
objs = {m.group(2): (m.group(1), d) for d in docs[1:] if (m := re.match(r"(\d+) &(\d+)", d))}
```
Class ids: `1` GameObject, `4` Transform, `65` BoxCollider, `23` MeshRenderer, `33` MeshFilter, `114` MonoBehaviour (ProBuilderMesh lives here). A GameObject lists `component: {fileID: N}`; follow to the Transform and read `m_LocalPosition`, `m_LocalRotation` (quaternion), `m_LocalScale`. Match by `m_Name`, then apply the values in the open editor via scripting (do not hand-edit the open scene file).

Two checks before writing anything:
1. **Do names encode the original coordinates?** (`Stringer_9.91`, `Balu_Rail_4.02`.) If the pass moved objects without renaming, the intended values are still legible. Naming generated geometry after its authored coordinate turns a revert into arithmetic.
2. **Was it a rescale or a rebuild?** Solve from rotated world bounds: for a box of local length `L`, height `H`, pitch `p`, `scale.z = s`: `zExtent = L*s*cos p + H*sin p`, `yExtent = L*s*sin p + H*cos p`. If `L` matches the original, meshes are untouched and only transforms need restoring.

**Pitfalls:** The pass being reverted may have fixed real bugs (here the top tread landing flush). Restore original proportions and re-derive dependent values (`riser = storeyHeight / treadCount`) rather than pasting old numbers blindly.

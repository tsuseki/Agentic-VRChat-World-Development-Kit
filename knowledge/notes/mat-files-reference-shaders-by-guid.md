---
title: A .mat file stores its shader as a GUID/fileID, not a name
topic: materials-textures-shaders
tags: [material, shader, git, grep, diagnostic, Unlit/Color]
summary: Grepping a .mat for a shader name always finds nothing, so a diagnostic/keyed material can pass a text check and ship.
---
**Symptom:** You temporarily keyed materials to a diagnostic shader (e.g. `Unlit/Color` magenta) to measure something, committed, then `git show <c>:path/M.mat | grep -c Unlit` returns 0 — "clean". It is not.

**Cause:** A `.mat` never spells its shader name. Built-in shaders share one GUID and differ only by `fileID`:
```yaml
m_Shader: {fileID: 46,    guid: 0000000000000000f000000000000000, type: 0}   # Standard
m_Shader: {fileID: 10755, guid: 0000000000000000f000000000000000, type: 0}   # Unlit/Color
```
The colour is just `- _Color: {r: 1, g: 0, b: 1, a: 1}` — not findable by any word you would grep. A clean `git status` only means the working copy matches an already-contaminated HEAD.

**Fix / rule:**
- Ask the engine, not the file: sweep every material with `AssetDatabase.LoadAssetAtPath<Material>(p).shader.name` and assert the diagnostic shader count is 0.
- Restore from the last commit **before** the keying, not from `HEAD`.
- After `git checkout` of a `.mat`, Unity keeps the old material in memory until `AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate)`. A plain `Refresh()` is not enough.

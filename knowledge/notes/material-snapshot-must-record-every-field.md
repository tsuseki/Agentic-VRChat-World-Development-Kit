---
title: A material snapshot/restore must capture every field it writes back
topic: unity-editor-scripting-mcp
tags: [material, snapshot, restore, SetColor, alpha, lightmap flags, git]
summary: Restoring with SetColor(new Color(r,g,b)) forces alpha to 1 and a partial snapshot can rewrite m_LightmapFlags; record every field you will write, or restore from git.
---
**Symptom:** After a scripted "restore original emissive colours" pass, `git diff` shows many `.mat` files changed: `_EmissionColor` alpha 0.3 / 1.3 / 1.4 / 0.7 → all 1, and `m_LightmapFlags` 0 → 2 on some.

**Cause:** The JSON snapshot stored only `r, g, b` and the keyword. `mat.SetColor("_EmissionColor", new Color(r, g, b))` forces alpha = 1. The GI flag was written from a default rather than the captured value.

**Fix / rule:**
- Snapshot **every** field you intend to write back (colour incl. alpha, keywords, `globalIlluminationFlags`).
- Prefer `git checkout <commit> -- <files>` over a hand-rolled restore whenever files are tracked — exact, cannot drop a field.
- Lightmap output folders are often gitignored; verify those by md5 against a backup.

**Pitfalls:** `_EmissionColor.a` is not rendered by the Standard shader (it's an artifact of the HDR picker's intensity encoding), so this clobber produces a real committed diff but **no visual change**. Don't look for it in a render — find it with `git diff`. Before diffing renders to explain a change, run `git status` / `git diff` on the assets.

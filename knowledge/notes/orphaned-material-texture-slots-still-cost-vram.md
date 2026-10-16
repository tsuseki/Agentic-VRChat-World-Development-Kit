---
title: Orphaned texture slots on materials still load into VRAM, and HasProperty hides them
topic: performance
tags: [vram, materials, uber-shader, orphan-texture, serializedobject, profiler]
summary: A material can keep a texture on a property its current shader no longer exposes; it still loads into VRAM, HasProperty returns false, and a cleanup guarded by HasProperty skips exactly those.
---
**Symptom:** A VRAM cleanup that nulls unused texture slots "succeeds" but memory barely moves.

**Cause:** Unity keeps texture references for properties the current shader variant doesn't expose in `m_SavedProperties.m_TexEnvs`; the asset still loads. The API half-hides it:
- `mat.HasProperty("_Foo")` -> **false**
- `mat.GetTexture("_Foo")` -> the texture, non-null
- `mat.GetTexturePropertyNames()` -> still lists `_Foo`
- enumerating the shader via `ShaderUtil.GetPropertyCount` -> does not list it

Example: an 8192x8192 rain texture sheet left on 7 materials of an uber shader with the rain feature disabled = 50.5 MB resident, never sampled. A loop written as `if (!mat.HasProperty(p)) continue; mat.SetTexture(p, null);` cleared 1 of 7.

**Fix / rule:**
- Audit from the **material** (`GetTexturePropertyNames()`), never from the shader's property list.
- Clear orphans via `SerializedObject` -> `m_SavedProperties.m_TexEnvs` -> match `first.stringValue` -> null `second.m_Texture`. `SetTexture` on a non-exposed property does not reliably remove the entry.
- Uber shaders with many optional slots (Mochie, Poiyomi, lilToon) are where this accumulates.

**Verify:** Attribute VRAM with `Profiler.GetRuntimeMemorySizeLong(tex)` over a `HashSet<Texture>` gathered from every renderer (`FindObjectsOfType<Renderer>(true)`, including inactive) plus terrain layers and alphamaps.

---
title: Never round-trip floats through strings in editor scripts: locale commas give 100x values
topic: unity-editor-scripting-mcp
tags: [locale, float.Parse, CultureInfo, InvariantCulture, comma decimal, execute_code]
summary: Under a comma-decimal OS locale, editor float formatting prints '1,15' and parsing it back yields 115 even with InvariantCulture, silently writing wrong values into the scene.
---
**Symptom:** Screenshot cameras render black/garbage because positions packed as `"x,y,z"` and re-parsed land outside the world (172.5 became 1725); integer positions work, disguising the cause. Or a bulk write sets 13 lights to intensity 115 instead of 1.15.

**Cause:** The Unity editor inherits the OS culture. Under a comma-decimal locale, `float.ToString()` / `ToString("F2")` emit `1,15`, and tool output from code-execution calls shows vectors like `(13,70, 15,30)`. Parsing back fails silently:
- `float.Parse("172.5")` with the current culture treats `.` as a thousands separator: 1725.
- `float.Parse("1,15", CultureInfo.InvariantCulture)` treats `,` as a group separator: 115. InvariantCulture does **not** save you here.

**Fix / rule:**
- Never round-trip a number through its own formatted string; keep the `float`. For histograms/modes key on `Mathf.RoundToInt(v*100)`, not `ToString`.
- Target values are literals in code (`const float FAM = 1.15f;`, `new Vector3(0f, 2.4f, 174.5f)`), never derived from a previous tool result's text. When reading tool output, commas may be decimal separators.
- If you must parse, disallow thousands separators so it throws instead of lying: `float.Parse(s, NumberStyles.Float & ~NumberStyles.AllowThousands, CultureInfo.InvariantCulture)`; format with `CultureInfo.InvariantCulture`.

**Verify:** Sanity-gate every bulk write by asserting the resulting range (e.g. intensities within 1.15-3.40, zero outliers above 4.0).

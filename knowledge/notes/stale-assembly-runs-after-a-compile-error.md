---
title: After a compile error the editor keeps running the previous assembly, so a placement script silently ignores new code
topic: unity-editor-scripting-mcp
tags: [compile error, stale assembly, execute_code, placement script, read_console]
summary: A single error CS leaves the last good assembly loaded, so calls to your new method or data field run the old code with no error; read the console for error CS after every refresh and prove new code ran by a measured result.
---
**Symptom:** A placement tool was re-run after its data gained new fields (skirts under floating walls) and reported success, but the scene had no new geometry; a review then found the old defect and a record claiming the new one existed.

**Cause:** The editor script had a compile error (an undefined variable in an unrelated method). Unity keeps the last successfully compiled assembly loaded, so the old `Place` ran, ignored the unknown data fields, and returned normally. Nothing in the call result mentions the error.

**Fix / rule:**
- After every asset refresh or script edit, read the console filtered to `error CS` before calling the new code; a clean `isCompiling = false` is not proof of a clean compile.
- Make new tools return a count of what they built (skirts built, items placed) and assert it against the data, so a stale assembly fails loudly.
- Never write "exists" in a doc from the tool's return value alone; measure the scene (gap raycasts, renderer counts).

**Verify:** introduce a counter in the tool's return value, run it, and confirm the number changes after the fix.

Related: [one-broken-editor-script-blocks-all-agents](one-broken-editor-script-blocks-all-agents.md), [play-mode-silently-refuses-on-compile-errors](play-mode-silently-refuses-on-compile-errors.md)

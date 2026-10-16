---
title: IPython rewrites `x = !expr` lines even inside string literals
topic: unity-editor-scripting-mcp
tags: [IPython, Jupyter, shell escape, embedded C#, execute_code, compile error]
summary: When C# for Unity is embedded in a Python triple-quoted string run through IPython, any line of the form `ident = !expr` is rewritten as a shell capture before Python parses it, corrupting the C#.
---
**Symptom:** C# sent to Unity from an IPython/Jupyter cell fails with a pair of errors like `; expected` and "the name '<shell helper>' does not exist in the current context" on a line that looks fine, e.g. `haveFoot = !f2;`. A `code.replace(...)` fix on that line is a no-op.

**Cause:** IPython's input transformers run on the raw cell text line by line, **before** parsing, and do not know a line is inside a string literal. The `x = !cmd` shell-capture form is rewritten into a call to a shell helper (e.g. `haveFoot = <helper>("f2;")`). The string in memory is already rewritten, so search-and-replace on the original text finds nothing.

**Fix / rule:** Never start an embedded line with `ident = !expr`. Use `ident = (expr == false);`, invert the flag's meaning (`bool empty` instead of `bool haveFoot`), or add a paren: `ident = (!expr);`. `!=` and `if (!(...))` are safe; only the assignment form triggers the transform.

**Verify:** When a compile error names an unknown helper, or a syntactically fine line fails, print the offending lines back: `for i in range(12, 19): print(f"{i:>3}: {lines[i]!r}")`.

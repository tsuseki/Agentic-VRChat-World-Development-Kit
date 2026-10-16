---
title: SendCustomEvent silently fails on parameterised UdonSharp methods — they export as __0_Name
topic: udonsharp-networking
tags: [UdonSharp, SendCustomEvent, entry points, NetworkCallable, SetProgramVariable, testing]
summary: A public UdonSharp method with parameters that is not [NetworkCallable] exports under a mangled name like __0_Method, so SendCustomEvent("Method") does nothing and a test can falsely pass.
---
**Symptom:** A play-mode test drives `SendCustomEvent("OnPersistenceRestored")` and the expected value holds — but the method never ran (the value was right for an unrelated reason). No error, no log.

**Cause:** Public methods **with parameters** that aren't `[NetworkCallable]` export mangled: `OnPersistenceRestored(bool)` → `__0_OnPersistenceRestored`, `Toggle(int)` → `__0_Toggle`. Parameterless and `[NetworkCallable]` methods keep plain names. `Start()` is `_start`.

**Fix / rule:** before driving a method from editor scripting, dump the real names:
- Entry points: `prog.EntryPoints.GetExportedSymbols()`.
- Parameters: `prog.SymbolTable.GetSymbols()` — named `__<n>_<param>__param`, where `n` counts occurrences of that **parameter name** across the whole class in declaration order (not the method index).
- Set the parameter symbols with `SetProgramVariable`, then `SendCustomEvent` the mangled entry point.

**Verify:** confirm the method actually executed (a log line or a state change that can only come from it) rather than trusting an unchanged value.

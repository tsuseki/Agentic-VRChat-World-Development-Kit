# Troubleshooting recipes

Linked from `.omp/AGENTS.md` "Routing". Odd world/editor behaviour goes to `.omp/skills/vrchat-world-gotchas/SKILL.md`
and `.omp/knowledge/notes/` first; these recipes cover the launcher and the harness.

## Unity launch via an already-running ALCOM/VCC

If the harness reports `Daemon start request timed out`, try the launcher's **OPEN UNITY** button; launcher failure does not prove Unity cannot open (verified 2026-09-13).

- Automating the launcher's window (UI Automation, `InvokePattern`): discover its current process at run time; never reuse recorded process ids or window handles. **Confirm the displayed project path before clicking.**
- Verify Unity's `-projectPath`, wait for its MCP instance and pin the exact instance with `set_active_instance`. Process creation/button invocation is not MCP readiness. Leave other Editors untouched.
- Launching `Unity.exe` directly from a script kernel can inherit an environment without `ALLUSERSPROFILE`: UPM then logs `The "path" argument must be of type string. Received undefined` and silently ignores newly added packages while the editor runs from cached package state. Pass the merged machine+user environment plus `ALLUSERSPROFILE=C:\ProgramData` and `PUBLIC` (verified 2026-10-02, Gregg Talk).

## Oversized screenshot payloads

`HTTP 413 request_too_large` is a **byte**, not token, limit; compaction or token thresholds cannot fix oversized base64 screenshots. A 1600×900 PNG can occupy ~3.5 MB base64 despite low token accounting. Re-encode large tool images before they reach the model (for example progressive JPEG via Python/Pillow: measured 3.53 MB → 0.37 MB at full resolution), if your host supports an image hook.

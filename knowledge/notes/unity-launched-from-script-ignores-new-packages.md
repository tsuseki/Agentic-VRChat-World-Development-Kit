---
title: Unity launched from a script with a stripped environment silently ignores new packages
topic: unity-editor-scripting-mcp
tags: [unity, upm, packages, launch, windows, environment, alcom, vcc]
summary: Launching Unity.exe from an agent/kernel without ALLUSERSPROFILE makes UPM fail quietly and keep running from cached package state.
---
**Symptom:** You add a package (manifest or VCC/ALCOM), launch `Unity.exe` from a script or agent
kernel, and the package never appears. The Editor log contains
`The "path" argument must be of type string. Received undefined`.

**Cause:** The child process inherited an environment without `ALLUSERSPROFILE` (and often
`PUBLIC`). The Unity Package Manager's Node process needs them; it errors and the Editor keeps
running on the previously resolved package cache.

**Fix / rule:** When launching Unity programmatically on Windows, pass the merged machine + user
environment and explicitly set `ALLUSERSPROFILE=C:\ProgramData` and `PUBLIC=%SystemDrive%\Users\Public`.
Alternatively, open the project with the VCC/ALCOM "Open Unity" button (can be driven via
PowerShell UI Automation `InvokePattern` if the launcher's own CLI times out — confirm the shown
project path before clicking).

**Verify:** Check the Editor log for the UPM error, and confirm the package folder appears under
`Library/PackageCache` or `Packages/`. Process start is not MCP readiness — wait for the MCP
instance to register before sending commands.

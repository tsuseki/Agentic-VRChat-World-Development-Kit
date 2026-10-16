---
title: Vendor world packages can ship without their U# scripts or with lilToon-only materials
topic: import-fbx-prefabs
tags: [unitypackage, missing script, GUID, lilToon, Standard, prefab rotation, vendor]
summary: Missing-script components heal automatically if the .cs with the original GUID is dropped in later; untextured lilToon materials convert to Standard nearly losslessly.
---
**Symptoms / rules:**
- **Missing scripts:** prefabs show missing-script components because the `.cs`, program assets and serialized programs were never included in the package. Native SDK parts (e.g. `VRCStation` + animator controller) keep working; script-driven features die. If the script package turns up, dropping the `.cs` back in with its original GUID heals every prefab **and** every placed instance. Disable UI that depends on the missing scripts.
- A helper package may contain a stripped Avatars SDK DLL that animator controllers need for `VRCAnimator*` state behaviours — check before deleting it from a Worlds project.
- **lilToon materials** render magenta without `jp.lilxyzw.liltoon`. If they carry no albedo textures (flat `_Color` + matcap), converting to Standard is nearly lossless (e.g. grey metal 0.651 / metallic 0.875 / smoothness 0.90).
- **Prefab roots with baked rotations** (e.g. `Euler(-90,0,0)`, `Euler(0,-90,0)`): compose yaw, don't assign — see [compose-fbx-root-rotation-never-assign](compose-fbx-root-rotation-never-assign.md).
- Count what each instance adds: trigger-only colliders add no player collision, but stations, object syncs and UdonBehaviours add up per instance.
- `Broken text PPtr` errors on import from a vendor `.controller` are a dangling reference in their asset — harmless.

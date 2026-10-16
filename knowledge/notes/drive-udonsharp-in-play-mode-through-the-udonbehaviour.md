---
title: Drive and inspect UdonSharp in play mode via the UdonBehaviour, and fake players with ClientSim
topic: udonsharp-networking
tags: [UdonSharp, play mode, SendCustomEvent, GetProgramVariable, ClientSim, testing, _start]
summary: In play mode the UdonSharpBehaviour C# proxy is empty; call SendCustomEvent/Get/SetProgramVariable on the paired UdonBehaviour, and spawn named fake players through ClientSim.
---
**Symptom:** Calling methods on an `UdonSharpBehaviour` in play mode throws `NullReferenceException` and its fields read default. Looks like a product bug; it is not.

**Cause:** In play mode UdonSharp runs in the Udon VM. The C# component is an edit-time proxy; runtime state lives in the VM. Serialized public refs on the proxy are still valid for reading scene wiring.

**How:**
- `ub.SendCustomEvent("MethodName")` for public parameterless methods.
- `ub.GetProgramVariable("x")` / `SetProgramVariable("x", v)` for fields, including private and `[UdonSynced]`.
- `Start()` is the Udon event **`_start`**; `SendCustomEvent("Start")` silently does nothing.
- Methods with parameters export under mangled names and take their arguments as program variables; see the related note for the naming scheme before calling them.

**Fake multiple named players with ClientSim:**
```csharp
var main    = System.Type.GetType("VRC.SDK3.ClientSim.ClientSimMain, VRC.ClientSim");
var inst    = main.GetField("_instance", Static|NonPublic).GetValue(null);
var spawner = main.GetField("playerSpawner", Instance|NonPublic).GetValue(inst);
spawner.GetType().GetMethod("SpawnPlayer").Invoke(spawner, new object[]{ "Vale", false });
// removal: main.GetField("_playerManager", ...) -> RemovePlayer(VRCPlayerApi)
```
Network events do not route to fakes, but presence, `GetPlayers`, display-name matching and join/leave callbacks run for real. With `SetProgramVariable` staging synced state this covers most roster and queue-ordering bugs without a multi-client build.

**Pitfalls:**
- Query VM state a few frames after entering play mode; before `Start` runs every field reads null.
- `SetProgramVariable` at runtime does not dirty the scene; confirm with `scene.isDirty`.
- `PlayerData` persists across play sessions, so state from a previous run can bleed in.

Related: [udonsharp-parameterised-methods-export-mangled-names](udonsharp-parameterised-methods-export-mangled-names.md).

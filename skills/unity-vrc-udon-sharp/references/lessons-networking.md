# UdonSharp networking lessons

Proven rules for driving, testing and structuring UdonSharp and synced world logic, beyond the NEVER list and references in SKILL.md.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Driving and testing in play mode

- **Drive U# in play mode through the paired UdonBehaviour (`SendCustomEvent`, `Get/SetProgramVariable`) and spawn named fake players through ClientSim's player spawner** — the C# proxy is empty at runtime, `Start` is `_start`, fields read null until a few frames in, and fakes run presence/join/leave for real but get no network events.
- **Dump exported entry points and parameter symbols before calling a parameterised method; set `__<n>_<param>__param` then send the mangled `__0_Name`** — non-`[NetworkCallable]` methods with parameters export mangled, so `SendCustomEvent("Name")` no-ops silently; prove the method ran from a log or state change only it can cause.
- **Treat any interrupted or recovered compile as a stale program: force `UdonSharpCompilerV1.CompileSync` then `CopyProxyToUdon`, and confirm behaviour changes by effect in play mode** — the VM can run old code while exposing the new variables, so reading a value back proves serialization, never execution.

## Keeping shipped data clean

- **Snapshot and restore U# serialized arrays that runtime code writes, with an `[InitializeOnLoad]` play-mode guard** — a drawn inspector copies the Udon heap back onto the proxy and the next save ships a tester's runtime values over authored data; never hand-fix while still in play mode.
- **Migrate a renderer out of a toggle list instead of just removing it, and assert the shipped state scene-wide (no `CustomProvided` probe usage, no property blocks)** — the OFF path no longer visits it, so its stale property block and serialized renderer fields from the ON path leak into the default state.

## Ownership patterns

- **For claimable pools, put a small synced claim behaviour on each object and claim by `SetOwner` → write → `RequestSerialization`; no central registry** — single ownership is the mutex; master clears claims `OnPlayerLeft` plus an idle timeout, never index arrays by `playerId`, and name-based reservations are courtesy, not security.
- **Lock a private room with one Manual-sync bool on a lever; every client runs a slow occupancy loop but only the owner acts, unlocking after two consecutive empty checks** — gating on `IsOwner` each tick survives owner handoff; duplicated rooms need their door, sign and icon arrays rewired, and late joiners need a 2-client Build & Test.
- **Mix one global Manual-synced catchable with local once-per-player collectibles, and keep the shared "+N" popup's GameObject active** — a U#-to-U# call into an inactive object silently no-ops; size trigger boxes on scaled imports in local units, and expect ClientSim to give +0 for the first seconds of play.

## Integrations and display

- **Bridge third-party minigames to a shared currency at each game's single money-backend class, keep the purse object's exact name, and make game resets clear bets only** — the whole game follows that one class, and shared-currency scripts often find the purse with `GameObject.Find`.
- **Keep SmartObjectSync (≥ 3.10.0) rather than migrating to LightSync; reset its example pickups to proximity 0.1 and toggle grabbability through `SmartObjectSync.pickupable`** — the example prefabs ship proximity 2, and writing `VRC_Pickup.pickupable` directly is overwritten by the ownership logic.
- **Format in-world numbers by converting to integers and joining with a literal `"."`, never by handing floats to `string.Format`** — Udon runs under each player's locale with no InvariantCulture, so some players see `3:02,412`.

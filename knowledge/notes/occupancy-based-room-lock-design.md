---
title: Private room lock: one synced bool, owner-run auto-unlock when the room is empty
topic: udonsharp-networking
tags: [room lock, UdonSynced, Manual sync, ownership, auto-unlock, teleport door]
summary: A Manual-sync lever toggles one synced bool; every client runs a slow check loop but only the owner acts, unlocking after two consecutive empty checks.
---
**How:**
- Lever behaviour (Manual sync, own GameObject) with one `[UdonSynced] bool`. Interact = `SetOwner` → flip → `RequestSerialization`. `ApplyState` (also from `OnDeserialization`) drives locked/unlocked icon arrays, `DisableInteractive` on the outside door (blocks the teleport in), a lever material swap and the interaction text.
- **Auto-unlock:** every client runs a ~3 s loop, but only `Networking.IsOwner` acts. If the room is empty (box test in a room-bounds transform's local space) for 2 consecutive checks, the owner unlocks. Ownership transfers when the owner leaves, and the loop gates on `IsOwner` each tick, so it survives.
- Duplicating a room: each copy needs its own outside sign, its lever's door reference repointed, and its icon arrays rewired (proxy fields + `CopyProxyToUdon`).
- Simple indicators: primitive padlock shapes with `Unlit/Color` materials, shadows off.

**Verify:** ClientSim covers lock/unlock, door disable and empty-room unlock; the sync/late-joiner leg needs a Build & Test with 2 clients.

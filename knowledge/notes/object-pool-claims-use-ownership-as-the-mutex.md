---
title: Claimable vehicle/object pools: per-object ownership as the mutex, no central registry
topic: udonsharp-networking
tags: [ownership, vehicles, pool, UdonSynced, playerId, OnPlayerLeft, claim]
summary: Put a small synced claim behaviour on each pooled object and claim by SetOwner → write → RequestSerialization; VRChat guarantees one owner, so there is no race and no contended registry.
---
**When:** a fixed pool of claimable things (submitted cars, boats, props) in a large instance (designed for ~20 objects / 80 players).

**How:**
- The pool size is structural (one scene instance per object), so "max N spawned" needs no counter. Add a live **concurrent-spawn knob** that can be turned down if the instance chugs.
- No central registry with a synced array: 80 clients contend on one object, and `SendCustomNetworkEvent` can't pass arguments. Instead, on each object: editor-set owner name string, `[UdonSynced] int _claimedById`, `[UdonSynced] bool _ownerOnly`. Claim = `Networking.SetOwner` → write fields → `RequestSerialization` → show the object. "One per player" is a free local scan of all claim fields.
- Owner priority is a **reservation, not a lock**: if the submitter is present, their object is greyed out for others; if absent, open to all. Give the submitter a "let anyone use it" toggle.
- Never eject a live driver; a recall flags the object to return to its bay when the driver exits.
- Cleanup, both load-bearing: `OnPlayerLeft` → master clears the claim, hides and respawns the object (otherwise each disconnect permanently removes one from circulation); and an idle timeout for claimed-but-parked objects.
- Typical vehicle systems already refuse ownership transfer while a vehicle is driven (`OnOwnershipRequest` returning false) — reuse that rather than duplicating it.

**Pitfalls:**
- `playerId` increases monotonically, it is not a slot index: never index arrays with it. Size player arrays 128+, since instances can exceed configured capacity.
- Udon exposes only `displayName` (changeable, no persistent ID): reservations are a courtesy, not security; fail open on rename.
- Verify early whether `SendCustomNetworkEvent` reaches a behaviour on a **disabled** GameObject in your setup; if it doesn't, hide pooled objects by toggling renderers instead of `SetActive`.

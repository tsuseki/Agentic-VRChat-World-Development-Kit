---
title: Hidden collectibles: global vs per-player finds, one shared popup, and placement traps
topic: udonsharp-networking
tags: [easter eggs, collectibles, UdonSynced, local, popup, ClientSim, trigger collider]
summary: Mix one global synced catchable with local once-per-player finds, drive one always-active "+N" popup by direct U# calls, and size trigger colliders in local units on scaled imports.
---
**How:**
- **Global catchable** (Manual sync, `[UdonSynced] int _spot`): catcher takes ownership, the object teleports to another of N spots; a sound plays on every client from the spot it fled **from**. Repeatable small reward.
- **Local collectibles** (no sync): once per player per session. Escalating reward per find (`rewardStep × count`) plus a full-set bonus keeps the hunt rewarding. One stash per area spreads players out.
- Finds are silent except a floating "+N" popup: one shared TextMeshPro that floats up ~0.7 m and fades over ~1.4 s.
- Hide them in zones not visible from main gathering areas; verify sightlines with the reviewer.

**Pitfalls:**
- The popup's GameObject must stay **active** (park it out of sight with empty text): a U#-to-U# call into an inactive GameObject silently no-ops.
- A parameterized method (`Show(int, Vector3)`) is called at runtime only by U# direct calls; in-world `SendCustomEvent("Show")` cannot pass arguments and no-ops. Editor tests can drive it through its mangled name (see [udonsharp-parameterised-methods-export-mangled-names](udonsharp-parameterised-methods-export-mangled-names.md)), but a real interact is the end-to-end test.
- ClientSim gives +0 for the first seconds after entering play (still initializing) while `DisableInteractive` still flips — looks like broken wiring. Reset the found flag via `SetProgramVariable` and retest.
- Imported models whose child nodes carry ×100 scale need root scales of ~100–150 to reach real size; a `BoxCollider` trigger on that root must be sized in **local** units (`transform.InverseTransformVector`) or it becomes a 40 m box.
- Check pivot location: a base pivot seats at floorY + 0.005, not floorY + halfHeight.

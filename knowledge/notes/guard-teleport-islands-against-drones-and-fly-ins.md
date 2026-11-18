---
title: Guard private teleport islands against drones and fly-ins with one trigger beyond the far clip
topic: udonsharp-networking
tags: [drones, VRCDroneApi, OnDroneTriggerEnter, TeleportTo, teleport islands, private rooms, privacy]
summary: VRChat drones can fly into private teleport islands; a trigger box around the island that reaches past the far clip, with OnDroneTriggerEnter/Stay and OnPlayerTriggerEnter/Stay sending outsiders (and drones whose owner is not inside) back to the door, keeps islands private without touching legitimate occupants.
sources: [https://creators.vrchat.com/worlds/udon/players/drones/]
---

**Symptom.** Private rooms built as teleport islands (reached only through a door teleport) can be
reached or looked into with VRChat drones, or by players flying in.

**API (SDK 3.10.x).** `OnDroneTriggerEnter/Stay/Exit(VRCDroneApi drone)` fire for trigger colliders;
`drone.GetPlayer()` gives the owner; `drone.TeleportTo(position, rotation)` moves it. Players:
`OnPlayerTriggerEnter/Stay(VRCPlayerApi)` and `player.TeleportTo`.

**Fix / rule.** One trigger `BoxCollider` per island on a layer that doesn't block interaction
raycasts (Ignore Raycast; it collides with the player layers), plus a local script:
- **Interior:** an axis-aligned world box = the island's renderer bounds + a small margin. Anyone
  standing in it came through the door and is left alone.
- **Players:** the local player inside the trigger but outside the interior is teleported to the
  hallway point the island's own exit door uses.
- **Drones:** the local player's drone inside the trigger is teleported there too unless its owner
  is inside the interior (occupants may fly their own drone indoors).
- Each client handles only its own player and drone (`isLocal`); nothing synced.
- Size: reach past the far clip (far + margin on every side, also up and down), so nobody can see
  into the island from outside the zone; keep clear of every normal play area (check with an
  overlap scan of active colliders) and of the island's own arrival points.

**Verify.** Overlap scan: only the island's own objects inside the trigger; door arrival points
inside the interior with margin; nearest walk surface ≥ 0.5 m inside the interior edge. In game:
fly a drone and a player in from outside (lands at the hallway), use the drone from inside
(stays). [Unverified] which layer drones use for trigger detection; if a drone doesn't fire the
events on Ignore Raycast, move the trigger to Default.

**Pitfalls.** If the trigger reaches below the respawn height, a player falling there is
teleported to the hallway instead of respawning. Social privacy only; modified clients can bypass it.

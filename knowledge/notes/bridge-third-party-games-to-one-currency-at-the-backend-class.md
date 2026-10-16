---
title: Integrate third-party minigames with a shared currency at each game's single money-backend class
topic: udonsharp-networking
tags: [UdonSharp, minigames, currency, integration, GameObject.Find, packages, VRCPlayerObject]
summary: Each game usually has exactly one class that reads/writes money; swap that class to the shared purse and the whole game follows.
---
**How:**
- Find each game's single money choke point (a balance component, a chip controller) and make it read/write the shared purse. Owner live-reads/writes the purse; any synced field is just a remote mirror. Games already native to the shared currency need nothing.
- Remove each game's own persistence when the world has a central one, and make "reset" functions clear bets only — never wipe the shared wallet.
- Leave out free-money features that would undermine the world's economy.

**Pitfalls:**
- Shared-currency scripts often locate the purse with `GameObject.Find` — the scene object must keep its exact name.
- An embedded package in `Packages/` that isn't in the VPM manifest is invisible to the Creator Companion; note it for anyone re-resolving packages.
- `VRCPlayerObject` prefabs (per-player spawned objects) must sit once at scene root.
- Some games create per-table assets (RenderTextures, materials) and arrays via their own editor "add table" tool; replicate it rather than duplicating tables by hand.
- Imported meshes with null materials render invisible/magenta; assign the pack's material.
- Parenting under a scaled area root (e.g. localScale 1.4) makes bounds/scale math lossy — world-space position sets are fine.

**Verify:** ClientSim: edit the purse and confirm every game's displayed balance follows within ~1 s.

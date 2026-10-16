---
title: SmartObjectSync is in maintenance mode and its example prefabs break the pickup defaults
topic: udonsharp-networking
tags: [SmartObjectSync, LightSync, VRC_Pickup, proximity, pickupable, object-sync, MMMaellon]
summary: SmartObjectSync works but gets no new features (its successor LightSync is broken), its example pickup prefabs ship proximity 2, and grabbability must be toggled through SmartObjectSync.pickupable, not the VRC_Pickup.
sources: [https://github.com/MMMaellon/SmartObjectSync, https://github.com/MMMaellon/LightSync, https://github.com/MMMaellon/SmartObjectSync/issues/5]
---
**When:** touching synced pickups in a world that embeds SmartObjectSync (3.10.x), or choosing an object-sync package.

**Rules:**
- **Status:** the README marks SmartObjectSync "STABLE, BUT DEPRECATED": it works, no new features. Its successor LightSync is "Currently Broken as of 01/01/2026" and its author points back to SmartObjectSync. Don't migrate.
- **Example prefabs:** shipped pickups (e.g. `Prefabs/DestructibleExample.prefab`) serialize `VRC_Pickup.proximity = 2` (and AutoHold No). Reset proximity to **0.1** (workspace pickup rule) on anything instantiated from them.
- **Owner gating:** the `SmartObjectSync.pickupable` setter rewrites `VRC_Pickup.pickupable` from ownership/theft state, so writing the pickup directly gets overwritten. Toggle grabbability through `sync.pickupable`.
- **Version floor:** keep ≥3.10.0, which fixed "disappearing objects with local-space teleports" on respawn (issue #5).

**Verify:** after placing a pickup from the package, read `VRC_Pickup.proximity` and `AutoHold` in the inspector (or via the Unity MCP `execute_code` tool); in play mode, toggle `pickupable` through the SmartObjectSync component and confirm it sticks after an ownership change.

---
title: SaccFlightAndVehicles: folder-copy install, finding ground vehicles, and seating by wheel anchors
topic: vrchat-sdk-upload-components
tags: [SaccFlightAndVehicles, vehicles, SaccWheel, SkinnedMeshRenderer, respawn, prefab pivot]
summary: Sacc vehicles install by folder copy; their root pivot is not at the wheels and the body is skinned, so seat them from SaccWheel anchors, and each already has a hidden respawn trigger.
sources: [https://github.com/Sacchan-VRC/SaccFlightAndVehicles]
---
**Install:** Plain folder copy, not VPM (no VPM listing exists). Per `Instructions.txt`, extract the `SaccFlightAndVehicles` folder into `Assets` (e.g. `gh release download <tag> -R Sacchan-VRC/SaccFlightAndVehicles`). Update by deleting the old folder outside Unity and dropping in the new one. `.meta` files ship with it, so GUIDs survive and Udon programs import with no missing sources. ~621 MB extracted, ~500 MB of it aircraft; cars are 1-3 MB each, but prefabs cross-reference `AssetFiles/Shared`, so keeping the folder whole is simplest. Budget several minutes of import; the MCP connection may drop and recover.

**Which prefabs are ground vehicles:** grep prefabs for the `SaccGroundVehicle` script GUID. In 1.8.1 only six were: `ST-Baron_Main` (buggy, 34.5k tris), `ST-Shoreline_Main` (60.8k, with `_Drift`/`_Realistic` variants), `ST-Iccarus_Main`, `ST-Thunder_Main`, and two `SaccTankMain*` (~4.9 m wide, 10 `SaccWheel`s). The rest are aircraft.

**Seating trap:** placing by root pivot or `MeshRenderer` bounds lands the car metres off its bay:
- The root is a bare Transform ~3.8 m behind the wheelbase centre; `Rigidbody` + `SaccEntity` live on an offset child.
- The body is a **SkinnedMeshRenderer**, so a MeshRenderer bounds filter finds only the small respawn trigger box. Skinned bounds are also bind-pose inflated (a tank measured ~2.7x its hull), so do not size anything from them.

Seat from the four `SaccWheel` components (suspension top anchors): XZ = anchor centroid; `rootY = groundY + WheelRadius + 0.5*SuspensionDistance - (anchorY - rootY)`. The rigidbody settles exact ride height at runtime. `WheelXXVis`/`WheelXX_SUS` are suspension-arm bones, not hubs; do not derive ride height from them.

**Respawn already exists:** each vehicle has a `VehicleRespawner` trigger post (`SAV_VehicleRespawnButton`, event `EntityRespawn`) whose MeshRenderer ships **disabled**. Check for it before writing a new behaviour. To drive it from a UGUI button, call `SendCustomEvent("KeyboardInput")` on it, which calls `Interact()` and keeps the prefab's sound/animator hooks; calling `SaccEntity.EntityRespawn` directly bypasses them.

**Structure:** body colliders ship on layer Walkthrough (never block players); seats are real `VRCStation`s; Sacc also ships its own race course/scoreboard system (`SaccRaceCourseAndScoreboard`, `SaccRacingTrigger`, `RaceCheckpoint`) with a trigger inside each vehicle, disabled until a race is selected.

**Verify:** A top-down render with bay lines visible; numeric height checks can pass while the car overhangs its bay. When photographing one vehicle for a UI portrait, hide neighbouring vehicles and their boards entirely, and assert no stray flat panels remain in range rather than trusting `SetActive(false)`.

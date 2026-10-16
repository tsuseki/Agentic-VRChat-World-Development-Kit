# Changelog

## Unreleased

- `WorldAudit`: a MeshCollider on a GameObject named `ContainShell` outside any prop root (a
  containment guard shell: upright slabs whose thin tops add up to walkable-angle area) is no longer
  a `WALKABLE_MESHCOLLIDERS` finding; such shells are counted on an informational
  `[CONTAINMENT_SHELLS]` line. Every other floor-like MeshCollider is still flagged.

## 0.3.0

- `WorldAudit`: second allowed prop collider. A `BoxCollider` on a GameObject named `SolidCollider`
  (big furniture: dining/kitchen tables, counters, cabinets, wardrobes) that is active, enabled and
  not a trigger is not a finding; such colliders are counted on a new informational
  `[SOLID_FURNITURE_COLLIDERS]` line. A disabled/inactive `SolidCollider`, a trigger, or a non-Box
  collider with that name is a `PROP_COLLIDERS` finding.

## 0.2.0

- `WorldAudit`: one allowed prop collider. A `BoxCollider` on a GameObject named
  `LieDownCollider` (the top surface of a bed, couch or cuddle platform) that is inactive or has its
  collider disabled is not a finding; such colliders are counted in a new informational
  `[LIE_DOWN_COLLIDERS]` line ("lie-down colliders: N, all off by default"). An enabled/active
  `LieDownCollider`, a trigger, or a non-Box collider with that name is a `PROP_COLLIDERS` finding.
- `ZFightRender`: the tie tolerance now models VRChat PC's measured depth buffer (Unity 2022.3 D3D11:
  32-bit float, reversed Z) instead of a 24-bit fixed-point buffer at near 0.01. New default
  `tol = max(0.05 mm, 2 * (2^-24 * C + 2^-23 * d))` with `C` the camera's largest per-axis
  |coordinate|; independent of the near clip. The old model is kept as
  `DepthFormat = ZDepthFormat.Fixed24` (uses `NearClip`, plus the same position term).
  `Tolerance(d)` gains an optional `cameraCoord` argument. The report states the model and a
  per-shot `tol@20m`. A 3 mm gap seen from 20 m and a 0.5 mm gap seen from 100 m are no longer
  flagged on PC.
- `Util.CapCam()` finds the existing `__CapCam__` after a scene change instead of requiring a valid
  scene, so it is not duplicated.

## 0.1.0

First release.

- `JobRunner` / `AgentJob`: time-sliced jobs on `EditorApplication.update` (150 ms budget per tick;
  each `Status()` poll also runs one slice), `Status`, `Cancel`, `RunBlocking`.
- `ZFightScan`: geometric coplanar-overlap scan, ported from the world-pipeline skill's
  `zfight_scan.cs` script (now removed) and reworked:
  - the plane-bucket hash is replaced by a hierarchical uniform grid. The old key used the plane
    offset n·p, so two coplanar triangles far from the origin whose normals differ slightly landed
    in distant buckets and were missed (a 0.05° tilt 600 m out moved the offset by about 0.5 m).
    The opposite-facing search also skipped the normal-neighbour buckets, and the single-axis sweep
    went O(n²) on large coplanar sets;
  - coplanarity tests all six vertices against both planes instead of one centroid;
  - fully duplicated faces inside one mesh are reported with `includeSelf` (faces that share only
    one or two vertices are neighbours and are skipped);
  - different LOD levels of one LODGroup, ShadowsOnly renderers and EditorOnly objects are skipped;
  - time-sliced instead of a 7 s deadline, so it never stops with a partial result.
  Measured headless on 2022.3.22f1 (EditMode test, D3D11): two coplanar 50 x 50 m grids of 100,352
  triangles each (200,704 total, 2.29 M narrow tests) completed in 4.1 s over 27 slices, longest
  slice 158 ms, reported 2499.06 m² of the exact 2500 m² overlap.
- `ZFightRender`: render-based detector with per-renderer ID passes and a depth-tie tolerance
  modelled on a 24-bit depth buffer at VRChat's 0.01 m near clip; reports renderer pairs and writes
  mask PNGs.
- `WorldCapture`: PNG captures from one persistent DontSave `__CapCam__`.
- `PerfSample`: play-mode frame sampling with optional renderer disabling for attribution; JSON out.
- `WorldAudit`: stations, pickups, realtime/mixed lights, leftover `__name__` objects, walkable
  MeshColliders, prop colliders, static renderers without UV2, uncompressed textures.

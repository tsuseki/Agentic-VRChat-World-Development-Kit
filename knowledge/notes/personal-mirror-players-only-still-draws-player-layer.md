---
title: Players-only personal mirrors still draw world objects on the Player layer; hide areas with a sky-wall
topic: vrchat-sdk-upload-components
tags: [personal mirror, players only, Show World, far clip, Player layer, teleport islands, sightlines, skybox occluder]
summary: The VRChat personal mirror with "Show World" off still renders world geometry on layer 9 (Player), so a skybox-painted, depth-writing wall on that layer, placed beyond the far clip of every normal view, hides distant players from players-only mirrors without being visible anywhere else.
---

**Symptom.** Players in a private teleport island (a suite floating ~300 m from the main building)
saw the main-building players in their VRChat personal mirror. Walls, shells and occluders don't help:
the personal mirror's "Show World" toggle (Settings > Mirrors) renders players only, so world
geometry vanishes from it and the far players stay.

**Measured (two local Build & Test desktop clients, players-only and world-on mirrors).**
- The desktop personal mirror follows the screen camera's far clip: far 4 m hid a player 6 m away
  and kept one 3 m away. A Player-layer cull distance on the screen camera changed nothing.
  At far 150 m a player ~330 m away was not drawn in the mirror; at far 400 m it was.
- The sighting itself happened in VR with far 150 m and was **not** reproduced on desktop.
  [Unverified] VR mirror rendering may not honour the far clip; treat the far clip alone as
  insufficient.
- A black quad on layer 9 (Player), no collider, **did** show in a players-only personal mirror.
  Players-only mode drops the world layers, not the Player layer.

**Fix / rule.**
1. Lower the world's reference-camera far clip to what the world needs (here the main building's
   diagonal plus margin: 80 m for a ~66 m footprint).
2. Between the island and the main area, place a two-sided quad on the **Player** layer that paints
   the skybox seen behind it and writes depth before avatars: shader with `Queue=Background+1`,
   `ZWrite On`, `Cull Off`, colour = the skybox shader's own lookup of
   `normalize(worldPos - _WorldSpaceCameraPos)` (same texture, rotation, exposure, dimming as the
   sky material). Normal views and world-on mirrors see plain sky; players-only mirrors see a sky
   patch where the far players were. No collider, shadows and probes off, not static.
3. Put it **beyond the far clip of every normal viewpoint** (island and main area), so it is culled
   everywhere it isn't needed and costs nothing. That needs the island-to-main gap to exceed twice
   the far clip, which is another reason to lower the far clip.
4. Size it from the island's eye positions to the main area's player volume (rays from the island
   corners to the far corners) with margin.

**Verify.** Two clients: observer in the island with the personal mirror, Show World off, aimed so
the main area is in the reflection; subject at the main area. With the far clip forced above the
wall distance (simulating a mirror that ignores it), a present/absent diff must find the subject
without the wall and nothing with it, and the mirror with Show World on must look unchanged.
In VR the owner checks once, since VR menus need controllers.

**Pitfalls.** A plain black wall is visible as a black patch in every players-only mirror facing it,
and in world-on mirrors that draw beyond the far clip. The skybox lookup must match the sky shader
exactly or the patch shows an edge.

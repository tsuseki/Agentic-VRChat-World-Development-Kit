---
title: Runtime writes to U# serialized arrays can leak into the saved scene
topic: udonsharp-networking
tags: [UdonSharp, play mode, inspector, proxy, serialized arrays, InitializeOnLoad, scene save]
summary: If a UdonSharp component's inspector is drawn during play mode, runtime values written into its serialized arrays get copied back onto the C# proxy and can be saved into the scene; snapshot and restore them around play mode.
---
**Symptom:** A behaviour that deliberately writes runtime data into serialized arrays (e.g. writing the claiming player's display name into a role roster so name matching works in ClientSim) ends up with a tester's name in the in-memory proxy, silently replacing authored data. A domain reload may discard it, so it can also look like it never happened.

**Cause:** When the component's inspector is drawn while the game runs, UdonSharp copies the Udon heap back onto the C# proxy, and the next scene save writes the runtime value into the shipped data.

**Fix / rule:** Add an `[InitializeOnLoad]` editor guard that snapshots the affected arrays on `PlayModeStateChange.ExitingEditMode` and restores them on `EnteredEditMode`, logging any diff. After play sessions that exercise those writes, check the console for the guard's log. Never hand-fix contaminated data while still in play mode; exit first and let the guard restore.

**Why:** Authored lists such as a cast or whitelist are often locked well before an event, and nothing in the world flags a quietly replaced entry until it matters.

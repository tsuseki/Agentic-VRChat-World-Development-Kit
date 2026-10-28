---
title: A leftover __ExportTerrain object from an interrupted Bakery export makes every later export throw ArgumentOutOfRange
topic: lighting-baking
tags: [Bakery, terrain, ExportScene, ArgumentOutOfRangeException, domain reload, crash recovery]
summary: When a Bakery export is interrupted after it converts terrains, it leaves `Terrain/__ExportTerrainParent/__ExportTerrain` in the scene, the next save keeps it, and every later export fails in `ftBuildGraphics.ExportScene` with "Index was out of range" because the stale object's parent is not in that run's terrain list.
sources: in-house
---
**When:** a Bakery render in a scene with a Unity Terrain fails with `Error exporting scene` / `ArgumentOutOfRangeException: Index was out of range … Parameter name: index`, and the problem continues after you change Bakery settings (Unwrap on or off) or restart the editor.

**Symptom:** the Console shows `Exception caught: System.ArgumentOutOfRangeException` from `ftBuildGraphics.cs:8504`. Editor.log has the real throw site, `ftBuildGraphics+<ExportScene>.MoveNext … ftBuildGraphics.cs:8296` (Bakery 1.98). The lightmap output folder only gets the `_probes.asset`. Under the Terrain there is a `__ExportTerrainParent` with a `__ExportTerrain` child carrying a mesh of about heightmapResolution² vertices that is not saved as an asset.

**Cause:**
- `ConvertTerrain` builds the temporary `__ExportTerrainParent/__ExportTerrain` objects at the start of the export. Bakery deletes them only when the export finishes normally.
- A crash, or a domain reload partway through the export (a "forced synchronous recompile" from a pending script change), leaves them in the scene with ordinary hide flags. The next save writes them to disk.
- On the next export, Bakery gathers the stale `__ExportTerrain` together with the freshly converted one. It finds a terrain by name with `terrainObjectList.IndexOf(obj.transform.parent.gameObject)`. That returns −1 for the stale parent, so `terrainObjectToActual[-1]` throws.
- Copying the scene copies the leftover too.

**Fix / rule:**
- Before every Bakery render, delete every GameObject whose name starts with `__ExportTerrain` (look under each Terrain, including inactive objects), mark the scene dirty, and save.
- Make sure no script compile is pending before you start, so a domain reload can't interrupt the export.
- After a failed export, clean up again before retrying.

**Verify:** search the saved `.unity` for `m_Name: __ExportTerrain`: there must be 0 matches before a bake and after a finished one.

**Related:** [bakery-unwrap-registry-rewrites-shared-models.md](bakery-unwrap-registry-rewrites-shared-models.md).

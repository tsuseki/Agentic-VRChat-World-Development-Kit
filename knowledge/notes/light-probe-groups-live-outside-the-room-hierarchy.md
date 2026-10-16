---
title: Find LightProbeGroups scene-wide and judge coverage from transformed probe positions
topic: probes-reflection-and-light
tags: [light-probes, LightProbeGroup, coverage, bounds, duplicates]
summary: Probe groups are usually parented under a lighting root, so per-room GetComponentsInChildren finds none, and a group transform-based AABB is meaningless because probe positions are local.
---
**Symptom:** A per-room `GetComponentsInChildren<LightProbeGroup>()` returns 0, so new groups get built - duplicating existing ones that live under a scene-level probes root. Duplicate co-located probes waste bake time and crowd the tetrahedralisation.

**Cause:** Probe groups are organised by the lighting rig, not the room hierarchy. And `probePositions` are **local**; the group transform often sits at the world origin, so an AABB seeded from `transform.position` reports garbage.

**Fix / rule:**
- Enumerate with `FindObjectsOfType<LightProbeGroup>()`; per-room containment proves nothing.
- Judge coverage by transforming every probe position to world space and taking min/max.

**Verify:** Compare those world extents against the room extents. In the example the existing groups stopped 3 m short, leaving both beds and a wall of furniture outside probe coverage - probe-lit props there sampled whatever tetrahedron was nearest.

Related: [light-probe-placement-raycast-grid](light-probe-placement-raycast-grid.md)

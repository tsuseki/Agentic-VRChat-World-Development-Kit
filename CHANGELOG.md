# Changelog

Semantic versioning, one git tag `vX.Y.Z` per release; the current version is in `VERSION`.

## 0.2.0 — 2026-11-03

First versioned release. It covers everything since the initial public release (tagged `v0.1.0`,
2026-10-16); the notes below list the changes made since the last push.

### Concept art now binds what is in each area, not only its feel

Before, images set only mood, palette, materials, lighting and density. A structure pass could
ignore the per-area concept art and build every area from the same generic block kit, so
every floor came out the same. Now:

- **Images are content and feel references, not blueprints.** They decide *what is there*
  (structure and object types, silhouettes, signature pieces) as well as the feel. Exact positions,
  proportions and layout still come from the plan and greybox.
- **New WORLD.md section "Area references (binding per-area targets)"**: one row per area with its
  target image(s), signature pieces, the user's pick and the user's exact words. Every B.2, C.1 and D.1
  brief copies its row. Template updated.
- **Always build from concept art**: each area gets a blockout, captures from several angles,
  concept art over those captures, then a pick, all before the area is built.
- **Several concept variants per view.** The user picks. If the user leaves a pick open,
  `dressing-reviewer` decides it in a new **CONCEPT PICK** mode. The built area matches the image's
  style but is not a copy of it. Area folders get descriptive names.
- **Reviewers check content match and distinctness**: `layout-reviewer` (for structures beyond plain
  massing) and `dressing-reviewer` check that each area contains what its image shows and doesn't
  look like its neighbours.
- `dressing-reviewer` now reviews whatever a C pass placed (inner buildings, machines, set pieces,
  shell finish, furniture, dressing), not only furniture passes.
- `asset-finder` and `blender-modeler` match the picked image's object type and silhouette.
- New knowledge note `concept-art-binds-content-not-just-feel.md` (the failure where every floor
  came out identical) and a matching line in `lessons-verification.md`.

### Spatial design: structures inside halls

- **No outdoor roofs on buildings that stand indoors** (no pitched or gabled roofs, pediments or eaves).
  The top of such a structure is a usable area (terrace, garden, deck, lookout, catwalk), or the
  structure is built into the ceiling.
- In tall halls, tie the big structures to the floor, the ceiling and the walls, and join neighbouring
  structures with bridges.
- No outdoor building types indoors, and nothing that needs open sky.

### Movement between floors

- **Stairs come first:** every floor can be reached on foot, and big worlds get at least 2 walking routes
  between each pair of main floors.
- **VR stair comfort** (spatial-design §5.6): long straight flights, no spiral stairs, no short zigzags.
- **Teleport lifts** have a button per floor. **Ladders are click-to-teleport only**: Interact at one end
  takes you to the other end. Players never climb them.
- New template `templates/udon/TeleportDoor.cs.txt`: one local Interact → `TeleportTo` script shared by
  doors, lifts and ladders (3 m interaction distance, optional sound effect). Its clickable part has a
  trigger collider, which never blocks movement.
- Rules in `world-builder` and the world-pipeline C.2 row.

### Agent models

- `world-architect`, `layout-reviewer`, `dressing-reviewer` and `final-reviewer` run on Opus.
- `perf-optimizer` and `blender-optimizer` run on Sonnet.

### Docs

- `review-protocol.md`, `intake.md`, `PIPELINE-LAYOUT.md` and `pipeline.html` updated to match.

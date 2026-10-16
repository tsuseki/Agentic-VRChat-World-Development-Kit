# Hard rules — <workspace>

These stay in force for the whole session. Background and rationale live in `.omp/AGENTS.md`.

1. **Read the project's own `AGENTS.md` before editing that project.** Per-project files
   (`<project>/AGENTS.md` in each world project) do not auto-load from the workspace root.
   Read `DESIGN.md` and `TASKS.md` too when they exist.

2. **No colliders on small props; big furniture is solid.** Small furniture, decoration and clutter
   are walked through: chairs, stools, couches, armchairs, coffee/side/bedside tables, decor. Add a
   collider only where the player must not pass, prefer one `BoxCollider`, never a `MeshCollider` on
   anything walked on. Stairs get one smooth rotated ramp box, never per-tread collision. Anything
   created from a Unity primitive: destroy its auto-added collider.
   **Big furniture gets a solid collider:** dining and kitchen tables and other big tables, kitchen
   counters and islands, bar counters, cabinets, sideboards, dressers, wardrobes, bookcases and
   appliance-sized pieces get one always-on child `SolidCollider` (one `BoxCollider`) over their
   footprint, floor to top surface, so players can't walk through and pickups rest on them.
   **Lie-down colliders:** beds, couches and lie-on furniture get a top-surface child
   `LieDownCollider` (one `BoxCollider`), disabled by default and switched on only by the world's
   single lie-down colliders toggle (Udon). Requested pickups keep their own tight collider.

3. **Never add a seat station unless the user explicitly asks.** No `VRC_Station`/`VRCStation`
   on any chair, sofa, bench, stool, bed, jacuzzi or prop, in any world. Strip stations off
   imported prefabs. Never re-add one that was removed. See `.omp/AGENTS.md`.

4. **The stage reviewers are the gate, not a courtesy.** Nothing built, generated, placed, textured
   or lit is "done" until the matching reviewer (`layout-` / `dressing-` / `final-reviewer`)
   returns SHIP IT (no blocker or should-fix finding, score ≥ 8). Your own screenshots and numbers
   do not count. Brief it with the stage, art direction, exact target and concerns. NEEDS WORK /
   MINOR FIXES is your next task list, not a report to relay. Whole worlds follow the
   `world-pipeline` skill. Exception: A.3 shell layouts, A.3 style-track images and style rounds are accepted by the
   **user's pick**; layout-reviewer only ranks them, and there is no SHIP IT loop before A.4.

5. **Drive the open Unity Editor through the Unity MCP, never the files.** Use the Unity MCP
   `execute_code` tool (and friends). Never hand-edit an open scene's YAML — the
   editor's in-memory state clobbers it. Scripted hierarchy edits need `MarkSceneDirty` before
   saving. After any script change, read the console and check for `error CS` before proceeding.

6. **Bake reflection probes immediately after every lighting bake.** A lightmap bake invalidates
   them and no luminance metric catches it. Probes only capture renderers flagged
   `ReflectionProbeStatic` — a different flag from `ContributeGI`.

7. **These git repos are local-only backups. Never push.** Commit a checkpoint after a
   significant chunk of work; `git add` can take minutes, so run it backgrounded.

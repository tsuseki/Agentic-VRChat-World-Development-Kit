# Start a new world

Assumes [bootstrap.md](bootstrap.md) is done on this machine.

1. **Create the project** in ALCOM/VCC: *Unity 2022 World* template, Unity 2022.3.22f1. Copy
   [.omp/scripts/unity-world.gitignore](../scripts/unity-world.gitignore) to its root as `.gitignore`,
   `git init`, commit.
   **Agent without the launcher UI:** copy `%LOCALAPPDATA%\VRChatCreatorCompanion\VRCTemplates\World`
   to the new folder (delete its `package.json` and `README.md`, set `productName` in
   `ProjectSettings/ProjectSettings.asset`), then bring the SDK current with
   `vrc-get install -y -p <project> com.vrchat.worlds <version>` **and**
   `vrc-get install -y -p <project> com.vrchat.base <version>`: the template pins `com.vrchat.base`
   to an old `~3.x` range that otherwise stays in the manifest. Register it with the launcher by
   appending the path to `userProjects` in `%LOCALAPPDATA%\VRChatCreatorCompanion\settings.json`
   (launcher closed, file backed up); ALCOM imports it into its project list on the next start.
2. **Install MCP for Unity** (`python .omp/scripts/install-unity-mcp.py <project>` while closed), open the
   project, install Roslyn and mark its DLLs Editor-only ([bootstrap.md §3](bootstrap.md#3-wire-it)).
3. **Install the agent tools package**: add
   `"com.awdk.agenttools": "file:<workspace>/.omp/unity-package/com.awdk.agenttools"`
   to `Packages/manifest.json`, let Unity compile, confirm the console has no `error CS`.
4. **Lightmapper**: Bakery if the user owns it; otherwise GLIM (free); Progressive GPU only when neither
   works ([bootstrap.md §3](bootstrap.md#3-wire-it)). **VRC Light Volumes** (`red.sim.lightvolumes`
   3.x) in every world: add the VPM listing `https://redsim.github.io/vpmlisting/index.json` in
   VCC/ALCOM and add the package to the project. The volumes are laid out over every playable area
   in D.1 and bake with the full render; they light everything that isn't lightmapped.
4b. **Jumping** (every world has it; VRChat's default jump impulse is 0): copy
   [.omp/templates/udon/PlayerMovementSettings.cs.txt](../templates/udon/PlayerMovementSettings.cs.txt) to
   `Assets/_World/Udon/PlayerMovementSettings.cs` and put one on an object at the scene root (UdonSharp
   `AddUdonSharpComponent`). Do it now, on day one; no one asks about it. `WorldAudit` reports a world
   without it as `NO_JUMPING`.
5. **Brief**: copy [.omp/templates/WORLD.template.md](../templates/WORLD.template.md) to the project root
   as `WORLD.md` (the code block inside it is the file body). Create the project's own `AGENTS.md`
   with machine facts (local asset library path, Unity instance name, owned paid packages).
6. **Start the pipeline**: tell the agent "make me a world: <description>" and give it whatever you
   have (a design doc, reference pictures). It loads
   [.omp/skills/world-pipeline/SKILL.md](../skills/world-pipeline/SKILL.md), gathers information
   from what you supplied (asking only about gaps), fills `WORLD.md`, and runs phases A–D: you
   decide the concept, the boards and the Design Lock, then the agents build to a ready-to-upload
   world.
7. Commit a checkpoint after each stage (A.1–D.4; local only unless you choose otherwise).

## Keeping a project's packages up to date

- **When:** between stages, never during a bake or a build stage. Commit a checkpoint first.
- **Check:** `vrc-get update` (refreshes the listings; unreachable third-party listings print
  `e: fetching remote repo` and are harmless), then `vrc-get outdated -p <project>`.
- **Upgrade** with Unity closed: `vrc-get upgrade -y -p <project> <package id>` (or ALCOM *Manage
  Project*). Stay inside the VRChat SDK 3.x line, keep `com.vrchat.base` and `com.vrchat.worlds` on
  the same version, and read Light Volumes' changelog before a major version jump (its bake
  workflow changes between majors). Reopen, wait for compile, read the console: zero `error CS`
  before any other work.
- **Never upgrade Unity** (2022.3.22f1 is the VRChat version) and never edit `vpm-manifest.json` by
  hand.
- **MCP for Unity** stays on the tag pinned in `.omp/scripts/install-unity-mcp.py`; bump the tag
  there and the server version in the host's MCP config together ([hosts.md](hosts.md)).
- **AWDK agent tools** point at the workspace copy (`file:` dependency), so they update with
  `git -C .omp pull`.
- **Bakery** is a paid Assets package, not VPM: update it through Bakery's own patch check or by
  re-importing the owner's newer `.unitypackage`, never by copying an older project's folder over
  a newer one.

# Start a new world

Assumes [bootstrap.md](bootstrap.md) is done on this machine.

1. **Create the project** in ALCOM/VCC: *Unity 2022 World* template, Unity 2022.3.22f1. Copy
   [.omp/scripts/unity-world.gitignore](../scripts/unity-world.gitignore) to its root as `.gitignore`,
   `git init`, commit.
2. **Install MCP for Unity** (`python .omp/scripts/install-unity-mcp.py <project>` while closed), open the
   project, install Roslyn and mark its DLLs Editor-only ([bootstrap.md §3](bootstrap.md#3-wire-it)).
3. **Install the agent tools package**: add
   `"com.awdk.agenttools": "file:<workspace>/.omp/unity-package/com.awdk.agenttools"`
   to `Packages/manifest.json`, let Unity compile, confirm the console has no `error CS`.
4. **Lightmapper**: import Bakery if the user owns it; otherwise Progressive GPU.
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

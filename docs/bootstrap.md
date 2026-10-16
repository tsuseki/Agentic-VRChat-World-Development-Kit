# Bootstrap: set up a machine from zero

Point a capable agent here to stand up everything a world needs on a bare machine: install,
wire, verify. One-time per machine; a second world is [new-world.md](new-world.md). Structure
modelled on [Atelier's bootstrap](https://github.com/Ryan6-VRC/atelier/blob/main/docs/bootstrap.md).

The steps name *what* must exist, not an OS-specific recipe; resolve host specifics as you go.
Ask the user only for things that need them (licence sign-in, purchases, paths to their assets).

## 1. Prerequisites

- **git** on `PATH` (Unity fetches the MCP package over a git URL), plus **git-lfs**.
- **Unity Hub + Unity 2022.3.22f1**: the VRChat-supported version, never upgraded. Sign in and
  activate a (free personal) licence first, or the first launch stalls on a licence modal that
  looks like the editor is still loading.
- **VRChat Creator Companion (VCC)** or **[ALCOM](https://vrc-get.anatawa12.com/alcom/)**, and the
  **[vrc-get](https://github.com/vrc-get/vrc-get)** CLI. ALCOM/VCC create projects and bundle the
  community repo list; vrc-get resolves and installs packages from the shell.
- **Python 3.10+** (kit tools) and **[uv](https://docs.astral.sh/uv/)** (`uvx` runs the MCP server).
- **Your agent host** with MCP support (see [hosts.md](hosts.md)).
- Optional: **Blender 4.x+** for custom props; **Bakery** (paid, [geom.io/bakery](https://geom.io/bakery/wiki/index.php?title=Manual))
  for lightmaps. Without Bakery, worlds bake with Unity's Progressive GPU lightmapper.

## 2. Create a world project

In ALCOM/VCC: *New project → Unity 2022 World* template, Unity 2022.3.22f1, in a folder of the
user's choice. Or open an existing world project. Confirm `Packages/vpm-manifest.json` contains
`com.vrchat.worlds` (UdonSharp ships inside it; never install it separately).

```
vrc-get resolve -p <project>          # restore packages from the manifest
vrc-get install -p <project> <id>     # add a package (the verb is install)
```

`install` may print a benign `error reading directory … (os error 3)` on success. `resolve`
reinstalls locked packages, so don't run it as a health check under a live editor.

Copy [.omp/scripts/unity-world.gitignore](../scripts/unity-world.gitignore) to the project root as
`.gitignore`, then `git init` and commit (local only).

## 3. Wire it

**MCP for Unity** ([CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp), MIT). With the
project **closed**: `python .omp/scripts/install-unity-mcp.py <project>` adds the pinned package to
`Packages/manifest.json`. With it open: Package Manager → *Add package from git URL* with the URL
from `.omp/scripts/install-unity-mcp.py`. Then *Window → MCP for Unity → Configure* your client (or add
the server to your host's MCP config by hand, see [hosts.md](hosts.md)). With several editors
open, every session's first Unity call is `set_active_instance` with the exact `Name@hash`.

**Roslyn for `execute_code`** (per project, once). Without it `execute_code` silently falls back to
a C# 6 compiler. *Window → MCP for Unity → dependencies → Roslyn → Install* downloads DLLs to
`Assets/Plugins/Roslyn/`. Then mark each DLL **Editor only** (Inspector → platforms → Editor,
Apply); the installer leaves them "Any Platform", which breaks world builds.

**Agent tools package.** Add to the project's `Packages/manifest.json` `dependencies`, pointing at
the workspace copy in `.omp/unity-package/`:

```json
"com.awdk.agenttools": "file:<workspace>/.omp/unity-package/com.awdk.agenttools"
```

Use the absolute path with forward slashes. API: [unity-tools.md](unity-tools.md).

**Editor preferences for an unattended editor** (per machine; `EditorPrefs`):

- *General → Interaction Mode: No Throttling* (`InteractionMode` = 1), or an unfocused editor idles.
- *General → Script Changes While Playing: Recompile After Finished Playing*
  (`ScriptCompilationDuringPlay` = 1), or a file write from another agent reloads a running play
  session and discards its state.
- *Asset Pipeline → Auto Refresh* on; it still fires only on focus, so an agent that wrote files
  calls the MCP `refresh_unity` tool itself.
- Console *Error Pause* off.
- Project side: *Player → Run In Background* on.

**Lightmapper.** Bakery (if the user owns it): import their `.unitypackage` through Unity, then
follow `.omp/skills/bakery-light-baking/SKILL.md`. Otherwise set *Lighting → Lightmapper: Progressive
GPU*; the pipeline's D.1 Lighting stage supports both.

**Blender MCP (optional).** [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp):
install the server (`uvx blender-mcp`) in your host's MCP config, install and enable the add-on in
Blender, start its bridge. Only `blender-modeler` needs it; it can also run Blender headless.

## 4. Verify

- The MCP `read_console` tool returns, and the console has **zero `error CS`** entries. A connected
  bridge over a project full of compile errors is not "working".
- `execute_code` with `return Application.unityVersion;` returns `2022.3.22f1`, and reports the
  `roslyn` compiler.
- `return AWDK.AgentTools.WorldAudit.Run();` returns a report (package compiled).
- `return UnityEditor.EditorPrefs.GetInt("InteractionMode");` returns `1`.
- Lighting window shows Bakery or Progressive GPU.

MCP config written mid-session usually isn't live until the host restarts.

## 5. Continue

For the project created in step 2, continue at [new-world.md](new-world.md) **step 5**: create
`WORLD.md` from the template and the project's own `AGENTS.md` (local asset library path, Unity
instance name, owned paid packages). Hard rule 1, asset-finder and the asset rules all read that
file, so don't start the pipeline without it.

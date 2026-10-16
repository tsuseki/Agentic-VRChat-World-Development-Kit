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
- **Blender 4.2+** for custom props (run headless by the kit). Lightmapper: **Bakery** (paid,
  [geom.io/bakery](https://geom.io/bakery/wiki/index.php?title=Manual)) if owned, else **GLIM**
  (free); Unity's Progressive GPU is the last fallback. Generation services are chosen in §4.

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

**Lightmapper**, best first:

1. **Bakery** if the user owns it: import their `.unitypackage` through Unity.
2. Else **GLIM** (free): add the VPM listing <https://z3y.github.io/vpm-package-listing/> in
   VCC/ALCOM and install it into the project; install Open Image Denoise and set
   `OpenImageDenoise_DIR` (steps in `.omp/skills/bakery-light-baking/SKILL.md` "Without Bakery:
   GLIM"), then restart Unity Hub and Unity.
3. Else *Lighting → Lightmapper: Progressive GPU*.

The pipeline's D.1 Lighting stage supports all three.

**Blender** runs headless (`blender -b`) for every kit step: install it and put its path in
`.omp/local/tools.json` (§4). No add-on is needed. The Blender MCP add-on
([blender.org/lab/mcp-server](https://www.blender.org/lab/mcp-server/)) is optional, for live
sessions the user drives.

## 4. Connect your tools

The kit calls fixed tool names (`image-gen`, `image-edit`, `image-to-3d`, `blender`); the user
picks what runs behind each. Full reference: [tools.md](tools.md). Walk the user through it:

1. Copy `.omp/local.example/` to `.omp/local/` if it doesn't exist yet.
2. **Ask the user which of these they already have or will pay for**, one question per tool,
   paid options first because they give better results:
   - images (`image-gen`, `image-edit`): an OpenAI API key (GPT Image), a Google Gemini API key
     (Nano Banana), a fal.ai or OpenRouter key in the Unity MCP, or an image tool their agent host
     or subscription already provides;
   - image-to-3D: a Tripo or Meshy API key, or a web studio subscription they use by hand;
   - the lightmapper (above): Bakery owned or not.
3. **Offer the free fallback for every tool**, even when a paid one is connected: ComfyUI with
   Qwen-Image-2512 / Qwen-Image-Edit-2511 for images and TRELLIS.2 for image-to-3D need a strong
   local GPU and 15–40 GB of downloads, so ask before installing them, and say what the GPU in this
   machine can run.
4. Have the user store each key as a user environment variable (`OPENAI_API_KEY`,
   `GEMINI_API_KEY`, `TRIPO_API_KEY`, `MESHY_API_KEY`) or a one-line file under `.omp/local/`.
   Never ask them to paste a key into the chat, and never write one into a tracked file.
5. Write `.omp/local/tools.json`: for each tool, the paid backends first, then the free one. Set
   `confirm_spend: true` on pay-per-use backends the user wants to approve one by one. Set
   `blender.path`.
6. Run `python .omp/scripts/tool.py check`; every configured row must be `ok`, `key present` or a
   hand-off. Then, with the user's OK for the small cost, generate one test image per image backend
   (`--backend <name> --prompt "a red ceramic mug on a plain grey background"`) and look at it.
   Skip paid image-to-3D tests unless the user asks.
7. Record the choices (no keys) in `.omp/local/config.md`.

A tool left without any backend makes the stages that need it ask the user instead (style rounds
show reference collages; props come from asset libraries or Blender).

## 5. Verify

- The MCP `read_console` tool returns, and the console has **zero `error CS`** entries. A connected
  bridge over a project full of compile errors is not "working".
- `execute_code` with `return Application.unityVersion;` returns `2022.3.22f1`, and reports the
  `roslyn` compiler.
- `return AWDK.AgentTools.WorldAudit.Run();` returns a report (package compiled).
- `return UnityEditor.EditorPrefs.GetInt("InteractionMode");` returns `1`.
- The Lighting window (or GLIM's *Tools → Glim* menu) shows the chosen lightmapper.
- `python .omp/scripts/tool.py check` passes (§4).

MCP config written mid-session usually isn't live until the host restarts.

## 6. Continue

For the project created in step 2, continue at [new-world.md](new-world.md) **step 5**: create
`WORLD.md` from the template and the project's own `AGENTS.md` (local asset library path, Unity
instance name, owned paid packages). Hard rule 1, asset-finder and the asset rules all read that
file, so don't start the pipeline without it.

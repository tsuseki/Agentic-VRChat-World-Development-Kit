# Start here if you have never used an AI agent

AWDK doesn't build anything by itself: it is a set of instructions an AI coding agent reads. You
install an agent, point it at the kit, and from then on you talk to it in plain language ("make me
a cosy cabin world"); it drives Unity and Blender for you and asks when it needs a decision.

## What you need

| Item | Cost | Why |
|---|---|---|
| A Windows PC; an NVIDIA graphics card helps (see "Images" below) | — | Unity, Blender and local image generation run on it |
| **Claude Pro** (try it out, one small room) or **Claude Max** (whole worlds) | $20 / $100 a month | Claude Code is the agent. The free Claude plan doesn't include it |
| Unity Hub, Unity 2022.3.22f1, ALCOM (or VRChat Creator Companion), Blender, Python, Git | free | The agent installs and checks these with you |
| ComfyUI (optional) | free | Local image generation for concept art and textures |

Usage limits are the real constraint: building a world takes a lot of agent work. On Pro, expect
to work on one area per session and to wait for the limit to reset.

## Steps

1. Buy the Claude plan at <https://claude.ai>, then install **Claude Code** from
   <https://claude.com/claude-code> (the VS Code extension is the friendliest way in) and sign in
   with the same account.
2. Make a workspace folder for your worlds, e.g. `C:\VRChatWorlds`, and put the kit in it as `.omp`:
   `git clone https://github.com/tsuseki/Agentic-VRChat-World-Development-Kit.git .omp`
   (no Git yet? Download the ZIP from that page and unpack it as `.omp`).
3. Open the workspace folder in Claude Code and say:
   *"Read .omp/AGENTS.md, run `python .omp/scripts/install.py --host claude`, then set up this
   machine by following .omp/docs/bootstrap.md. I'm new to this, explain each step before you do it."*
   It walks you through Unity, ALCOM, Blender, the Unity connection (MCP) and the image tools, and
   only stops for things you have to click or sign in to yourself.
4. Restart Claude Code once it says the setup is done (new connections load at startup).
5. Say *"Make me a VRChat world"* and describe it. The agent asks about anything it still needs
   and shows you choices (layouts, styles) to pick from as it goes.

## Images without a subscription

Claude can't draw images. The kit uses images for concept art, style sheets and some textures;
without them it still builds the world, using collages of reference pictures and free texture
sites instead, so the style is less consistent. To generate images for free on your own PC,
install **ComfyUI Desktop** (<https://www.comfy.org/download>) and pick a model by your graphics
card's memory (VRAM; the agent can check it for you):

| VRAM | Model (ComfyUI *Workflow → Browse Templates*) | Notes |
|---|---|---|
| under 8 GB, or no NVIDIA card | none | go without generated images |
| 8–12 GB | FLUX.2 [klein] 4B (text-to-image and image edit) | fast; check the licence on its model page |
| 12–16 GB | Qwen-Image-Edit-2511, GGUF Q4 build | Apache-2.0 |
| 24 GB | Qwen-Image-2512 + Qwen-Image-Edit-2511, FP8 | best local quality, Apache-2.0 |

Avoid Qwen-Image 2.1: its licence allows non-commercial research use only. The agent connects
the chosen model to the kit (`.omp/docs/tools.md`, backend `comfyui`). Image-to-3D (Tripo,
Meshy) costs money per model: skip it, the kit uses free assets and Blender modelling instead.

## Updates

- **Unity stays on 2022.3.22f1.** Never accept a Unity upgrade; VRChat supports only this version.
- **VRChat SDK and other packages** update in ALCOM (*Manage Project*). Update between work
  sessions, not in the middle of a build stage: ask the agent to commit a backup first, close
  Unity, update in ALCOM, reopen, and have the agent check the console for errors. Never edit
  package files by hand.
- **MCP for Unity** (the agent's connection to Unity) is pinned to one version on purpose; don't
  update it from Unity's Package Manager. When a kit update changes the pinned version, ask the
  agent to update it in each project together with the server (`.omp/docs/hosts.md`).
- **ALCOM itself** can update whenever it offers to; it only creates and manages projects.
- **The kit:** `git -C .omp pull`, then re-run `python .omp/scripts/install.py --host claude` and
  restart Claude Code.

## When something goes wrong

Tell the agent what you see, in your own words, with a screenshot if you have one. It checks
`.omp/docs/troubleshooting.md` and the kit's notes before guessing.

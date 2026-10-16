# Generation tools: fixed names, your backends

Skills and agents never name a product. They call one of four tools through
`.omp/scripts/tool.py`, and each user decides what runs behind each name in
`.omp/local/tools.json` (template: [local.example/tools.json](../local.example/tools.json)).

| Tool | Does | Output |
|---|---|---|
| `image-gen` | text → image: concept art, references, texture sheets | PNG |
| `image-edit` | text + reference images → image: keep a style, object or outfit | PNG |
| `image-to-3d` | one image, or front/left/back/right views → model | GLB |
| `blender` | runs a Python script in headless Blender | whatever the script writes |

```
python .omp/scripts/tool.py image-gen  --prompt-file p.txt --aspect landscape --output out.png
python .omp/scripts/tool.py image-edit --prompt-file p.txt --reference lock1.png --reference lock2.png --output out.png
python .omp/scripts/tool.py image-to-3d --image front.png --faces 8000 --output prop.glb
python .omp/scripts/tool.py image-to-3d --front f.png --left l.png --back b.png --right r.png --output prop.glb
python .omp/scripts/tool.py blender --script build.py [--blend file.blend] -- <script args>
python .omp/scripts/tool.py check            # what is configured, and does it answer
```

- `--aspect`: `square`, `landscape` (3:2), `portrait` (2:3), `wide` (16:9), `tall` (9:16) or
  `WIDTHxHEIGHT`. `--quality low|medium|high`, `--transparent` (PNG alpha where the backend
  supports it; others report a warning, so use a flat key colour instead).
- `--dry-run` shows which backend would run with what request, without calling anything.
  `--backend <name>` forces one entry of the chain.
- Stdout is one JSON object. `backend` says which entry produced the file: record it next to
  the prompt, because a fallback backend draws in a different style. `format` is the file type
  actually written; `meta.format_warning` flags a WebP/JPEG where PNG was expected (some
  subscription tools write WebP under a `.png` name).

| Exit | Meaning | What the agent does |
|---|---|---|
| 0 | done, file at `output` | inspect the result |
| 1 | every backend failed (`tried` lists why) | report it; don't silently switch tools |
| 2 | usage or config error | fix the call or the config |
| 3 | hand-off: `handoff: agent` (call `agent_tool` yourself with `request`) or `handoff: user` (ask the user to make it, `how` says where) | do it, save to `output` |
| 4 | the backend spends money and needs approval | ask the user to approve this generation, then re-run with `--approve-spend` |

## Choosing backends: paid first, free as fallback

Each tool takes a list; the first backend that works is used. Put the best service you pay for
first and a free one after it, so work continues when a key runs out or a service is down.

| Tool | Paid (better, listed best first) | Free fallback |
|---|---|---|
| `image-gen` | `openai` (GPT Image), `gemini` (Nano Banana), Unity MCP `generate_image` with a fal.ai or OpenRouter key (`agent`), a subscription CLI you already have (`command`) | `comfyui` + Qwen-Image-2512 (local GPU) |
| `image-edit` | `openai`, `gemini` (both take several references), Unity MCP `generate_image` (one reference, `agent`) | `comfyui` + Qwen-Image-Edit-2511 |
| `image-to-3d` | `tripo`, `meshy`, Unity MCP `generate_model` (`agent`), a web studio by hand (`manual`) | TRELLIS.2 on a local GPU (`command`) |
| `blender` | none | Blender 4.2+ (required for custom props) |

`confirm_spend: true` makes a backend stop with exit 4 until the user approves each generation.
Set it on every pay-per-use backend whose cost the user wants to see first (image-to-3D usually).

## Backend reference

Common fields: `backend` (type), `name` (label for `--backend` and the output), `params` (extra
API fields merged into the request), `timeout` (seconds), `confirm_spend`.

### openai

GPT Image through the OpenAI Images API. Key: <https://platform.openai.com/api-keys>, saved as
the user env var `OPENAI_API_KEY` (or `key_env`/`key_file`). `model` defaults to
`gpt-image-2.5-sunburst`; `base_url` for an OpenAI-compatible proxy. References go to the edits
endpoint (up to 16). Supports `--transparent`.

### gemini

Nano Banana through the Gemini API (`/v1beta/interactions`). Key:
<https://aistudio.google.com/apikey> as `GEMINI_API_KEY`. `model` defaults to
`gemini-nano-banana-2.1` (`gemini-3-pro-image` for Nano Banana Pro); `image_size` `1K`/`2K`/`4K`
(default `2K`). Explicit sizes map to the nearest supported aspect ratio. No transparency.

### comfyui (free, local)

Any ComfyUI workflow, run through ComfyUI's HTTP API. Two model choices:

- **Qwen-Image 2.1** (<https://huggingface.co/Comfy-Org/Qwen-Image-2.1>): one model for
  text → image and editing with up to 10 references. The kit ships ready API workflows for it:
  `.omp/scripts/comfyui/qwen-image-2.1-t2i.json` and `.omp/scripts/comfyui/qwen-image-2.1-edit.json`
  (int8 diffusion model and int8 Qwen3-VL encoder, bf16 VAE; fits a 24 GB GPU; needs a ComfyUI
  recent enough to have the `TextEncodeQwenImage21` node). **Licence: Qwen Research License,
  non-commercial research and evaluation only**; commercial use needs a separate licence from
  Qwen. An edit's output follows the first reference's aspect ratio.
- **Qwen-Image-2512** (text → image) and **Qwen-Image-Edit-2511** (references), Apache-2.0, so
  usable commercially. Open their templates under *Workflow → Browse Templates*, let them download
  the models (FP8 wants about 20 GB of VRAM + RAM; GGUF Q4 builds,
  <https://unsloth.ai/docs/models/tutorials/qwen-image-2512>, run in about 14 GB), run each once,
  then *Workflow → Export (API)* to `.omp/local/comfyui/`.

Install ComfyUI (<https://www.comfy.org/download>, or the portable build from
<https://github.com/comfyanonymous/ComfyUI>), set `url` and `workflow` in `tools.json`, then
`tool.py check`. To have the tool start ComfyUI when it is down, add `start` (the launch command as
a list, e.g. `["<comfy python>", "<ComfyUI>/main.py", "--listen", "127.0.0.1", "--port", "8188",
"--disable-auto-launch"]`), `start_cwd`, and optionally `start_log` and `start_timeout` (seconds,
default 240). It only auto-starts on a loopback url and leaves the server running afterwards.

The router fills a workflow by itself: the prompt goes into the text encoder feeding the sampler's
`positive` input, the size into the `Empty…Latent` node (multiples of 32, about 1 MP), a fresh
seed into the sampler, and the reference images into the `LoadImage` nodes in node-id order. With
more references than `LoadImage` nodes it adds nodes when the encoder has numbered image inputs
(`images.image_1`, `image_2`, ...); otherwise the counts must match. When a workflow is unusual,
put placeholders in the JSON instead: `{{prompt}}`, `{{negative}}`, `{{width}}`, `{{height}}`,
`{{seed}}`, `{{image1}}`, `{{image2}}`, ...

### tripo

Tripo API v3 (<https://developers.tripo3d.com>). Key from the Tripo console as `TRIPO_API_KEY`, or
`key_file` pointing at a one-line key file under `.omp/local/`. `model` defaults to
`v3.1-20260211`; low-poly P-series via `"model": "P1-20260311"`. `--faces` sets `face_limit`;
four views use the multiview endpoint. API credits are separate from a Studio subscription. The
task id is printed when submitted: after a timeout, `--resume <task_id>` downloads it instead of
paying again.

### meshy

Meshy API (<https://docs.meshy.ai>) with `MESHY_API_KEY`. `model` defaults to `latest`; `--faces`
turns on remeshing to that count. Several views use multi-image-to-3D. Resume with
`--resume <kind>:<task_id>` as printed.

### command (any local program)

Runs a program you already have: a subscription CLI, a local model, your own script. `args` is
the argument list with placeholders: `{prompt}`, `{prompt_file}` (a temp file when the prompt was
given inline), `{output}`, `{aspect}`, `{width}`, `{height}`, `{quality}`, `{image}`, `{front}`,
`{left}`, `{back}`, `{right}`, `{faces}`, `{kit}`; the tokens `{references}` and `{images}` expand
to every file, each preceded by `reference_flag` / `image_flag` when set. A first argument ending
in `.py` runs with this Python unless `python` names another interpreter. The run counts as done
only when it exits 0 and writes `{output}`.

TRELLIS.2 (MIT, <https://github.com/microsoft/TRELLIS.2>, weights `microsoft/TRELLIS.2-4B`) needs
an NVIDIA GPU with 24 GB+ (upstream tests on Linux only). Install it per its README (`setup.sh`),
then use the kit's wrapper `.omp/scripts/trellis2_glb.py` (the repo's minimal example as a CLI:
`--image`, `--faces`, `--output`) through a `command` entry with `python` = the TRELLIS.2
environment's interpreter and `cwd` = the clone; the template has the entry.

### agent and manual (hand-offs)

`{"backend": "agent", "tool": "generate_model", "how": "...", "args": {...}}` returns exit 3 so
the agent calls one of its own tools: the Unity MCP `generate_image` / `generate_model` tools
(provider keys stay in the Unity editor's secure store; call `list_providers` first), or an image
tool your agent host has. The agent saves the result to `output`.

`{"backend": "manual", "how": "..."}` returns exit 3 so the user makes it by hand (a web studio
on a subscription) and saves it to `output`.

### blender

`{"path": "<blender executable>"}`. The tool runs
`blender -b --factory-startup [file.blend] --python <script> -- <args>`: background mode, no
window, third-party add-ons off. Every Blender step in the kit runs this way. The Blender MCP
add-on is optional, for live sessions the user drives.

## Lightmapper

Not a `tool.py` tool, but chosen in the same order: **Bakery** (paid) if the user owns it, else
**GLIM** (free, <https://github.com/z3y/glim>), else Unity's **Progressive GPU**. Setup and the
differences between them: `.omp/skills/bakery-light-baking/SKILL.md`.

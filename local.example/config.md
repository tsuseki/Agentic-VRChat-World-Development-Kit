# Local setup (template)

Copy this folder to `.omp/local/` and fill it in. `.omp/local/` is ignored by the kit's git, so
your paths, accounts and hardware never reach the public repo. Shared kit files name a setting
here (for example "the `image-gen` provider in `local/config.md`") instead of a personal value.

## Machine

- workspace: `<folder that holds your Unity projects>` (the kit lives in `<workspace>/.omp`)
- hostname: `<output of hostname>`; benchmark profile `.omp/local/benchmarks/<hostname>.json`
  (copy `benchmarks/HOSTNAME.json` from this folder)
- gpu: `<model and VRAM>`

## Providers

Every capability names what the agent calls (an MCP tool, a command, or a skill) and any limits.
Pick one per line; delete the rest. Free local options are listed first.

- image-gen (text to image: concept art, references, textures):
  - free, local: ComfyUI + Qwen-Image-2512 (Apache-2.0). Q4_K_M GGUF needs ~14 GB VRAM+RAM
    combined; FP8 ~20 GB. Setup: <https://unsloth.ai/docs/models/tutorials/qwen-image-2512>.
    Call: ComfyUI HTTP API at `http://127.0.0.1:8188` with your saved workflow JSON.
  - hosted: the Unity MCP `generate_image` tool (fal.ai or OpenRouter key in the editor), an
    OpenAI / Google (Nano Banana) API key, or any image skill your agent host provides.
- image-edit (reference-conditioned: keep a style, outfit or object across images):
  - free, local: ComfyUI + Qwen-Image-Edit-2511 (multi-reference), same setup as above.
  - hosted: the same providers as image-gen when they accept reference images.
- image-to-3d (props from approved reference images):
  - free, local: TRELLIS.2 (MIT, <https://huggingface.co/microsoft/TRELLIS.2-4B>); needs a large GPU.
  - hosted: Tripo, Meshy (the Unity MCP `generate_model` tool supports both with your key).
- 3d-modeling: Blender (free) with a Blender MCP add-on connected to your agent host.
- unity: MCP for Unity, see `docs/hosts.md`.

## Assets

- asset-library: `<path to your local model/texture library, or none>`
- owned packs: `<purchased packs you may use in worlds; never redistribute them>`

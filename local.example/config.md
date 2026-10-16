# Local setup (template)

Copy this folder to `.omp/local/` and fill it in. `.omp/local/` is ignored by the kit's git, so
your paths, accounts and hardware never reach the public repo. Shared kit files name a setting
here (for example "the `asset-library` from `local/config.md`") instead of a personal value.

## Machine

- workspace: `<folder that holds your Unity projects>` (the kit lives in `<workspace>/.omp`)
- hostname: `<output of hostname>`; benchmark profile `.omp/local/benchmarks/<hostname>.json`
  (copy `benchmarks/HOSTNAME.json` from this folder)
- gpu: `<model and VRAM>`

## Tools

The services behind `image-gen`, `image-edit`, `image-to-3d` and `blender` are set in
`tools.json` next to this file (guide: `.omp/docs/tools.md`; paid first, free fallbacks after).
Note here what you chose and any limits the agent should know (subscription caps, who approves
spending), never the keys.

- lightmapper: `<Bakery | GLIM | Progressive GPU>`
- unity: MCP for Unity, see `docs/hosts.md`.

## Assets

- asset-library: `<path to your local model/texture library, or none>`
- owned packs: `<purchased packs you may use in worlds; never redistribute them>`

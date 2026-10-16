# Personal layer template

The kit keeps everything specific to one person or machine in `.omp/local/`, which the kit's
`.gitignore` excludes. Set it up once:

1. Copy this folder to `.omp/local/` and fill in `config.md`, `tools.json` and `AGENTS.local.md`
   (`.omp/docs/bootstrap.md` §4 walks you through `tools.json`).
2. Optional: `git -C .omp/local init` to back it up locally (never push it).
3. Enable the leak check: `git -C .omp config core.hooksPath .githooks`. Every commit then fails
   if an added line matches `local/banned-terms.txt`.

| File | Holds |
|---|---|
| `AGENTS.local.md` | your projects, priorities and preferences; overrides kit defaults |
| `config.md` | paths, hardware, asset library, lightmapper |
| `tools.json` | which services run behind `image-gen`, `image-edit`, `image-to-3d`, `blender` (`.omp/docs/tools.md`) |
| `banned-terms.txt` | regexes the pre-commit leak check blocks |
| `benchmarks/<hostname>.json` | your machine's perf bands (`scripts/perf_grade.py`) |
| `skills/` | personal skills; point your host at them (omp: `skills.customDirectories`) |
| `notes/` | personal knowledge notes |

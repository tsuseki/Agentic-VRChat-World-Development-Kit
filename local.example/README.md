# Personal layer template

The kit keeps everything specific to one person or machine in `.omp/local/`, which the kit's
`.gitignore` excludes. Set it up once:

1. Copy this folder to `.omp/local/` and fill in `config.md` and `AGENTS.local.md`.
2. Optional: `git -C .omp/local init` to back it up locally (never push it).
3. Enable the leak check: `git -C .omp config core.hooksPath .githooks`. Every commit then fails
   if an added line matches `local/banned-terms.txt`.

| File | Holds |
|---|---|
| `AGENTS.local.md` | your projects, priorities and preferences; overrides kit defaults |
| `config.md` | paths, hardware, and which tool provides each capability (image-gen, image-to-3d, ...) |
| `banned-terms.txt` | regexes the pre-commit leak check blocks |
| `benchmarks/<hostname>.json` | your machine's perf bands (`scripts/perf_grade.py`) |
| `skills/` | personal skills; point your host at them (omp: `skills.customDirectories`) |
| `notes/` | personal knowledge notes |

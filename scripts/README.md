# .omp/scripts/

Workspace helper scripts: driving a Unity project with the CoplayDev **MCP for Unity**
server (`com.coplaydev.unity-mcp`) and maintaining the knowledge base. Python 3.10+;
no third-party packages.

## install.py

```
python .omp/scripts/install.py --host claude|agents [--copy] [--dry-run]
```

Wires the kit into a host that does not read `.omp/` itself: links skills (kit and
`.omp/local/skills/`) into `.claude/skills/` or `.agents/skills/`, copies agents to `.claude/agents/`,
and points the host's `CLAUDE.md` / `AGENTS.md` at `.omp/AGENTS.md`. Idempotent. See `docs/hosts.md`.

## tool.py

```
python .omp/scripts/tool.py image-gen|image-edit|image-to-3d|blender|check ...
```

The generation tools the skills call by fixed name; the backends behind each come from
`.omp/local/tools.json` (paid first, free fallbacks). Contract, backends and exit codes:
`docs/tools.md`.

## leak_check.py

```
python .omp/scripts/leak_check.py [--all]
```

The pre-commit hook (`.githooks/pre-commit`; enable with `git -C .omp config core.hooksPath .githooks`).
Refuses staged added lines matching a regex in `.omp/local/banned-terms.txt` (else
`.omp/local.example/banned-terms.txt`); `--all` scans every tracked file.

## check_kit.py

```
python .omp/scripts/check_kit.py
```

Release check over tracked files: skill/agent front matter, relative links, no host-specific URIs
(`xd://`, `skill://`, ...) outside `docs/hosts.md`, valid notes, and `leak_check.py --all`.

## install-unity-mcp.py

```
python .omp/scripts/install-unity-mcp.py PROJECT_ROOT
```

Adds the MCP for Unity package (pinned git URL in `PACKAGE_URL`) to
`PROJECT_ROOT/Packages/manifest.json`. Only for a **closed** project: it refuses
to run if `Temp/UnityLockfile` exists, and does nothing if the dependency is
already present. The original manifest is saved as `manifest.json.before-mcp`;
delete it once Unity has resolved and compiled the package. For a project that
is already open, use Package Manager > *Add package from git URL* with the same
URL instead. A manifest entry alone does not prove connectivity — open Unity,
check the console, and confirm the project shows up as an MCP instance.

## unity_mcp.py

```
python unity_mcp.py --list                      # list tools
python unity_mcp.py --schema <tool>             # print one tool's JSON schema
python unity_mcp.py <tool> '<json args>'        # call a tool
python unity_mcp.py <tool> --args-file args.json
```

Minimal stdio MCP client: launches the server via
`uvx --from mcpforunityserver==10.0.0 mcp-for-unity --transport stdio` (pinned to
the same tag as `PACKAGE_URL`; bump both together), performs
the MCP handshake, calls one tool, prints the result and exits (exit code 1 on a
tool error). Useful when your agent host has no MCP support, or for quick
manual calls. `--args-file` avoids shell-quoting problems with C# passed to
`execute_code`.

Requirements: [uv](https://docs.astral.sh/uv/) with `uvx` on `PATH`; the server
package already in the uv cache (the script runs `uvx --offline` — see the
docstring for the one-time online command, or remove `--offline`); the MCP for
Unity package installed in the project; and the project open in the Unity Editor.

## unity-world.gitignore

Template `.gitignore` for a Unity/VRChat world project (GitHub's Unity template plus IDE caches,
agent screenshot folders, and `*.unitypackage` so purchased packs stay out of the repo). Copy it to
the project root as `.gitignore` before the first commit.

## build-knowledge-index.py

```
python .omp/scripts/build-knowledge-index.py
```

Regenerates `.omp/knowledge/INDEX.md` from the note front matter and validates every note in
`.omp/knowledge/notes/` (known `topic`, a `summary`, well-formed `sources`). Exits non-zero and
lists the bad notes on failure. Run it after adding or editing a note.

## perf_grade.py

```
python .omp/scripts/perf_grade.py --baseline base1.json [--baseline base2.json] [variant.json ...] \
    [--label variant.json=Name] [--static textureVramMB=339] [--sort drawCalls|cameraRenderMs|gpuFrameMs]
```

Grades `PerfSample` JSON against the benchmark bands in `.omp/local/benchmarks/<hostname>.json` (errors
on a host without a profile: the bands are machine-specific) and, given variant runs with one
system disabled each, prints the attribution table: per-system deltas in ms, draw calls, SetPass,
batches and tris, sorted, with deltas inside twice the baseline noise range marked `~`. Variants
are labelled by their `disabledRoots`, or by `--label` for systems toggled by hand.

## vrc_session_perf.py

```
python .omp/scripts/vrc_session_perf.py record [--once]
python .omp/scripts/vrc_session_perf.py analyze <session dir> [<session dir> ...] [--settle 15] [--spot 30]
```

In-game side of the benchmark profile. `record` waits for `VRChat.exe` and captures its frames
with PresentMon (`~/Tools/PresentMon/PresentMon.exe`; no admin needed for "Performance Log Users",
it targets the PID). Each VRChat launch is its own session; it keeps waiting for the next launch
until Ctrl+C (`--once`: one launch). Raw CSVs stay outside git in `~/Tools/PresentMon/sessions/`.
`analyze` takes one or more consecutive session segments and reports **spots only**: the frames
after each F12 screenshot (3 s screenshot stall skipped, up to `--spot` s or the next F12), where the
owner stands still at a view he chose as representative, plus an "all spots" row per world. Reports
FPS, 1% low, frame-time median/p95, CPU/GPU busy, CPU- or GPU-bound and hitches/min. Whole-visit
stats (walking, menus; the last 5 s before a world switch trimmed) stay in `report.json`. Reported
verdicts (what players say about a world: smooth/ok/laggy) go in `~/Tools/PresentMon/sessions/verdicts.json`
keyed by world name; a `<session>/verdicts.json` overrides them.

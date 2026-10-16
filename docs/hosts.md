# Wiring AWDK into an agent host

The kit is plain files: `.omp/AGENTS.md` (entry point), `.omp/skills/<name>/SKILL.md` (front matter
`name`, `description`; the [Agent Skills](https://agentskills.io) format) and `.omp/agents/<name>.md`
(front matter `name`, `description`, then the prompt). Clone it as `<workspace>/.omp/`, where
`<workspace>` holds your Unity projects; every `.omp/...` path in the kit resolves from there.

Every host needs four things: (1) read `.omp/AGENTS.md` at session start, (2) discover the skills,
(3) register the agents as subagents where the host has them, (4) MCP for Unity connected (and a
Blender MCP for modelling). `scripts/install.py` does (1)–(3); (4) is per host, below.

Personal skills in `.omp/local/skills/` are installed alongside the kit's (`install.py`) or added
through the host's extra-skills setting.

## oh-my-pi

- Reads `.omp/AGENTS.md`, `.omp/skills/` and `.omp/agents/` directly; nothing to install.
- Personal skills: `skills.customDirectories: ["<workspace>/.omp/local/skills"]` in `~/.omp/agent/config.yml`.
- Optional per-agent `model:`, `thinking-level:` and `tools:` front matter, per the table below.
- MCP: `mcp.json` (user `~/.omp/agent/mcp.json` or `<workspace>/.omp/mcp.json`).

## Claude Code

- `python .omp/scripts/install.py --host claude`: links each skill into `<workspace>/.claude/skills/`,
  copies the agents into `<workspace>/.claude/agents/` and adds `@.omp/AGENTS.md` to
  `<workspace>/CLAUDE.md`. Re-run after pulling kit updates that add skills or change agents.
- Agents without a `tools:` line inherit all tools; add one to restrict a reviewer (table below).
  The kit's `model:` / `thinking-level:` keys are oh-my-pi syntax; Claude Code ignores what it doesn't know.
- MCP: `claude mcp add UnityMCP -- uvx --from mcpforunityserver==10.0.0 mcp-for-unity --transport stdio`
  (or *Window → MCP for Unity → Configure*). Keep the server version equal to the Unity package tag
  pinned in `.omp/scripts/install-unity-mcp.py` (`PACKAGE_URL`, currently `v10.0.0`); bump both together.

## Codex, Gemini CLI and other `AGENTS.md` hosts

- `python .omp/scripts/install.py --host agents`: links each skill into `<workspace>/.agents/skills/`
  (read by Codex, Gemini CLI and others) and adds a pointer to `.omp/AGENTS.md` in
  `<workspace>/AGENTS.md`.
- No subagent registry: run each agent file as its own session seeded with the brief the pipeline
  writes, keeping builder and reviewer turns separate.
- MCP: add MCP for Unity to the host's MCP config: command `uvx`, args
  `--from mcpforunityserver==10.0.0 mcp-for-unity --transport stdio`.

## Cursor

- Add an always-applied project rule (`.cursor/rules/vrchat-world.mdc`) that says to read
  `.omp/AGENTS.md` and load skills from `.omp/skills/` via its routing table.
- No subagent registry: run reviewers as separate chats seeded with the agent file.
- MCP: *Settings → MCP → Add* MCP for Unity with the same command and args as above.

## Generic / no MCP support

`.omp/scripts/unity_mcp.py <tool> '<json>'` is a minimal stdio MCP client the agent can call from a shell
(`--list`, `--schema <tool>`, `--args-file`). See `.omp/scripts/README.md`.

## Your own tools (images, image-to-3D, Blender)

Skills call fixed tool names (`image-gen`, `image-edit`, `image-to-3d`, `blender`) through
`python .omp/scripts/tool.py`; which service or program runs behind each is set per machine in
`.omp/local/tools.json`, paid services first and free local ones as fallbacks. Setup and every
backend: [tools.md](tools.md). Tools only your agent host can call (an MCP image tool, a host
image skill) plug in as `agent` hand-offs, so the skills stay the same on every host.

## Recommended tools and model tiers per agent

| Agent | Tools | Model tier / reasoning |
|---|---|---|
| orchestrator (main session) | everything, incl. user questions and subagent spawning | strongest available, medium |
| `world-architect` | read/write/edit, shell, file search, Unity MCP, image generation | strong, medium |
| `world-builder` | read/write/edit, shell, file search, Unity MCP | strong, medium |
| `perf-optimizer` | read/write/edit, shell, file search, Unity MCP | strong, medium |
| `layout-reviewer` | read, shell, file search, Unity MCP | strong (vision), low |
| `dressing-reviewer` | read, shell, file search, Unity MCP | strong (vision), low |
| `final-reviewer` | read, shell, file search, Unity MCP | strong (vision), low |
| `asset-finder` | read, file search, shell, web search; no MCP | mid-size, medium |
| `blender-modeler` | read/write, file search, shell, Blender MCP | strong, low |
| `blender-optimizer` | read/write, file search, shell, Blender (headless) | strong, low |

Reviewers need `execute_code` for captures but must not write project files; deny edit tools if the
host allows per-agent tool lists.

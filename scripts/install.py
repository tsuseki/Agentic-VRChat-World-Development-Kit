#!/usr/bin/env python3
"""Wire the AWDK kit into an agent host that does not read `.omp/` by itself.

    python .omp/scripts/install.py --host claude|agents [--copy] [--dry-run]

The kit lives in <workspace>/.omp/; the workspace is its parent folder.
- claude: Claude Code. Skills -> <workspace>/.claude/skills/<name>, agents -> <workspace>/.claude/agents/<name>.md,
  and <workspace>/CLAUDE.md imports .omp/AGENTS.md.
- agents: hosts that read the shared `.agents/skills/` folder and a root AGENTS.md (Codex, Gemini CLI and
  others). Skills -> <workspace>/.agents/skills/<name>; <workspace>/AGENTS.md points at .omp/AGENTS.md.
  These hosts have no subagent registry: run an agent file from .omp/agents/ as its own session.
oh-my-pi needs no install: it reads .omp/ directly (add .omp/local/skills via skills.customDirectories).

Skills from .omp/local/skills/ (personal, when present) are installed too. Skill folders are linked
(a junction on Windows, a symlink elsewhere) so kit updates apply at once; --copy copies instead and
must be re-run after updates. Agent files are always copied. Idempotent.
"""
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
WORKSPACE = KIT.parent
HOSTS = {
    "claude": {"skills": ".claude/skills", "agents": ".claude/agents", "entry": "CLAUDE.md",
               "line": "@.omp/AGENTS.md"},
    "agents": {"skills": ".agents/skills", "agents": None, "entry": "AGENTS.md",
               "line": "Read `.omp/AGENTS.md` first and follow it; it is the entry point of the AWDK kit."},
}


def is_link(path: Path) -> bool:
    if path.is_symlink() or (getattr(path, "is_junction", None) and path.is_junction()):
        return True
    if os.name == "nt" and path.exists():
        try:
            return bool(os.readlink(path))
        except OSError:
            return False
    return False


def link_target(path: Path) -> Path:
    target = os.readlink(path)
    return Path(target[4:] if target.startswith("\\\\?\\") else target).resolve()


def remove(path: Path) -> None:
    if is_link(path):
        os.rmdir(path) if os.name == "nt" and path.is_dir() else path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def make_link(src: Path, dst: Path) -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)], check=True, stdout=subprocess.DEVNULL)
    else:
        dst.symlink_to(src, target_is_directory=True)


def same_tree(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__"])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(same_tree(a / d, b / d) for d in cmp.common_dirs)


def install_skill(src: Path, dst: Path, copy: bool, dry: bool) -> str:
    if not copy:
        if is_link(dst) and link_target(dst) == src.resolve():
            return "ok"
        action = "relinked" if dst.exists() or is_link(dst) else "linked"
        if not dry:
            remove(dst)
            make_link(src, dst)
        return action
    if dst.is_dir() and not is_link(dst) and same_tree(src, dst):
        return "ok"
    action = "updated" if dst.exists() or is_link(dst) else "copied"
    if not dry:
        remove(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return action


def install_agent(src: Path, dst: Path, dry: bool) -> str:
    text = src.read_text(encoding="utf-8")
    if dst.is_file() and dst.read_text(encoding="utf-8") == text:
        return "ok"
    action = "updated" if dst.exists() else "copied"
    if not dry:
        dst.write_text(text, encoding="utf-8", newline="\n")
    return action


def ensure_entry(path: Path, line: str, dry: bool) -> str:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in text:
        return "ok"
    if not dry:
        path.write_text((text.rstrip("\n") + "\n\n" if text else "") + line + "\n", encoding="utf-8", newline="\n")
    return "appended" if text else "created"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", required=True, choices=sorted(HOSTS))
    ap.add_argument("--copy", action="store_true", help="copy skill folders instead of linking them")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if KIT.name != ".omp":
        print(f"warning: the kit folder is {KIT.name!r}; its docs assume <workspace>/.omp/", file=sys.stderr)
    host = HOSTS[a.host]

    skills_dir = WORKSPACE / host["skills"]
    if not a.dry_run:
        skills_dir.mkdir(parents=True, exist_ok=True)
    roots = [KIT / "skills", KIT / "local" / "skills"]
    for skill in sorted((p for r in roots if r.is_dir() for p in r.iterdir() if (p / "SKILL.md").is_file()),
                        key=lambda p: p.name):
        print(f"skill {skill.name}: {install_skill(skill, skills_dir / skill.name, a.copy, a.dry_run)}")

    if host["agents"]:
        agents_dir = WORKSPACE / host["agents"]
        if not a.dry_run:
            agents_dir.mkdir(parents=True, exist_ok=True)
        for agent in sorted((KIT / "agents").glob("*.md")):
            print(f"agent {agent.stem}: {install_agent(agent, agents_dir / agent.name, a.dry_run)}")
    else:
        print("agents: this host has no subagent registry; run .omp/agents/<name>.md as its own session")

    entry = WORKSPACE / host["entry"]
    print(f"{host['entry']}: {ensure_entry(entry, host['line'], a.dry_run)}")
    print("\nNext: connect MCP for Unity (and Blender MCP) in the host, see .omp/docs/hosts.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

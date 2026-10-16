#!/usr/bin/env python3
"""Check the kit before a release: front matter, relative links, host-neutral syntax, leaks.

    python .omp/scripts/check_kit.py

Scans tracked files only (git ls-files), so .omp/local/ never counts. Exits 1 on any finding:
- skills: `name` equals the folder, `description` set; agents: `name` equals the file stem, `description` set
- every relative Markdown link resolves
- no harness-specific URIs (`xd://`, `skill://`, `local://`, `agent://`, `artifact://`, `cfg://`)
  outside docs/hosts.md, which documents the hosts
- knowledge notes valid (build-knowledge-index.py) and no personal terms (leak_check.py --all)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
HOST_URI = re.compile(r"\b(xd|skill|local|agent|artifact|cfg)://")
HOST_DOCS = {"docs/hosts.md", "scripts/README.md", "scripts/check_kit.py"}  # these describe the URIs
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
# Backticked kit paths such as `.omp/docs/hosts.md`; placeholders (<...>, *), local/ and anchors skipped.
OMP_PATH = re.compile(r"`\.omp/(?!local/)([^`<>*\s#:]+?)/?(?:[#:][^`]*)?`")


def tracked() -> list[str]:
    out = subprocess.run(["git", "-C", str(KIT), "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p and (KIT / p).is_file()]


def front_matter(path: Path) -> dict | None:
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", path.read_text(encoding="utf-8"), re.S)
    if not m:
        return None
    return {k.strip(): v.strip().strip("\"'") for k, v in
            (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l and not l.startswith((" ", "\t")))}


def main() -> int:
    errors: list[str] = []
    for skill in sorted((KIT / "skills").glob("*/SKILL.md")):
        d = front_matter(skill)
        if not d or d.get("name") != skill.parent.name or not d.get("description"):
            errors.append(f"skill front matter (name == folder, description): {skill.relative_to(KIT).as_posix()}")
    for agent in sorted((KIT / "agents").glob("*.md")):
        d = front_matter(agent)
        if not d or d.get("name") != agent.stem or not d.get("description"):
            errors.append(f"agent front matter (name == file stem, description): agents/{agent.name}")

    for rel in tracked():
        path = KIT / rel
        if path.suffix not in (".md", ".py", ".cs", ".txt", ".json", ".html"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if rel not in HOST_DOCS:
            for n, line in enumerate(text.splitlines(), 1):
                if HOST_URI.search(line):
                    errors.append(f"host-specific URI {rel}:{n}: {line.strip()[:100]}")
        if path.suffix == ".md":
            for target in LINK.findall(text):
                if re.match(r"[a-z]+:", target):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"broken link {rel} -> {target}")
                elif rel.startswith(("skills/", "agents/")) and not resolved.is_relative_to(KIT / "skills"):
                    # installed skills and agents move to .claude/skills etc.; only skill-to-skill links survive
                    errors.append(f"non-portable link {rel} -> {target} (write it as `.omp/...`)")
            for target in OMP_PATH.findall(text):
                if not (KIT / target).exists():
                    errors.append(f"missing path {rel}: .omp/{target}")

    for script, args in (("build-knowledge-index.py", []), ("leak_check.py", ["--all"])):
        r = subprocess.run([sys.executable, str(KIT / "scripts" / script), *args], capture_output=True, text=True)
        if r.returncode:
            errors.append(f"{script} failed:\n{r.stdout.strip()}\n{r.stderr.strip()}")

    print("\n".join(errors) if errors else "kit OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

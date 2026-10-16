#!/usr/bin/env python3
"""Block personal content from entering the kit's git history.

    python .omp/scripts/leak_check.py            # staged added lines + commit identity (the pre-commit hook)
    python .omp/scripts/leak_check.py --all      # every tracked file, full content (cleanup report)

Patterns: one case-insensitive regex per line in local/banned-terms.txt (personal, ignored by git),
else local.example/banned-terms.txt. Exit 1 and list file:line: pattern on any match.
Fix a hit by moving the personal part into local/ (AGENTS.local.md, config.md) and naming the
setting in the shared file. Never bypass with --no-verify.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent


def patterns() -> list[re.Pattern]:
    for name in ("local/banned-terms.txt", "local.example/banned-terms.txt"):
        path = KIT / name
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            return [re.compile(l.strip(), re.I) for l in lines if l.strip() and not l.lstrip().startswith("#")]
    return []


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(KIT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def staged_lines():
    """(path, line number, text) for every added line in the index."""
    path, line = None, 0
    for row in git("diff", "--cached", "-U0", "--no-color", "--no-ext-diff", "--diff-filter=ACMR").splitlines():
        if row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
        elif row.startswith("@@"):
            line = int(re.search(r"\+(\d+)", row).group(1))
        elif row.startswith("+") and path:
            yield path, line, row[1:]
            line += 1


def tracked_lines():
    for path in git("ls-files", "-z").split("\0"):
        full = KIT / path
        if not path or not full.is_file():
            continue
        data = full.read_bytes()
        if b"\0" in data[:8192]:
            continue  # binary
        for n, text in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            yield path, n, text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true", help="scan every tracked file instead of the staged diff")
    a = ap.parse_args()
    pats = patterns()
    if not pats:
        print("leak_check: no banned-terms.txt in local/ or local.example/; nothing checked", file=sys.stderr)
        return 0
    hits = [(p, n, pat.pattern) for p, n, text in (tracked_lines() if a.all else staged_lines())
            for pat in pats if pat.search(text)]
    for p, n, pat in hits:
        print(f"{p}:{n}: {pat}")
    if hits:
        print(f"\nleak_check: {len(hits)} personal term(s) in kit files. Move them to .omp/local/ "
              "(AGENTS.local.md / config.md) and reference the setting instead.", file=sys.stderr)
        return 1
    if not a.all:
        for var in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
            ident = git("var", var).rsplit(">", 1)[0] + ">"
            if any(pat.search(ident) for pat in pats):
                print(f"leak_check: {var} is {ident}, a personal identity. Set this repo's user.name and "
                      "user.email (git config) to the kit's public identity.", file=sys.stderr)
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

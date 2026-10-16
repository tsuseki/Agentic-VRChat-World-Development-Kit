"""Regenerate .omp/knowledge/INDEX.md from the note front matter and validate every note.

Usage: python .omp/scripts/build-knowledge-index.py
Each note in .omp/knowledge/notes/ needs front matter with a known `topic` and a `summary`;
`sources`, when present, is `in-house` or a [list] of http(s) URLs. The index is written even
when some notes fail; the script then lists the failures and exits non-zero.
"""
import collections
import re
import sys
from pathlib import Path

KNOWLEDGE = Path(__file__).resolve().parent.parent / "knowledge"
TOPICS = [
    "lighting-baking", "probes-reflection-and-light", "materials-textures-shaders",
    "geometry-meshes-uvs", "import-fbx-prefabs", "placement-layout-design", "colliders-physics",
    "udonsharp-networking", "vrchat-sdk-upload-components", "performance",
    "unity-editor-scripting-mcp", "agent-workflow-verification", "assets-sourcing",
    "audio-video-ui", "blender-modeling",
]


def front_matter(path):
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    if not match:
        return None
    data = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("\"'")
    return data


def valid_sources(value):
    """Optional `sources:` field: `in-house`, or a [list] of http(s) URLs."""
    if value == "in-house":
        return True
    if not (value.startswith("[") and value.endswith("]")):
        return False
    items = [item.strip() for item in value[1:-1].split(",")]
    return bool(items) and all(re.match(r"https?://\S+$", item) for item in items)


def build_index(errors):
    groups = collections.defaultdict(list)
    for path in sorted((KNOWLEDGE / "notes").glob("*.md")):
        data = front_matter(path)
        if not data or data.get("topic") not in TOPICS or not data.get("summary"):
            errors.append(f"bad front matter (need a known topic and a summary): {path.name}")
            continue
        if "sources" in data and not valid_sources(data["sources"]):
            errors.append(f"bad sources (want [https://..., ...] or in-house): {path.name}")
        groups[data["topic"]].append((data.get("title", path.stem), path.name, data["summary"]))
    lines = [
        "# Knowledge index", "",
        "One lesson per file in `notes/`. Each has front matter (`title`, `topic`, `tags`, `summary`, "
        "optional `sources`; no `sources` means in-house, see ../CREDITS.md) "
        "and a Symptom → Cause → Fix → Verify body. Grep `notes/` for keywords, or browse by topic below.", "",
        "## Topics", "",
    ]
    lines += [f"- [{t}](#{t}) ({len(groups[t])})" for t in TOPICS if groups[t]] + [""]
    for topic in TOPICS:
        if groups[topic]:
            lines += [f"## {topic}", ""]
            lines += [f"- [{title}](notes/{name}) — {summary}" for title, name, summary in sorted(groups[topic])]
            lines.append("")
    (KNOWLEDGE / "INDEX.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return sum(len(v) for v in groups.values())


def main():
    errors = []
    count = build_index(errors)
    print(f"{count} notes indexed -> {KNOWLEDGE / 'INDEX.md'}")
    if errors:
        print("\n".join(errors))
        sys.exit(1)


if __name__ == "__main__":
    main()

# Writing a knowledge note

One lesson per file in `.omp/knowledge/notes/<kebab-slug>.md`. Grep `.omp/knowledge/notes/` for an
existing note on the same lesson before adding one; extend it instead of duplicating.
[INDEX.md](INDEX.md) is generated; never edit it by hand. After adding or changing a note, run
`python .omp/scripts/build-knowledge-index.py`: it regenerates `INDEX.md` and fails on bad front matter.

## Front matter

```yaml
---
title: Lightmap EXRs land on disk after the bake's completion signals
topic: lighting-baking
tags: [lightmapping, isRunning, bake verification]
summary: One sentence stating the lesson, readable without the body.
sources: [https://example.org/the-guide]   # optional; omit (or `in-house`) for your own findings
---
```

`topic` is exactly one of:

`lighting-baking`, `probes-reflection-and-light`, `materials-textures-shaders`,
`geometry-meshes-uvs`, `import-fbx-prefabs`, `placement-layout-design`, `colliders-physics`,
`udonsharp-networking`, `vrchat-sdk-upload-components`, `performance`,
`unity-editor-scripting-mcp`, `agent-workflow-verification`, `assets-sourcing`, `audio-video-ui`,
`blender-modeling`.

## Body

**Symptom** (what the user or a check saw) → **Cause** → **Fix / rule** → **Verify** (how to
prove the fix). Keep the measured numbers. Add **Pitfalls** or **Related** links to other notes
when useful.

## Sanitizing

Notes are shared across worlds and users, so write them project-agnostic:

- No project or world names, people, personal paths (user-profile folders, local asset drives),
  owned purchases, session dates or "the user prefers" anecdotes. Describe the context neutrally
  ("a large open-world scene", "a night interior"). Credited creators by public handle are the
  one exception.
- Name MCP tools generically ("the Unity MCP `execute_code` tool"), not by one host's syntax.
- Paths are relative to the workspace root (`.omp/skills/world-pipeline/references/review-protocol.md`).
- Every external source (guide, doc, repo, asset site, talk) goes in `sources:` with its real URL,
  and gets an entry in [CREDITS.md](../CREDITS.md). Never invent a URL.

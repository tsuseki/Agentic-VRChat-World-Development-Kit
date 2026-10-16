---
name: spatial-design
description: Architecture and interior-design rules for social VRChat worlds — space archetypes (A1–A5), massing, intimacy gradient, seating and clearances, scale from the reference eye height — with case studies of past worlds. Load before drawing a floor plan or greybox, building out or reviewing any area. Clip planes and world extent live in `.omp/skills/clip-planes/SKILL.md`.
---

# Spatial design

The rules every world-pipeline stage builds to and every reviewer judges against. Citations in agents
and reviews read `spatial-design §N.N`; they point into the guide below.

## Files

| File | Holds | Open when |
|---|---|---|
| [references/spatial-design.md](references/spatial-design.md) | **The guide**: §0 top rules, §1 archetypes (§1.5 archetype → sections table), §2 massing, §3 per-archetype rules, §4 intimacy gradient, §5 shared rules and dimensions (§5.9 eye-height scaling, §5.11 dimension table), §6 pointer to `.omp/skills/clip-planes/SKILL.md`, §7 case-study lessons, §8 checklists and reviewer shots | Always; start at §1.5 with the target area's archetype |
| [references/case-studies/](references/case-studies/) | Postmortems of past worlds: what users rejected and the fixes they accepted | Before A.3 concepts; append one when a world finishes |

## Who reads what

- `world-architect`, `layout-reviewer`: the whole guide.
- `world-builder`: C.1 the sections named in its "Build-out"; C.2 `.omp/skills/clip-planes/SKILL.md`.
- `dressing-reviewer`: §1.5, the §3 row per archetype, §4, §5.1–§5.4, §5.9–§5.11; clip-planes §6.
- `final-reviewer`: §1.5, §3 Light rows, §5.4, §8.3; `.omp/skills/clip-planes/SKILL.md`.

Stage order, gates and reviewers: `.omp/skills/world-pipeline/SKILL.md`. A user's reference that contradicts a rule
wins for that world; record it in WORLD.md.

Placement and layout lessons checklist (read before placing or dressing): [references/lessons-placement.md](references/lessons-placement.md).

Sources: SOURCES.md (not needed to use this skill).

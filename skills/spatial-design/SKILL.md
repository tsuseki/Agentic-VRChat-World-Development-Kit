---
name: spatial-design
description: Architecture and interior-design rules for social VRChat worlds — space archetypes (A1–A5), massing, intimacy gradient, seating and clearances, scale from the reference eye height — with the sourced research and case studies behind them. Load before drawing a floor plan or greybox, building out or reviewing any area. Clip planes and world extent live in `.omp/skills/clip-planes/SKILL.md`.
---

# Spatial design

The rules every world-pipeline stage builds to and every reviewer judges against. Citations in agents
and reviews read `spatial-design §N.N`; they point into the guide below.

## Files

| File | Holds | Open when |
|---|---|---|
| [references/spatial-design.md](references/spatial-design.md) | **The guide** (the digest of everything below): §0 top rules, §1 archetypes (§1.5 archetype → sections table), §2 massing, §3 per-archetype rules, §4 intimacy gradient, §5 shared rules and dimensions (§5.9 eye-height scaling, §5.11 dimension table), §6 pointer to `.omp/skills/clip-planes/SKILL.md`, §7 case-study lessons, §8 checklists and reviewer shots | Always; start at §1.5 with the target area's archetype |
| [references/research/architecture-interior.md](references/research/architecture-interior.md) | Massing, plan organisation, dimensions, plausibility | A massing or plan rule needs context |
| [references/research/social-architecture.md](references/research/social-architecture.md) | The five archetypes; Gehl, Whyte, Oldenburg, residential and hospitality planning, level changes | An archetype rule needs context |
| [references/research/social-vr.md](references/research/social-vr.md) | VRChat platform facts, proxemics, density and capacity in VR | Capacity, voice range, spawn, VR-specific pitfalls |
| [references/case-studies/](references/case-studies/) | Postmortems of past worlds: what users rejected and the fixes they accepted | Before A.3 concepts; append one when a world finishes |

Inline tags in the guide and research resolve in [SOURCES.md](SOURCES.md), grouped by research file. Open it only to check where a claim came from.

## Who reads what

- `world-architect`, `layout-reviewer`: the whole guide.
- `world-builder`: C.1 the sections named in its "Build-out"; C.2 `.omp/skills/clip-planes/SKILL.md`.
- `dressing-reviewer`: §1.5, the §3 row per archetype, §4, §5.1–§5.4, §5.9–§5.11; clip-planes §6.
- `final-reviewer`: §1.5, §3 Light rows, §5.4, §8.3; `.omp/skills/clip-planes/SKILL.md`.

Stage order, gates and reviewers: `.omp/skills/world-pipeline/SKILL.md`. A user's reference that contradicts a rule
wins for that world; record it in WORLD.md.

Related lessons: [knowledge index → placement-layout-design](../../knowledge/INDEX.md#placement-layout-design)

---
title: Lie-on seating added beside existing layouts read as random clutter; replacing whole groups fixed it
topic: placement-layout-design
tags: [seating, lie-on furniture, daybed, sofa group, door zone, spacing, archiving, LODGroup, decor]
summary: Daybeds dropped into open floor and doorways beside the existing sofa groups read as clutter; replacing each group as one composition (same U/L, lie-on pieces), a scripted door-zone check, end and table spacing rules, moving decor off archived spots and rebuilding LOD chains fixed it.
---
**What was built:** a finished multi-room residence had to gain lie-on seating (daybeds, sofa-beds with chaise ends) for small-avatar groups. The first pass added six daybeds to rooms whose sofa groups were already composed, placed by free floor area: on a sun deck in front of the bar, inside a glazed doorway, beside a lounge U.

**Symptom (owner's words):** one daybed stood alone in the middle of a sun deck in front of the bar, facing nothing, and the owner reacted with an angry "seriously"; "don't just place stuff in front of the doorways"; on a deck U of three sofas, "these are too close together" (arms touching around a small table); after archiving, "don't put the book on the bed" (a decor book from an archived table now lay on the new round bed). Asked what they wanted instead: "I want the main area redesigned so it's like original but couches have extensions for laying down" and "I still want the general U shape with different pieces".

**Cause:**
- New pieces were *added beside* composed groups instead of replacing them, so each read as a stray object with no relation to a table, view or the other seats.
- Placement used open floor, not use: doorways and the routes behind them are open floor too.
- Groups were assembled by footprint, so sofa ends touched and seats sat at uneven distances from the table.
- Archiving the replaced pieces left their tabletop decor behind on whatever now stood there.
- The replaced pieces were members of perf merges and LOD groups. Removing them broke the LOD chains: nine LOD-copy renderers stayed enabled outside any active LODGroup and drew on top of the real objects at every distance (rug, books, lamp, vase, planter, stool), and an archived sofa's LOD1/LOD2 still rendered.

**Fix / rule:**
- New furniture **replaces** the existing layout of its spot as **one composed group**, keeping the original composition (the same U or L, same opening side, same rug, table and view) with lie-on pieces forming it; never add pieces beside or between an existing group.
- Nothing stands alone in open floor: every piece faces a view, table, fire or other seats and sits on a rug or against a wall or rail.
- Door zones, checked by script for every door, sliding door and glazed opening, both sides: a box ≥ 1.2 m deep × (door width + 0.3 m each side) with no furniture in it, plus a ≥ 0.9 m clear route onward (scene metres).
- Group spacing: sofa ends ≥ 0.35 m apart or a side table between them; seat fronts ≈ 0.45–0.55 m from the coffee table.
- When archiving a piece, move or archive the decor that stood on it.
- After archiving pieces that were in perf merges or LOD groups, rebuild those LOD chains with the perf tooling.

**Verify:** door-zone script reports every door clear; measured end gaps and seat-to-table distances printed per group; scene query: no enabled renderer of a LOD copy outside an active LODGroup and no LOD member whose source is archived (0 found, after the broken state reported 9); eye-height captures of each replaced group before/after; a sweep for decor resting on beds and seats.

**Related:** [moving-furniture-orphans-tabletop-dressing](moving-furniture-orphans-tabletop-dressing.md).

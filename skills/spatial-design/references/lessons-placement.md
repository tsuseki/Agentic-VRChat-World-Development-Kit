# Placement and layout lessons

Scripted placement, seating, wall mounting, dressing audits, scatter and open-map layout as they go wrong in practice.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Seating props on what is really under them

- **Re-seat a cloned prop on the destination floor: `y = donorY + (destFloor − donorFloor)`, then lift the group root by `floor − lowest renderer bounds.min.y`** — copying the donor Y across a few-centimetre level step buries or floats every clone, and it only shows at eye height.
- **Seat simple props from `bounds.min.y`; seat bundle prefabs (vehicles with cameras/UI, rigs with unposed skinned meshes) by a downward raycast with their own colliders disabled and `Physics.SyncTransforms()` first, only where the ground collider is the visible surface** — bundle bounds span the map, skinned bounds are junk, and the ray otherwise hits the object's own collider. Place stools on a ring outside the counter, not at old blockout XZ, or they land on the top. World-builder "Unity rules → Placement" is the base rule.
- **Test each prop against every pad, podium, step and plinth in its footprint and seat it on the highest** — a single global floor height puts props inside overlays; a prop that "renders as nothing" is usually occluded, so raycast camera → prop to name the occluder.
- **Where the walkable collider is a separate proxy, take floor height from the visible floor mesh's upward triangles, not `Physics.Raycast`** — a flat collider proxy sits under a cambered visible deck, so props seated to it vanish while every clearance metric reads perfect; on camber, fit a plane over the footprint.
- **Before floor-seating an unfamiliar pack prop, check its source folder and render it once from a low oblique angle** — lowest-vertex seating never fails, so rigging- or ceiling-mounted props end up balanced on a corner; a small contact patch means mount it as authored or pick another prop.
- **In a collider-free world verify support renderer-against-renderer (gap within about −0.30…+0.05 m), then contact-test face-mounted parts axis-agnostically** — downward raycasts pass through colliderless troughs and beds and bury the one real floater under a hundred false ones.
- **Find free space on a surface with a largest-free-interval scan over sorted occupant spans and assert every placed prop's bounds lie inside the surface** — min/max of occupants hides interior gaps and let a vase hang 13 cm off a table edge.
- **Scale a prop to fit its container before clamping its position, and iterate two or three passes** — a push-inside clamp on a prop wider than its container cancels itself and leaves it overhanging both sides with no error.

## Moving, parenting and editing dressed rooms

- **When moving furniture, detect its tabletop dressing by support surface (highest renderer under the prop centre with `max.y ≤ base + 0.05`) and move each group by one shared delta** — dressing is usually authored as room siblings, so moving the table strands it mid-air; re-seating items one by one destroys the arrangement.
- **Move scripted composite props as the whole sibling set by one `+= delta` (skip companions whose parent is in the set), and sweep the old footprint for left-behind trim** — legs, lantern parts, soil caps and nosings are flat siblings; verify with a pairing gap test, not an overlap count.
- **Never parent a new prop under a transform with non-unit `lossyScale`; walk up to a unit-scale ancestor** — boards, slabs and walls are scaled primitives and their scale multiplies into the children (books came out 9 mm tall).
- **When mirroring a room, solve each asymmetric prop's yaw from its measured back axis (centroid of its tallest 25% of vertices), then re-seat** — `rotY' = −rotY` is right for directions but flips meshes backwards; set L-sectionals square by hand and leave low curved seats.
- **Cutting a door into a dressed wall: inventory everything on the wall plane, shift whole runs with their sibling props, retire what cannot move, rebuild the head as its own piece, and split the wall collider into segments** — the opening lands on dressing, and the old full-length collider becomes an invisible wall in the doorway.
- **Before choosing where to cut an opening, raycast for floor on both sides of the wall in 0.5 m steps** — a bay that looks symmetric on the elevation can open onto a double-height void, and a thin void-guard collider looks like any mullion.

## Replacing and composing furniture groups

- **Lie-on or new seating replaces the spot's existing group as one composition (same U or L, rug, table and view), never added beside it** — daybeds dropped beside composed sofa groups and into open floor read as random clutter; replacing whole groups fixed it.
- **Nothing stands alone in open floor: each piece faces a view, table, fire or other seats and sits on a rug or against a wall or rail** — a daybed alone mid-deck, facing nothing, was the worst-received piece.
- **Check door zones by script for every door and glazed opening: ≥ 1.2 m deep × (door width + 0.3 m each side) free of furniture, plus a ≥ 0.9 m route onward** — placing by free floor area puts pieces inside doorways, which are free floor too.
- **Space groups by measurement: sofa ends ≥ 0.35 m apart or a side table between, seat fronts ≈ 0.45–0.55 m from the coffee table** — footprint-assembled U groups jammed arms together round a small table.
- **When archiving furniture, move or archive its decor, then rebuild the LOD chains it belonged to and assert no LOD copy renders outside an active LODGroup** — a decor book ended up on a new bed, and nine orphaned LOD copies drew over the real objects at every distance.

## Wall-mounted items and trim

- **For each wall-mounted prop assert it is on the occupied face, facing into that room, and inside a solid wall segment** — "at the wall" is ambiguous by the wall's thickness, so whole schemes end up on the far face (showing up as a light leak in the next room) or inside door openings.
- **Mount trim proud of a wall from the wall renderer's measured face coordinate and the room side taken from the room's renderer-bounds centre (not a ray from inside the wall), print the proud distance per piece, and include walls in the clash test** — a remembered plane or the wrong side builds the assembly inside the wall silently; any depth change to a wall plane needs a canvas-vs-frame re-audit.
- **Cast a short ray along each wall-hung object's back normal; no hit within about 0.5 m means it is floating — relocate onto continuous wall runs found by a 0.5 m sweep, taking its wash light along** — art placed on a coordinate line hangs in void and renders black; judge it from the room side, as thin canvases look buried from behind.
- **Use `RaycastHit.normal` as-is for "into the room"; never negate it, and check facing against the room's bounds centre rather than a ray from the prop** — the normal already points back at the caster, so negating it turned 21 pictures into the wall, and a ray started inside the wall collider reports nothing.

## Shelves and occupancy

- **After any shelf-dressing pass, resolve each object's board from its `min.y` against the measured per-column board heights and flag anything reaching the next board up** — a correctly seated object can still spear the next board, and a uniform pitch misassigns boards on mixed bays; the same check covers nightstands under art and counters under cabinets.
- **Size shelf props to the measured bay height, found per column from upward-facing triangles, and seat them on the board below** — the shelf AABB says nothing about bay headroom (real bays 0.17–0.39 m in a 2.74 m case); contents overlapping the shelf AABB are normal, not a clash.
- **Filter surface-occupancy scans to exclude the shelf's own boards and rails, wall art behind, and anything spanning the whole bay or taller than the measured bay opening** — lips and pictures count as occupants, so empty boards read as full; treat a zero-gap result as a red flag and print the occupant list.
- **Judge planters by geometry plus a render from just above the rim, not a name search for `*soil*`** — many plant models carry pot, soil and foliage in one mesh, and substring matches flag walls and glazing.

## Scripted sweeps, searches and room geometry

- **Write an occluder sweep as a sightline test (linecast or renderer-bounds ray from eye height to the target) with a height cut and a room-spanning-size cut, and log every delta** — a bounding-band test moved corridor-length ceiling lights and the target's own downlight.
- **Bulk align/centre sweeps need a semantic eligibility filter, a clash test against every renderer in the room, and a slightly negative threshold so exact contact counts** — container membership picks wrong targets, class-scoped tests miss the painting, and `overlap > ε` cannot see abutment; re-check already-closed findings afterwards.
- **In free-spot searches exclude the moved object's whole subtree (`IsChildOf`) and build occupancy from renderer AABBs in a body-height band, then verify with an independently written overlap pass** — self-matching child transforms reject every cell, and `Physics.CheckSphere` sees straight through colliderless props; physics is fit only for floor height where the floor collider is the visible surface.
- **Classify objects by storey before any plan-space (XZ) containment test or bulk delete, and run bulk deletes from a committed scene** — an XZ test deleted legitimate balcony plants that overhang the ground slab.
- **Derive room extents and floor height from the 10th/90th percentile of the room's own renderer centres and `bounds.min.y`** — a few stray children blow the renderer-union AABB out into neighbouring rooms, and upper rooms get shot at ground eye height.
- **If a measurement stays constant across a swept parameter, it is measuring the wrong geometry; filter radially from the axis, and widen the search before relaxing the target** — a parasol yaw sweep kept finding its own mast.

## Measuring emptiness and readability

- **Find orphaned props by casting about 24 rays outward from the prop against renderer AABBs (not `Physics.Raycast`, which misses colliderless props) and ranking by mean clear distance, after excluding outdoor sets** — centre or edge distance to the nearest neighbour cannot see that the one neighbour is the only thing within 8 m.
- **Measure room emptiness by wall-mounted items per wall run, largest bare floor square, furniture coverage and counts with clusters collapsed — and ask the scene reviewer which rooms read empty first** — props per m² scored the emptiest-looking room among the fullest (bottles counted like sofas, a 13 m wall with nothing on it).
- **Find bare walls by projecting props that intersect an eye-height band (about floor +0.9…+2.2 m, up to 0.6 m deep) onto each real wall, excluding the wall's own cladding, and report gaps ≥3 m with coordinates** — density, AABB-edge runs and point probes overreported bare wall up to 10×.
- **Rotate furniture clusters ±6–12° and jitter small items, and end the entrance sightline on a focal piece (not a mirror)** — scripted dressing lands on a perfect grid; this applies spatial-design §5.3 and §5.10.
- **Choose a small prop's finish against the surface it is seen against and render it framed with that backdrop** — a white vase on a white back panel read as a smear while every numeric check passed.
- **When review says a prop reads as a plain box, model the 2–3 features people identify it by, plus a small emissive cue in dark rooms** — albedo and smoothness tweaks only produce a nicer box.

## Planting and scatter

- **Measure bed coverage as the fraction of soil samples hidden by any plant footprint (target ≥70%) and place the next plant at the uncovered sample farthest from canopy** — plants per m² can be uniform while some beds look bare.
- **Scatter to the container edge: inset by at most the plant's base radius and cap plant size at the edge instead** — an inset grid leaves a bare band along the near kerb, the most visible zone from eye height.
- **Pick the mass-planting species by measured silhouette opacity per 1k tris, decimating before measuring** — scanned shrubs at ~5% opacity never hide the ground at any count; broadleaf (~25–30%) does.
- **On large maps weight scatter acceptance by distance to the play path with a noise mask, and emit into a spatial grid of merged meshes with a fresh UV2 unwrap per combined mesh** — uniform scatter reads as a few specks, one renderer per instance or one map-wide mesh defeats culling, and merged source UV2s overlap.

## Layout, sightlines and open maps

- **Block out to the WORLD.md reference avatar with EditorOnly capsules, keep separate teleport areas ≥200 m apart yet near the origin (±200 m slots, |centre| + half-extent < 256 m), and wire scripts only after the layout settles, with arrival points parented to their structures** — premature wiring is deleted as layout iterates; spacing matches the clip-planes skill and scale follows spatial-design §5.9.
- **Plan vehicle areas as circulation: shared aisles and a turnaround apron first, then bays (≈5.2 m pitch, ≈9.25 m aisle), roads uniformly wide** — dense packing left back-row cars driving through others; under a post grid, put tables at post-grid midpoints.
- **Turn "you should see the route from here" into a visible fraction by raycasting route samples from the reference eye height, and raise viewing areas onto a shelf** — at ground level a straight is edge-on; keep everything in a raised area relative to its origin and height so a shelf change doesn't bury it.
- **Review exploration landmarks at 2–15 m from the arrival viewpoint at the WORLD.md reference eye height; distance silhouette is optional** — a stone circle read as a ring only from above; keep landmarks visible from the route but not beside it, and off tile-seam coordinates.
- **Put information drivers must read on the start/finish gantry, wide and single-row if the band is short** — a trackside board cannot face oncoming drivers without overhanging the road.
- **Of two duplicate markings, keep the position of the one the trigger, checkpoint or spawn sits on and move the better-looking geometry there** — a visual reviewer cannot see triggers; shader-painted markings live in material properties, and a hidden decal's baked shadow stays until the rebake.
- **Render world-thumbnail titles with Pillow and a real font at one fixed layout (centred, block centre ~45% from top, widest row ~57% of width, 1200×900)** — image models drift in size, position and font and misspell; full rules in `.omp/skills/vrchat-world-thumbnail/SKILL.md`.

---
title: 'Lamp too bright' usually means the spill; the fixture's own glow is a separate knob
topic: lighting-baking
tags: [lamps, emission, BakeryPointLight, BakeryLightMesh, spill, night interior, brightness feedback]
summary: A lamp's spill on the room (baked emitter intensity) and the fixture's own appearance (shade emission/colour) are independent; 'too bright' and 'too dark' can both be true of one lamp, and fixing it moves the two knobs in opposite directions.
---
**Symptom:** Feedback on a lamp seems contradictory: "the light source should be dimmer but the shade should be lighter … less light on the bed and roof." The lamp washes out the room while still looking like a dull box.

**Cause:** Two independent controls:
- **The emitter** (`BakeryPointLight` + `BakeryLightMesh` intensity) controls the spill: the wash on bed, wall, ceiling. When a complaint mentions the room, this is almost always what "too bright" means.
- **The fixture's appearance** (`_EmissionColor` + `_Color` on the shade) controls whether the lamp reads as switched on. If the shade carries a `BakeryLightMesh` it is permanently probe-lit and its emission is added straight in the shader, so **this axis needs no bake**: iterate and measure it freely, bake once at the end.

**Fix / rule:** Move both, in opposite directions. Before assuming two brightness notes conflict, check whether one is about the room and the other about the object. When two readings of an instruction lead to opposite edits, ask: a bake plus re-review costs minutes, the question seconds.

**Reference:** a cozy night interior signed off at room mean luminance ~0.14 and probe L0 mean ~0.063, after several rounds of dimming emitters by 0.6-0.85x. Dark rooms with small warm pools usually need to be dimmer than a first pass suggests.

Related: [bakery-light-mesh-traps](bakery-light-mesh-traps.md)

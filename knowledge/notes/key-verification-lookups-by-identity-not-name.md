---
title: Key spatial verification lookups by identity, not by object name
topic: agent-workflow-verification
tags: [verification, duplicate names, instance ID, metric sanity, containment]
summary: A name-keyed lookup pairs an object with a same-named stranger across the map; an impossible metric value means the check is broken, not the scene.
---
**Symptom:** A containment check reports dozens of plants overhanging their bed, worst 1193 m, in a 60 m world.

**Cause:** Several renderers in different beds share the name `Soil`. The verifier found each plant's host bed by name and measured the distance to a same-named bed a kilometre away.

**Fix / rule:** An impossible magnitude indicts the measurement. Before fixing anything, sanity-check the value against the world's own extent: a defect cannot be larger than the thing it lives in. Then, strongest first:
- Key by identity: hold the `Renderer` reference or an instance ID, never the name.
- If you must group by name, generate unique names at build time (`Bed_<NN>_Soil`).
- Prove containment inside the generator, against the bed it just populated, while that reference is still in hand. An after-the-fact verifier has to re-derive the pairing, and that is where it goes wrong.

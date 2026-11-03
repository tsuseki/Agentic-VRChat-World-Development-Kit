---
title: Code builds boxes only; source or model every other shape
topic: assets-sourcing
tags: [generator, primitives, asset-finder, blender, tripo, structures]
summary: Machines, tanks, gates and trusses built in Unity from code-generated lathes, tubes and lattices read as faceted greybox next to their concept art; a data generator should make boxes only, and every other shape should be an imported asset from the library, a Blender kit or image-to-3D.
---

**Symptom.** A structure pass placed 30 themed structures (tanks, a sluice with a radial gate, pump
modules, a reactor, cranes) into large halls. Every one was generated in code: prisms, lathes for
cylinders and domes, tubes for pipes and lattice functions for trusses, emitted as vertex data and
built into meshes by an editor script. Next to the concept sheets they read as faceted primitives
(the radial gate was a 12-sided drum, the pump module a blank box). Both reviewers returned NEEDS
WORK (style 4/10), and the user rejected the approach outright.

**Cause.** The pipeline had asset-finder, blender-modeler and image-to-3D, but they were only
called for furniture and props. Structure passes were owned by the generator, which had already
made massing, so it was extended to "detail" shapes it can't make well. No rule said where code
geometry stops.

**Fix / rule.**
- Code (primitives, generators, editor builders) makes **boxes only**: slabs, decks, walls, plinths,
  quays, beams, square towers, stair treads and landings, greybox massing.
- Every other shape is an imported prefab matched to its picked concept sheet, sourced in this order:
  1. **asset-finder:** the local library, owned packs and free sources;
  2. **blender-modeler:** a low-poly reusable kit of simple geometric pieces (tanks, domes, pipes, flanges, trusses, rails, caged ladders, drums, cabins, waterfall ribbons);
  3. **image-to-3D:** organic or irregular pieces (crystals, complex machines, hulls, statues), cleaned in Blender;
  4. trees come from the tree tool.
- The generator places those prefabs as instances.
- Every structure gets a parts list before it is built, giving each part's source: box, library, kit or image-to-3D.
- Reviewers treat a code-built non-box shape as a blocker.

**Verify.** For each structure the report lists its parts and sources. A scene audit finds no
generated mesh with curved or lattice topology under the structure roots, only boxes and prefab
instances.

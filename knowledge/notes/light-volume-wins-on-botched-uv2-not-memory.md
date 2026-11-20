---
title: Light Volumes win on botched-UV2 objects, not on memory; texels per chart predicts the scuffed bake
topic: lighting-baking
tags: [VRC Light Volumes, lightmap, UV2, texels per chart, small props, voxel size]
summary: In a 16-object lab bake, objects with a botched UV2 (few texels per chart) looked scuffed on the lightmap and clean on a Light Volume at any voxel size, while self-shadowing objects looked better on the lightmap; memory differed by only ~0.1 MB for small props.
---
**Symptom:** Small statues and fruit baked with pale patches and blotches on the lightmap; on a Light Volume they looked clean. Pillows looked bad when moved to volumes.

**Measured (lab scene, one cell per object, Bakery full bake at each class's median world density, volumes at 0.1 / 0.25 / 0.5 m):**

| Object | Texels per chart / charts < 4 texels | Better on |
|---|---|---|
| Bust statue, figurine, lemon, potted plant, wicker basket | 0.05–1.2 / 79–100 % | Light Volume (all voxel sizes) |
| Sofa with slats, bookshelf, tree crowns | — | lightmap (volumes leak light through slats and shelves at 0.25–0.5 m; 0.1 m close) |
| Pillow (bare plinth), shelf, planter, street lamp, fern | 18.5 / 30 % (pillow) | equal |

Memory: the 14 non-tree objects cost ~0.12 MB of BC6H lightmap against 0.06 MB (0.25 m) to 0.43 MB (0.1 m) of volume; a 0.1 m volume around one tree costs ~13 MB. In a finished world 3,690 of 3,693 lightmapped objects already sat inside room volumes, so moving them adds no volume memory.

**Rule:** See `.omp/skills/lightmap-allocation/SKILL.md` "Lightmap or Light Volume". Small + complex UV2 + botched at its baked density → Light Volume (0.25–0.5 m is enough); self-shadowing objects, soft goods, furniture bodies and books stay on the lightmap; leafy plants are exempt from the chart test.

**Verify:** Same-camera captures of the object on the lightmap and on its volume; texels per chart computed from UV2 area × |scaleOffset| × atlas size ÷ chart count after the bake.

**Pitfalls:** Bakery's automatic atlas size squeezes or inflates a lab's objects (28–70 % or 1.6–3× of target density): fix the atlas size and set Scale In Lightmap per object before comparing. A lab bake can add objects to the shared `ftGlobalStorage.asset`; restore it afterwards.

Related: [lightmap-vs-light-volume-is-a-per-object-test](lightmap-vs-light-volume-is-a-per-object-test.md), [probe-light-small-objects-instead-of-lightmapping](probe-light-small-objects-instead-of-lightmapping.md)

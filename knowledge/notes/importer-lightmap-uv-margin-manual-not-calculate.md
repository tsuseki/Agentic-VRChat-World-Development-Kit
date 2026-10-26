---
title: Generate Lightmap UVs with margin method Manual; the Calculate margin at a low min resolution eats the islands
topic: import-fbx-prefabs
tags: [ModelImporter, generateSecondaryUV, secondaryUVMarginMethod, pack margin, UV2, fill, lightmap]
summary: The importer's Calculate margin sized for a low minimum lightmap resolution leaves UV2 fill around 0.10 and can collapse islands into a corner; Manual with a margin of about 6 raised fill to about 0.4 and density with it.
---
**Symptom:** Furniture imported with *Generate Lightmap UVs* bakes blurry and dark even at a high Scale In Lightmap: outdoor sofas got about 2.4 texels/m and their pillows baked as black blocks. In a worse case one FBX's texel extent jumped from 25 to 7,939.

**Cause:** `secondaryUVMarginMethod = Calculate` sizes the gutters from `secondaryUVMinLightmapResolution` and `secondaryUVMinObjectScale`. At a low minimum resolution (16 texels/unit) the gutters take most of the 0–1 square: UV2 fill measured 0.10–0.13, so every chart is shrunk to a tenth of the area it could have.

**Fix / rule:** set `secondaryUVMarginMethod = Manual` and `secondaryUVPackMargin` ≈ 6 (pixels for a mesh filling a 1024 map), reimport, then set Scale In Lightmap for the class. Measured fill went to 0.39–0.46, and the same sofas reached 24.5–27.8 texels/m at Scale In Lightmap 4. If Bakery's own UV processing is on, it can reimport and re-pad models during export; keep it consistent with the importer setting.

**Verify:** UV2 fill (sum of UV2 triangle areas) per mesh before and after; post-bake texels/m on the renderer; a near-reach render of the piece.

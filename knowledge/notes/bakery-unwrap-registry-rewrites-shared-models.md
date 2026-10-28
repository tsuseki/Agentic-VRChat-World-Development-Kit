---
title: A Bakery test render can rewrite the lightmap UVs of shared models through its global registry
topic: lighting-baking
tags: [Bakery, unwrap, UV2, ftGlobalStorage, test scenes, model importer]
summary: Bakery's scene export can register every model it touches in `Assets/Bakery/ftGlobalStorage.asset` and add `#BAKERY` padding properties to their `.meta` files, and its postprocessor re-applies its unwrap on every later import, so a test render quietly changes the UV2 of models shared with shipped scenes and breaks their existing lightmaps.
sources: in-house
---
**When:** running a Bakery render in a test or scratch scene that uses models shared with other scenes (promo, world or pack folders), especially in a project normally baked with another lightmapper.

**Symptom:**
- Rocks, lanterns and walls in untouched scenes sampled the wrong lightmap texels after a Bakery trial render elsewhere.
- `git status` showed `extraUserProperties: '#BAKERY{"meshName":…,"padding":[…]}'` added to model `.meta` files, and changes to `Assets/Bakery/ftGlobalStorage.asset` (`modifiedAssetPathList`, `modifiedAssets`, `assetList`).
- It happened with *Unwrap UVs* on. A second export with it off still rewrote three unrelated boulder metas from an older registry entry.

**Cause:**
- Bakery keeps its UV padding and unwrap decisions in a project-wide registry outside the models.
- Its model postprocessor re-applies them on every import.
- Restoring the `.meta` files from git and reimporting therefore re-applies Bakery's UV2.

**Fix / rule:**
- Never enable Bakery *Unwrap UVs* in a comparison or test scene.
- Copy every model a test uses into the test folder with its own import settings, so no test shares a model with a shipped scene.
- To undo:
  - restore `ftGlobalStorage.asset` (and `ftLocalStorage.asset` if present) and the model metas from git;
  - force-reimport the storage asset first, then the models.

**Verify:** after every Bakery run, `git status Assets/Bakery/ft*Storage.asset` and the shared model folders must be clean. Re-render one shot of each scene that shares those models.

**Related:** [glim-backface-black-on-two-sided-foliage.md](glim-backface-black-on-two-sided-foliage.md).

---
title: Importing a .unitypackage can overwrite files inside Packages/ when GUIDs collide
topic: import-fbx-prefabs
tags: [unitypackage, GUID, VPM, Packages, UdonSharpProgramAsset, git]
summary: A .unitypackage places each asset at the path of any existing asset with the same GUID — including VPM packages under Packages/ — silently replacing package code; check git status Packages/ after every import.
---
**Symptom:** After importing a world-gadget `.unitypackage`, compile breaks (`... could not be found`) in a package you didn't touch.

**Cause:** The package bundled an older copy of a library whose installed VPM fork keeps the same GUIDs. GUID identity wins over folder location — Unity treats it as "update existing asset" and overwrites the package's own scripts/prefabs in `Packages/`.

**Fix / rule:**
- After importing any unitypackage into a VPM project, run `git status Packages/`. Modified files there mean a clobber; restore with `git checkout -- <files>`.
- Expect a duplicate `UdonSharpProgramAsset` dropped in `Assets/` pointing at the same script GUID ("referenced by 2 UdonSharpProgramAssets") — delete the `Assets/` copy, keep the package's.
- For texture/recolour packs whose `.meta` GUIDs collide with originals you want to keep, import the images into a separate folder **without** their `.meta` files and use copied materials.

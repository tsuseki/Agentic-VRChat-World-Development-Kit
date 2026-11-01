# Verification lessons

Capture and image-checking lessons for builders and reviewers. Distilled from the knowledge notes for this topic (the older ones are compiled into `SKILL.md` itself); grep .omp/knowledge/notes/ for the evidence.

- **Settle the LOD cross-fade before every compared capture: duration 0.001, render each pose twice, restore** — the first render after a camera jump catches dithered or mixed LOD levels and shows up as false A/B diffs.
- **Check a "leaf halo" at 1:1, in nearest-neighbour crops and against a magenta sky before touching textures** — the image viewer's downscale painted a pale net that no texture or shader variant changed.
- **Find re-shoot cameras by rendering each stored camera with the changed asset's renderers on vs off** — eyeballing misses background appearances and re-rendering everything is slow; inspect masks for water and glitter.
- **Copy a regenerated image to a new name before reading it** — reading it at the same path can show the previous version.

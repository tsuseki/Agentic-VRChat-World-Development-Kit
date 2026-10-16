# Asset sourcing lessons

Proven rules for choosing, fetching and exporting third-party and generated assets, beyond the source list and import checklist in SKILL.md.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Choose by eye, not by metadata

- **Pick pack prefabs from a rendered contact sheet (7–9 candidates in a row at 3/4 view, inside a dark box far from the scene), never by name or triangle count** — pack names hide period and style (a "bookshelf office" was a Victorian armoire), and an open-world rig gets blown out by skybox ambient.
- **Composite candidate images into one labelled contact sheet and look at it before assigning any to a surface** — aspect and resolution checks cannot see sideways, mirrored or off-subject content.
- **Inventory a pack by category before dressing; when a category is empty, build it procedurally (lathed ceramics, upright book runs)** — substituting the nearest wrong prop surfaces as many unrelated-looking review findings; see SKILL.md §Go-to sources for what to buy.

## Fetch and extract

- **Prefer CC0 sources with scriptable downloads (Poly Haven, ambientCG, Quaternius), confirm price on the Asset Store before trusting any "free download" site, and skip URP/HDRP-only packs** — mirrors of paid packs are piracy and URP/HDRP materials import magenta in Built-in RP; keep a downloads index of what came from where. See SKILL.md §License first.
- **Pull a few prefabs out of a big `.unitypackage` by BFS over `guid:` references from the seed prefabs, copying each asset with its `.meta`** — the package is a tar.gz of GUID folders, so 11 prefabs needed ~45 of ~5,800 entries.

## Export packages

- **Before exporting a prefab, walk `GetDependencies` by size and grep the YAML for stray GUIDs; flatten the prefab into a new asset and convert layered PSDs to PNG** — a stale renderer Anchor Override drags another prefab's whole closure in and PSDs balloon size (667 → 109 MB with no visual change); poll the output file when export outlasts the MCP timeout.

## Generated skyboxes

- **Generate 360° skies locally at 2048×1024 with an equirect LoRA, upscale via img2img, make the rolled-strip seam inpaint the last generative step, then boost highlights into a half-float EXR** — every img2img pass re-breaks the wrap seam; FLUX negatives are inert at cfg 1.0, and slow sampling at half GPU power means weights paging from RAM. Match camera height first (SKILL.md §360 panoramas).

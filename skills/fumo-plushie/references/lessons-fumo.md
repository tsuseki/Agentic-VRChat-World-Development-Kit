# Fumo plush lessons

Scope: concept views, image-to-3D generation, Blender prep, lighting choice, pickup setup, fire screams and
placement of fumo-style plush pickups. Distilled from the plush runs of 2026-10-22 to 10-24 (eleven
characters, four test pipelines).

## Concept
- **The user approves the four concept views before any paid 3D generation; a design approval is not a spend approval** — every regeneration from a changed design is paid again, and exit 4 asks for each spend.
- **Give the front prompt a real-fumo photo as construction reference, and from the second plush on an approved plush of the world** — without them the image model draws detailed anime figures (sculpted strands, gradients) instead of flat felt pieces, and each plush comes out in a different style.
- **Name asymmetric features by image side, not the character's side** — "her left eye" gets mirrored; "the eye on the LEFT side of the image" doesn't.
- **Make side and back views as edits of the approved front (reference 1), the character view as reference 2** — independent generations depict a different doll per view, and the 3D model averages them.
- **Fix one detail of an approved front with a "reproduce EXACTLY … change ONLY" edit** — a fresh generation loses everything the user already approved.

## Generation (if the image-to-3d backend is Tripo)
- **Use the newest models only: Smart Mesh P2.0, Topology Quad** — H3.1 multiview meshes (11.5–12k tris) took 73 % of a study's triangles and baked blotchy; a P1.0 retopo was still blotchy and paler.
- **Generate at the minimum quad count the budget allows (1,000–1,500 quads for a 25 cm plush), every candidate at the same count** — 2,000 quads already gave 2,693 faces / ~4.4k tris; bigger counts only spend budget.
- **Texture from the sidebar Texture panel with Remove Lighting on and 2K, not the viewer-bar button** — painted-in shading doubles up with the world's light; 2K costs half of 4K and the shipped texture is 512² anyway.
- **Never run the service's Smart UV on a textured model** — it deleted the texture.
- **A few non-manifold edges on a P2.0 mesh are fine** — 6 pieces, 25 non-manifold edges and 247 charts still baked evenly.

## Blender prep
- **Force the Standard view transform in every Blender script that saves an image, and check the written texture's median colour against its source** — Blender 5's default AgX desaturated every saved texture: (238, 198, 156) came out (191, 171, 152).
- **A clean, smooth surface bakes well, not quads** — a noisy surface makes xatlas cut hundreds of tiny charts; at ~56² texels most texels sit on chart edges and the light breaks into bright and dark spots.
- **Author lightmap UV2 with xatlas in Blender and import with Generate Lightmap UVs off** — Unity's own UV2 on generated meshes filled 2–3 % of the chart.
- **UV0 and UV2 are separate; UV0 seams never show in a bake** — UV0 still matters for texture downscaling (seam bleed) and a tiled felt detail normal (weave turns at every UV0 seam).
- **Remesh + bake from the original (`fumo_remesh_bake.py`) only to keep an approved older shape at budget** — it bakes evenly at 2,800 tris but softens hair strands, ear tips and ahoges.
- **Ship 512² crunched and one material** — a 2K texture on a 25 cm prop is VRAM for nothing; one material is one draw call.
- **Line every new plush up with the existing ones and a 1.4 m figure before Unity** — on a shared shelf a plush of a different height or style reads as a different product.

## Lighting
- **Pickups are never lightmapped: probe-lit, and with VRC Light Volumes an LV-aware material** — a moved object keeps the lightmap of where it was; Unity Standard ignores the volumes.
- **For a plush that stays static, Scale In Lightmap 8** — props 15–40 cm got a median of 6 texels (flat colour); SIL 8 (~56² texels) looked nearly as good as SIL 16; SIL 1 was flat and muddy.
- **Bake AO into the base colour of a probe-lit plush by ray-casting against a watertight voxel proxy** — Cycles AO on layered hair and cloth shells self-occludes into per-chart blotches.

## Pickup and placement
- **Gravity on, VRCObjectSync, proximity 0.1, AutoHold No, one tight BoxCollider, layer Pickup, not static** — kit pickup rules; a plush that stays where it is dropped needs a support, not kinematic.
- **Give every resting spot without a collider a `Rest_*` box on layer Walkthrough (17), top flush with the visible surface** — small furniture has no colliders, so pickups fell through: 26 of 33 bottles before shelf rests, 31 of 33 after.
- **Seat by mesh vertices or a downward ray, not a rotated renderer AABB** — AABB-seated props hovered 5–13 mm.
- **After any play session, re-check every pickup against its support before saving the scene** — pickups that had fallen to the floor in play mode were saved and committed that way.
- **One copy of each character per world: move a plush, never duplicate it; never place clay placeholders** — user rule.
- **Scatter plushies to natural surfaces (sofa seat, sideboard, shelf, window ledge, bed), not walkways or a bare display** — user: "plushies are just floating there, scatter them around the world".

## Fire screams
- **Fire zones cover only the flames, on layer Walkthrough, and never reach a resting plush or its support** — a zone that touched the fireplace ledge would scream at a plush placed there.
- **FumoScream is NoVariableSync** — an UdonSharp program with sync mode None cannot `SendCustomNetworkEvent`; nothing plays.
- **One shared settings object holds the clip** — the user swaps the scream by changing one field.
- **Scream source: 3D, Logarithmic, 0.5–8 m, spatial Near 0.5 / Far 8** — the user's setting; the first build's 12 m range was cut to 8 m.
- **Wait a few seconds after entering play mode before scripted checks** — events sent in the first frames are dropped.
- **Candle flames are not fires** — only fireplaces, fire pits and braziers get a zone unless the user asks.

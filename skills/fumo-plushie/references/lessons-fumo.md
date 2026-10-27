# Fumo plush lessons

Scope: concept views, image-to-3D generation, Blender prep, colour grading, review, lighting choice, pickup
setup, fire screams and placement of fumo-style plush pickups. Distilled from the plush runs of
2026-10-22 to 10-26 (fifteen characters, five test pipelines).

## Concept
- **The user approves the four concept views before any paid 3D generation; a design approval is not a spend approval** — every regeneration from a changed design is paid again, and exit 4 asks for each spend.
- **Give the front prompt a real-fumo photo as construction reference, and from the second plush on an approved plush of the world** — without them the image model draws detailed anime figures (sculpted strands, gradients) instead of flat felt pieces, and each plush comes out in a different style.
- **Name asymmetric features by image side, not the character's side** — "her left eye" gets mirrored; "the eye on the LEFT side of the image" doesn't.
- **Make side and back views as edits of the approved front (reference 1), the character view as reference 2** — independent generations depict a different doll per view, and the 3D model averages them.
- **Fix one detail of an approved front with a "reproduce EXACTLY … change ONLY" edit** — a fresh generation loses everything the user already approved.
- **Legs stay stubby (≤ head height) even when the avatar wears thigh-highs** — the user rejected long legs twice.
- **Simplify fine hair and a patterned top into wide flat locks and a plain full-coverage colour in the front concept** — a busy top and strand detail came back from the 3D model as shredded fringe and speckled cloth.

## Generation (Tripo Studio)
- **Use Smart Mesh P2.0, Topology Quad, polycount 2000, four takes at the same count; no decimation afterwards** — this is Kutsu's recipe (experiment 11a): about 2,700 faces and 4.4–4.5k tris, the user's favourite plush. Plushes built at the minimum quad count, decimated to 2,500 tris and rebaked came out worse ("new ones are kinda crappy"): fringes shredded, eyes smeared.
- **Pick the take from clay views of all sides, not the first take** — eyes and fringe clean, legs short, tail and wings intact; the take that looks best from the front is not always the one that is good from the side (picks were takes 3 or 4 of 4).
- **Texture from the sidebar Texture panel with Remove Lighting on and 2K, not the viewer-bar button** — painted-in shading doubles up with the world's light.
- **Run Smart UV on every plush; unwrap before texturing, or bake the existing texture across with `transfer_bake.py`** — Smart UV removes the texture, but it keeps the mesh bit-identical and cuts Tripo's 1,300–2,500 tiny-island seams down to a few large islands (Kutsu 2,119 → 618).
- **Render and bake with Cycles on the GPU (`cycles_gpu.use_gpu`)** — the same texture transfer took 533 s on the CPU and 19 s on OptiX.
- **When an FBX replaces a Unity asset in place, keep the old node name (`MESH_NAME`)** — Unity names a single-mesh FBX's mesh after the node, so 4 of 11 swapped plushies whose mesh was still called `Fumo_CharN_P2` lost their MeshFilter reference until the node was renamed back.
- **A few non-manifold edges on a P2.0 mesh are fine** — 6 pieces, 25 non-manifold edges and 247 charts still baked evenly; 40–270 non-manifold edges on the 4.5k meshes shipped fine.
- **The API cannot choose these options; Studio credits are separate from API credits** — about 100 credits for four takes plus 10 for the texture, per character.
- **Studio automation needs the logged-in profile and a clean Chrome** — kill only the Chrome whose command line contains the profile directory before each step; positions assume a 1440×900 viewport.

## Blender prep and texture
- **Force the Standard view transform in every Blender script that saves an image, and check the written texture's median colour against its source** — Blender 5's default AgX desaturated every saved texture: (238, 198, 156) came out (191, 171, 152).
- **Keep Tripo's mesh and UV0 as generated; add only an xatlas UV2** — every decimate-and-rebake path drifted UV0 against the texture. A 12 mm rebake cage tore the fringes; uniform decimation smeared Nikki's eyes (a protected face zone only avoids that; it is a fallback for a strict budget, not the default).
- **Author lightmap UV2 with xatlas in Blender and import with Generate Lightmap UVs off** — Unity's own UV2 on generated meshes filled 2–3 % of the chart.
- **UV0 and UV2 are separate; UV0 seams never show in a bake** — UV0 still matters for texture downscaling (seam bleed).
- **Tripo Remove-Lighting textures drift from the concept and must be measured and graded per colour class** — pale blond came out orange (245,185,90 against 229,191,145), dark brown dark red (63,40,38 against 77,57,54), ash hair tan. Grade only the class that drifted, with a class window wide enough that nothing is left unmasked: a narrow brown window left dark red blotches on Mari2; strength 0.5–0.7 where hair and skin drift together; an untouched texture that matches the concept (Nikki) stays untouched.
- **Ship 1024² compressed, crunch off, one material** — crunch smeared the embroidered eyes at 512²; 1024² costs little for a 25 cm prop; one material is one draw call.
- **Clean flat-colour clothing only when it is scuffed** — black clothing speckled, grey hairlines, lilac-tinted white; the Kutsu-way textures came out clean enough on four plushes that this was not needed.
- **Line every new plush up with the existing ones and a 1.4 m figure before Unity** — on a shared shelf a plush of a different height or style reads as a different product.

## Review
- **Run the self-review gate before showing anything: close-ups of face and body beside the best existing plush** — the failure list: eyes smeared or offset, fringe shredded, hair into the eyes, legs too long, colour cast, scuffed clothing, features mirrored, missing inner faces. The first rebuilds of this session were shown without it and were rejected.
- **Use the pipeline's own checks, not replacements** — an earlier build skipped `texture_check.py`, the AO prep and the lineup sheet and used ad-hoc scripts; colour casts and long legs went unnoticed until the user saw them.
- **Vary the close-up camera height per character** — a fixed height cut Monster's and Mari2's eyes off at the crop edge.

## Lighting
- **Pickups are never lightmapped: Light-Volume lit on an LV-aware material** — a moved object keeps the lightmap of where it was; Unity Standard ignores the volumes.
- **For a plush that stays static, Scale In Lightmap 8** — props 15–40 cm got a median of 6 texels (flat colour); SIL 8 (~56² texels) looked nearly as good as SIL 16; SIL 1 was flat and muddy.
- **Baked AO in the texture is optional and rarely worth it** — in the 2026-10-26 A/B (five plushes, Light-Volume-style gradient light, AO at 35 %) the multiplier over the UV islands averaged 0.995 on three plushes and 0.945 on two; the visible effect was a slightly deeper shade under hair and chin, nothing worth a second texture, and no seams on faces. If you do bake it, ray-cast against a watertight voxel proxy: Cycles AO on layered hair and cloth shells self-occludes into per-chart blotches.

## Pickup and placement
- **Gravity on, VRCObjectSync, proximity 0.1, AutoHold No, one tight BoxCollider, layer Pickup, not static** — kit pickup rules; a plush that stays where it is dropped needs a support, not kinematic.
- **Give every resting spot without a collider a `Rest_*` box on layer Walkthrough (17), top flush with the visible surface** — small furniture has no colliders, so pickups fell through: 26 of 33 bottles before shelf rests, 31 of 33 after.
- **Seat by mesh vertices or a downward ray, not a rotated renderer AABB** — AABB-seated props hovered 5–13 mm.
- **After any play session, re-check every pickup against its support before saving the scene** — pickups that had fallen to the floor in play mode were saved and committed that way.
- **One copy of each character per world: move a plush, never duplicate it; never place clay placeholders** — user rule.
- **Plushies are decoration on shelves, at the side of the room** (a shelf first; a sideboard or window ledge where there is no shelf), spread through the world. Never on sofas, chairs, beds, walkways or a bare display. The user said: "plushies are just floating there, scatter them around the world", and later: "don't put fumos on the sofas or beds… they are decoration, put them on the shelves".
- **Never move a plush the user placed himself; check git history before moving one.** The user put a fumo on the gym mirror shelves himself, and an agent moved it back to the bench.

## Fire screams
- **Fire zones cover only the flames, on layer Walkthrough, and never reach a resting plush or its support** — a zone that touched the fireplace ledge would scream at a plush placed there.
- **FumoScream is NoVariableSync** — an UdonSharp program with sync mode None cannot `SendCustomNetworkEvent`; nothing plays.
- **One shared settings object holds the clip** — the user swaps the scream by changing one field.
- **Scream source: 3D, Logarithmic, 0.5–8 m, spatial Near 0.5 / Far 8** — the user's setting; the first build's 12 m range was cut to 8 m.
- **Wait a few seconds after entering play mode before scripted checks** — events sent in the first frames are dropped.
- **Candle flames are not fires** — only fireplaces, fire pits and braziers get a zone unless the user asks.

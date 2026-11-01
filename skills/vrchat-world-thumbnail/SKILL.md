---
name: "vrchat-world-thumbnail"
description: "Shot composition, scouting, title placement, size and legibility rules for a VRChat world thumbnail (world image), review checks, retouching supplied frames, plus a script that renders the title. Use whenever making or reviewing a world image, thumbnail or title card."
---

# VRChat world thumbnail

## Layout

- **Image:** 4:3, exported at 1200×900.
- **Position:** centred horizontally. The text block's vertical centre sits about **45% from the top**, over the main subject.
- **Size:** widest row about **57% of the image width**, never wider. Long names go on two centred rows.
- **Crops:** the full 1200×900 shows only on the website and loading screen.
  - The world-menu tile is a centre crop with a see-through **PC/Quest platform badge at the top right** (nearly opaque on hover zoom). Keep the title and the subject clear of that corner.
  - A dropped portal shows only a **central circle**. The image is squashed horizontally so that the template's ellipses become circles: ×0.91 (the guide's text says "about 33 %"; trust the drawn ellipses, which `title_render.py` uses). Check that the title still reads inside that circle; a full 57%-wide row can touch its edge, so preview the portal crop before finalising.
  - The top and bottom bands survive only on the full view: never put the title there. By default leave them free of any credit or store line; add one only when the owner asks.

## Shot

- **Title on calm sky.** The title and its second row sit on one calm tone, usually sky. Tilting the camera up 6–15° is usually enough.
- **The product is the subject** and fills the lower half. An empty foreground (bare sand, plain lawn) was rejected.
- **The name matches the frame.** A name built on a plant or a feature ("… Coast", "… Lagoon") needs that plant as the subject and that feature visible.
- **Show the place's shape** (a lagoon, an island, a valley) from a raised view a player could reach (5–15 m up) or from an aerial.
- **Side light or back light.** Take the sun direction from the directional light: `toSun = -light.transform.forward`.

## Scouting procedure

1. In the Unity MCP `execute_code` tool, generate 8–13 candidate poses. Height: `Physics.Raycast(new Vector3(x, 300, z), Vector3.down)` + N metres. Rotation: `Quaternion.Euler(pitch, yaw, 0)`; in Unity a negative pitch looks up (Euler x 354 = 6° up).
2. Write one line per pose (name, position, rotation, FOV, near) to a file, so the round can be re-rendered.
3. Render drafts at 640×480 through the one persistent capture camera (`.omp/skills/world-pipeline/references/review-protocol.md` "Capture rig": settle the LOD cross-fade first), then grade them.
4. Draw the real title on every draft with `render(...)` and put them on one contact sheet. Pick from that sheet, never from bare frames: the title changes which frame works.
5. Render finals at 1600×1200 with 2× supersampling, Lanczos-downscale to 1200×900, and run `crop_sheet` for each option.

## Legibility

- **One calm tone behind the title.** Never let it cross a mix of very dark and very bright areas (dark conifers against sky): a navy fill vanished on the trees and a light fill's glow vanished on the sky. Move the camera instead.
- **Dark scene:** a light fill with a soft glow plus a slight dark shadow behind the letters.
- **Pale sky or haze:** a dark fill (e.g. indigo `#1E2B4F`, dark olive `#2C3A1E`) with a white or ivory glow at 0.85–0.9 and `--shadow-alpha 0`.
- It must read at thumbnail size; exact spelling; the scene behind stays unchanged.

## Font and colour

- Pick them to fit the world's theme; there is no house font. Record the choice in the project's `AGENTS.md`.
- **Sibling worlds** (a set by one owner): give each world its own font, and never reuse a font or a name word already tied to another of the owner's worlds.
- Deliver a default name plus two alternatives, each with its second-language name, and one `--preview --themes <theme> ja_sub` contact sheet per world.
- **User's font verdicts so far:**
  - **Liked:**
    - Cinzel SemiBold caps, ivory with an amber glow, on the Penthouse mansion (luxury);
    - the Cozy Airship's rounded retro swash serif, on the Airship itself (cozy).
  - **Disliked:**
    - gpt-image's bold gold poster serif;
    - the Airship retro serif reused on the mansion (wrong theme);
    - the thin ivory serif gpt-image drew for the mansion.

## Render with real fonts, not an image model

Image models drift in size and position and can misspell. Use `scripts/title_render.py`:

- `--preview [--themes ...] [--fonts ...]` builds a font contact sheet;
- `--font X --fill HEX --glow HEX` renders the final at the standard position and size;
- `--sub TEXT [--sub-font K]` adds a smaller second row (e.g. the Japanese name; `ja_sub` fonts carry the glyphs); the whole ink block is then centred at 45 %.
  - A second row that has to read over busy edges (a treeline): `--sub-scale 0.5` (the default 0.38 read weakly) with its own wider, stronger glow, `--sub-glow-alpha 0.85 --sub-glow-blur 0.3`, which reads as a soft local dark band.
- `--credit TEXT` adds one small, quiet line in the bottom band (full view only); only when the owner asks for one;
- `--crops` writes the crop previews: full, menu tile with the badge, hover zoom, portal circle. Crop geometry is measured from Maebbie's template; import `render` / `crop_sheet` to script it.
- Labels on your own contact sheets that include Japanese names need a CJK font (Windows `YuGothB.ttc`); Arial draws empty boxes. The script's sheets already fall back to it.

## Supplied frames and retouching

- Faint vertical streaks over far open sea (smoke or particles) can be retouched: replace the brightened columns with a wide horizontal median of the same rows, restricted to the sea span.
- Never paint pixels that are greener than blue or brighter than 200: those are trees, sand and sky.
- The streak pixels fail the "is sea" colour test themselves, so take each column's sea span from its neighbours (a min/max filter about 61 px wide), or the streak survives on the anti-aliased horizon rows.
- Check at 2× zoom. Cropping the streak out is the alternative.
- Prove the retouch touched only what it claims: `.omp/skills/agent-verification/SKILL.md` §5 "Retouch verification".

## Review checks

For the reviewer, and for the maker before handing over:

- **Title geometry from an ink mask** (bright ink minus the graded raw > 40): widest row as % of width and block centre as % of height, against the 57 % / 45 % standard.
- **Background ring:** mean luminance 2–6 px around the letters; lower reads stronger (68–89 read fine with a glow on a light fill).
- **Hover zoom:** the standard 45 % placement can put the title's top a few px under the badge's bottom edge (a nit).
- **Top band:** judge the sky and horizon band on the full view. A hazy, detail-less top quarter (Laplacian energy ≈ 30× below the subject rows) is a should-fix for a pick.
- **Re-render under an existing title:** prove the placement is unchanged by the title ink pixel count and bounding box (old vs new) and the % of pixels changed > 18/255 inside the title band (≤ 0.06 %).
- Both crops and the portal circle from `--crops`, and the full view at 300 px wide.

Thumbnail lessons checklist: [references/lessons-thumbnail.md](references/lessons-thumbnail.md).

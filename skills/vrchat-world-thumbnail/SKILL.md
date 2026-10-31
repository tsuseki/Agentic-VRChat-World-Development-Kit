---
name: "vrchat-world-thumbnail"
description: "Placement, size and legibility rules for the title on a VRChat world thumbnail (world image), plus a script that renders it. Use whenever making a world image, thumbnail or title card."
---

# VRChat world thumbnail title

- **Image:** 4:3, exported at 1200×900.
- **Position:** centred horizontally. The text block's vertical centre sits about **45% from the top**, over the main subject.
- **Size:** widest row about **57% of the image width**, never wider. Long names go on two centred rows.
- **Crops:** the full 1200×900 shows only on the website and loading screen.
  - The world-menu tile is a centre crop with a see-through **PC/Quest platform badge at the top right** (nearly opaque on hover zoom). Keep the title and the subject clear of that corner.
  - A dropped portal shows only a **central circle**, with the image squashed about 33% horizontally. Check that the title still reads inside a circle centred on the image; a full 57%-wide row can touch its edge, so preview the portal crop before finalising.
  - The top and bottom bands survive only on the full view: fine for credits or update notes, never for the title.
- **Legibility:**
  - a light fill on a dark scene, with a soft glow plus a slight dark shadow behind the letters;
  - it must read at thumbnail size;
  - exact spelling;
  - the scene behind stays unchanged.
- **Font and colour:** pick them to fit the world's theme; there is no house font. Record the choice in the project's `AGENTS.md`.
- **User's font verdicts so far:**
  - **Liked:**
    - Cinzel SemiBold caps, ivory with an amber glow, on the Penthouse mansion (luxury);
    - the Cozy Airship's rounded retro swash serif, on the Airship itself (cozy).
  - **Disliked:**
    - gpt-image's bold gold poster serif;
    - the Airship retro serif reused on the mansion (wrong theme);
    - the thin ivory serif gpt-image drew for the mansion.
- **Render with real fonts, not an image model.** Image models drift in size and position and can misspell. Use `scripts/title_render.py`:
  - `--preview [--themes ...] [--fonts ...]` builds a font contact sheet;
  - `--font X --fill HEX --glow HEX` renders the final at the standard position and size;
  - `--sub TEXT [--sub-font K]` adds a smaller second row (e.g. the Japanese name; `ja_sub` fonts carry the glyphs);
    the whole ink block is then centred at 45 %. A small sub row over a busy band (a treeline) gets its own wider,
    stronger glow with `--sub-glow-alpha 0.9 --sub-glow-blur 0.35`, which reads as a soft local dark band;
  - `--credit TEXT` adds one small, quiet line in the bottom band (full view only), e.g. the asset credit;
  - `--crops` writes the crop previews: full, menu tile with the badge, hover zoom, portal circle. Crop geometry is
    measured from Maebbie's template (vrclibrary.com world-thumbnail guide); import `render` / `crop_sheet` to script it.

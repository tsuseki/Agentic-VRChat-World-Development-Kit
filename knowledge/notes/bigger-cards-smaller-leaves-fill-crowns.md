---
title: Fill a card crown with bigger cards and smaller-leaved sprays, never with dense clump sprays or extra cards
topic: materials-textures-shaders
tags: [trees, foliage, leaf atlas, image generation, prompt, sprays, crown fullness, card size]
summary: Dense foliage-clump sprays plus extra cards measured fuller but read as stacked textures and were rejected; drawing each spray as a bigger open branch with leaves ~1/16 of the image height and scaling cards ×1.6 kept real leaf size and gave a fuller silhouette that was approved.
---
**Symptom:** Olive card crowns showed sky through the crown (sky fraction 0.30–0.41) and notches between clumps in the silhouette. A first fix regenerated the sprays as dense, ragged foliage clumps (cell coverage ~0.23 → ~0.5) and added cards: the sky fraction dropped to 0.20–0.28, but the crowns read as stacked, overlapping textures and were rejected outright ("not actually fuller, just overlapping textures").

**Cause:** Fullness is judged on the silhouette and on how natural the foliage looks, not on coverage. Dense clumps make every card an opaque blob, so overlapping cards show as layered texture sheets instead of a bigger tree.

**Fix / rule:** Keep the sprays open (cells ~20–25 % opaque) and make each card cover more crown: generate each spray as a **bigger branch section with smaller leaves** (olive: 10–14 twigs, 90–110 leaves each about 1/16 of the image height instead of 35–45 at 1/10, "open and airy, NOT a dense clump") and scale every card up by the same factor (×1.6), so the leaves keep their real size. Keep card counts; repair bare limb ends with tip cards rather than adding cards to fill. Bigger cards make edge-on cards streak further past the crown: fade leaf alpha as the card turns edge-on in the shader.

**Verify:** sky fraction inside the crown at eye level ([full-crowns-measure-sky-fraction-inside-crown](full-crowns-measure-sky-fraction-inside-crown.md)) dropped from 0.30–0.41 to 0.20–0.28 on six olives with the same card counts; hand-measured leaf median ~9.5 cm (real 4–10 cm); atlas cells still 18–24 % opaque; an eye-height render shows a continuous outline without layered sheets. The approval came from the person judging the trees, not from the metric.

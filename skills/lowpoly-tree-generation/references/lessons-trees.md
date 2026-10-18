# Tree lessons

Low-poly leaf-card trees: crown fullness, sprays, volume crowns, cards, trunks, atlas layout and foliage shading.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Crown fullness
- **Measure the sky fraction inside the crown silhouette at eye level with `crown_fullness.py` (1.6 m camera, 2× crown width, 4 azimuths, cutout 0.45, bark opaque, silhouette closed 0.6 m and filled above the lowest leaf) and hold dense species ≤ 0.15, cedar ≤ 0.20, open species ≤ 0.30** — sparse-spray crowns at 0.27–0.50 were rejected as "too branchy, not full"; dense sprays plus volume crowns reached 0.03–0.29 at 0.5–3.4k tris and were approved.
- **Regenerate sparse sprays as one dense, ragged, tufted foliage clump per cell before adding cards** — cell coverage 0.23–0.37 → 0.46–0.65 moved olives from 0.41 to 0.20–0.28 sky with no mesh change; smooth oval clumps read as flat solid blobs on the tree.
- **Build opaque column/dome species as a short visible trunk with root flare plus cards on a spindle or ellipsoid volume, with no inner trunk or limbs; keep visible limbs on open species** — a cypress used 84 bark tris and reached 0.03 sky; on olives, figs and pines the limbs are what identifies the species.
- **On dense volume crowns, plan an unculled card count inside the budget** — removing even 5 % of cards moved the silhouette 2–22 cm against a 0.3 cm allowance; branch-structured crowns still pass at 0.10–0.20.

## Leaves and limbs
- **Measure leaf size on dense sprays by hand: leaf px on a grid in 2 atlas cells × card length / cell px** — segmentation reads overlapping leaves as a few big ones (2.97× reported on leaves hand-measured at ~1.1×) and the tool skips volume-crown trees.
- **Turn on `low_tips` for open trees with low limbs: chains with < 3 cards get 7 cards over their outer 2 m and ground limbs below 0.8 m are dropped** — bare limb ends below the card zone read as dead spikes at eye height, and the uncovered-tips check never sees them; off = byte-identical builds.
- **On big lobed trunks use a one-step root flare (about 1.25× over 0.8 m) with flare height scaled to the trunk radius; the ground ring must be the widest** — a multi-ring flare picked up the cross-section wobble and bulged wider 0.3 m up than at the ground, reading as a stone plinth.

## Atlas and shading
- **For one-material trees use a square 2048² atlas with four 3:4 portrait spray cells and a vertical bark strip, imported wrap U Clamp / V Repeat; skip normal maps** — the bark tiles up the trunk with plain UVs in any shader and cards keep the cell aspect, while a square bark tile cost +47–92 % tris (cut UVs) or 4× blurrier bark; stereo VR exposes painted relief on low-poly trees.
- **Fade leaf cards at glancing angles (Crispy Foliage `_EdgeFade` 1, or 0.5 if edge-on cards turn into dots within ~3 m)** — edge-on cards smear into streaks within ~1 m, and the fade changed only 1–2 % of pixels at distance.

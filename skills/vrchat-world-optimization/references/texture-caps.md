# Texture size caps: controlled proof

Capping importer max size on small props saves texture memory without touching the look, when the
mips already render below the cap. It is reversible (importer settings only), but it can still
damage a close view; prove it, don't assume it.

## Selection

Only textures whose every user is a small prop (≤ 2.5 m); never the skybox, architectural
finishes, artwork, fonts or maps someone already protected. Size from UV texel density: colour /
emission ≥ 1024 px/m, normal / data ≥ 512 px/m. Cap the max size and any already-enabled platform
override; leave format, mips, filtering and aniso alone. Save the before values as rollback JSON.

## Controlled A/B/A capture (proven necessary)

Whole-frame diffs lie: in a measured world they reported up to 16 % changed pixels, almost all of
it from artwork still downloading in the background, while the lamp itself was pixel-identical.
And the 0.75 m views missed a real defect: at 0.30 m a five-map cap showed a faint angular seam on
a lamp's dark rim, caused by the metallic and emissive caps. Restoring those two removed it; the
three remaining caps passed review.

1. Freeze content: hide or fully load runtime-downloaded images, record their state, restore after.
2. Poses: the closest reachable distance (≈ 0.3 m from the prop at reference eye height, floor
   under the camera, no capsule overlap), oblique views of rims and bases, and a seated view.
3. Capture **A** (original) → apply caps, reimport, throwaway render → **B** (capped) → restore →
   **C** (original). Two frames per state (first + repeat).
4. Masks: diff the prop's projected region separately from the background.
5. Pass: A vs C pixel-identical (proves reversibility and stable capture); first vs repeat
   identical; background changes ≈ 0; the prop region's A vs B differences low-amplitude, then
   **look at native-resolution crops**. Any coherent line or seam → find the responsible map by
   restoring maps one at a time, and keep only the clean ones.

## Upload size: attribute it, don't guess

Upload size and frame cost are separate problems with separate tools; never quote one as evidence
for the other. After a Build & Test (or upload), open **VRWorld Toolkit → Build Report** (VCC
Curated `dev.onevr.vrworldtoolkit` ≥ 3.5; reads the SDK's Windows/Android build reports): every
built asset by size, groupable by type (lightmaps, skybox, fonts, audio, meshes, textures). Its
**Build Report Comparison** window diffs two builds: capture one before and one after each
size-reduction pass and quote the delta. For compressed vs uncompressed size per asset (some assets
compress far better in the bundle than others), AssetBundleStat (lox9973). Usual surprises: unused
TMP fonts, an oversize skybox HDRI, lightmaps bigger than they need to be, and inactive objects
that still ship (only `EditorOnly` strips; VRWorld Toolkit's `DisableOnBuild` tag only disables).
Review the toolkit's Auto Fixes against workspace rules before applying any (post-processing setup,
crunch defaults).

"""One texture set for the whole tree (one material).

    python tree_atlas.py <tex_dir> <Tex> [--cell 3]          quadrant layout (legacy, SoftCrown shader only)
    python tree_atlas.py <tex_dir> <Tex> --layout column     column layout (any shader)

Reads <Tex>_Leaves_RGBA.png (2048^2, 2x2 cells), <Tex>_Leaves_Cards.json (cells used by the leaf cards) and
<Tex>_Bark_Albedo.png (tileable); the quadrant layout also ships <Tex>_Bark_Normal.png.

Quadrant layout: bark goes into the free quadrant of the 2x2 leaf atlas. Writes <Tex>_Atlas_RGBA.png (leaf cells
untouched) and <Tex>_Atlas.json {"bark_rect": [u0, v0, u1, v1]}. The bark normal ships as its own Repeat texture.
SoftCrown.shader wraps tag-shifted bark UVs into bark_rect (frac + tex2Dgrad); no other shader can.
Bark cell layout (per side): GUTTER px of alpha 0 next to the leaf cells, then PAD px of wrapped bark, then the tile.
--cell: which quadrant takes the bark (0 TL, 1 TR, 2 BL, 3 BR in image space; default = the one no card uses).

Column layout: the bark is a full-height column on the right (u 0.75..1) that repeats vertically; the leaves fill
u 0..0.75. Native sources (<Tex>_Leaves_Cards.json has "layout", written by branch_atlas.py --layout, e.g.
layouts/column_4cells.json: four 3:4 portrait cells already in u 0..0.75) are copied unchanged.
Legacy 2x2 sources are squeezed to 3/4 width (portrait 768x1024 cells, M px transparent rows at the atlas top and
bottom so the vertical Repeat never wraps a stem onto a tip). Import the textures with wrap
U = Clamp, V = Repeat: bark UVs run along the trunk in V without limit and around it inside the column in U,
so any shader repeats the bark with plain UVs. No normal map (low-poly trees, one texture per family; stereo VR
shows painted relief as flat). Writes
  <Tex>_Atlas_RGBA.png    2048^2 albedo + alpha
  <Tex>_Atlas.json        {"layout": "column", "bark_u": [u0, u1] (inner, tileable), "v_per_tile": 0.5,
                           "leaf_map": null (native: leaf UVs kept) or [su, m] (legacy: old leaf uv ->
                           (u * su, v remapped into [m, 0.5] / [0.5, 1 - m]))}
Column (per side, px at 2048): GUTTER alpha-0 next to the leaves, PAD wrapped bark, the tile (inner x 1024,
twice per height). No gutter or pad vertically: the column is exactly periodic over the atlas height.
"""
import json, sys
import numpy as np
from PIL import Image

GUTTER, PAD = 16, 32  # px at 2048

def put_bark(atlas, tile, q, size, gutter, pad):
    """Writes the bark tile (wrap-padded) into quadrant q of atlas (H, W, C) and returns the inner px box."""
    cs = size // 2; col, row = q % 2, q // 2
    x0, y0 = col * cs, row * cs
    inner = cs - 2 * (gutter + pad)
    t = np.array(Image.fromarray(tile).resize((inner, inner), Image.LANCZOS))
    padded = np.pad(t, ((pad, pad), (pad, pad), (0, 0)), mode="wrap")
    g = gutter
    region = atlas[y0:y0 + cs, x0:x0 + cs]
    region[:] = 0
    # gutter keeps the bark colour (edge-extended) with alpha 0: no dark/odd fringe, nothing opaque bleeds
    full = np.pad(padded, ((g, g), (g, g), (0, 0)), mode="edge")
    region[..., :full.shape[2]] = full
    return x0 + g + pad, y0 + g + pad, inner

M_EDGE = 8  # px: transparent rows at the atlas top and bottom (column layout)

def squeeze_rgba(cell, size):
    """Resize a leaf cell premultiplied (no black pulled into edge pixels), then carry the nearest leaf colour out
    into the transparent pixels so mips and other tools never show dark fringes."""
    from scipy import ndimage
    a = cell[..., 3:4].astype(np.float32) / 255.0
    pm = np.concatenate([cell[..., :3].astype(np.float32) * a, a * 255.0], axis=2)
    pm = np.stack([np.array(Image.fromarray(pm[..., i]).resize(size, Image.LANCZOS)) for i in range(4)], axis=2)
    pm = np.clip(pm, 0, 255)
    al = pm[..., 3] / 255.0
    rgb = np.where(al[..., None] > 1e-3, pm[..., :3] / np.maximum(al[..., None], 1e-3), 0)
    solid = al > 0.5
    if solid.any():
        _, (iy, ix) = ndimage.distance_transform_edt(~solid, return_indices=True)
        rgb = np.where(solid[..., None] | (al[..., None] > 0.02), rgb, rgb[iy, ix])
    return np.concatenate([np.clip(rgb, 0, 255), pm[..., 3:4]], axis=2).astype(np.uint8)

def column(d, tex):
    leaves = np.array(Image.open(d + f"{tex}_Leaves_RGBA.png").convert("RGBA"))
    size = leaves.shape[0]; cs = size // 2
    spec = json.load(open(d + f"{tex}_Leaves_Cards.json")).get("layout")
    if spec:  # native: branch_atlas.py --layout already placed the sprays in their final cells; bark strip only
        W = size - spec["bark_w"]
        atlas = leaves.copy(); atlas[:, W:] = 0
    else:     # legacy 2x2 leaf sheet: quadrants keep their place, squeezed to 3/4 width (image space, y down)
        W = size * 3 // 4; cw = W // 2; ch = cs - M_EDGE  # leaf area width, cell width / height
        atlas = np.zeros((size, size, 4), np.uint8)
        for q in range(4):
            col, row = q % 2, q // 2
            cell = leaves[row * cs:(row + 1) * cs, col * cs:(col + 1) * cs]
            y0 = M_EDGE if row == 0 else cs
            atlas[y0:y0 + ch, col * cw:(col + 1) * cw] = squeeze_rgba(cell, (cw, ch))
    inner = size - W - 2 * (GUTTER + PAD)
    t = np.array(Image.open(d + f"{tex}_Bark_Albedo.png").convert("RGB").resize((inner, cs), Image.LANCZOS))
    t = np.concatenate([t] * (size // cs), axis=0)                        # twice per height: exact period
    t = np.pad(t, ((0, 0), (PAD, PAD), (0, 0)), mode="wrap")              # wrap padding left/right
    t = np.pad(t, ((0, 0), (GUTTER, GUTTER), (0, 0)), mode="edge")        # gutter keeps the bark colour
    atlas[:, W:, :3] = t
    atlas[:, W + GUTTER:size - GUTTER, 3] = 255  # bark + wrap padding opaque; gutters alpha 0
    Image.fromarray(atlas, "RGBA").save(d + f"{tex}_Atlas_RGBA.png")
    u0, u1 = (W + GUTTER + PAD) / size, (size - GUTTER - PAD) / size
    m = M_EDGE / size
    json.dump({"layout": "column", "bark_u": [u0, u1], "v_per_tile": cs / size,
               "leaf_map": None if spec else [W / size, m]},
              open(d + f"{tex}_Atlas.json", "w"), indent=1)
    print("ATLAS", tex, "layout column", "native" if spec else "squeezed", "bark_u", [round(u0, 5), round(u1, 5)],
          "inner px", inner)

def main():
    d, tex = sys.argv[1].rstrip("/\\") + "/", sys.argv[2]
    if "--layout" in sys.argv and sys.argv[sys.argv.index("--layout") + 1] == "column":
        return column(d, tex)
    leaves = np.array(Image.open(d + f"{tex}_Leaves_RGBA.png").convert("RGBA"))
    size = leaves.shape[0]
    cells = json.load(open(d + f"{tex}_Leaves_Cards.json"))["cells"]
    used = set()
    for c in cells:
        u0, v0 = c["rect"][0], c["rect"][1]
        used.add(int(round(u0 * 2)) + 2 * int(round((1 - v0 - 0.5) * 2)))
    q = int(sys.argv[sys.argv.index("--cell") + 1]) if "--cell" in sys.argv else min(set(range(4)) - used)
    if q in used: raise SystemExit(f"cell {q} is used by leaf cards {sorted(used)}")
    col, row = q % 2, q // 2
    cs = size // 2
    g = GUTTER  # a stem pinned to the neighbouring cell's bottom edge may spill a pixel row into the gutter
    if leaves[row * cs + g:(row + 1) * cs - g, col * cs + g:(col + 1) * cs - g, 3].max() > 8:
        raise SystemExit(f"cell {q} is not empty in the leaf atlas")
    bark = np.array(Image.open(d + f"{tex}_Bark_Albedo.png").convert("RGB"))
    atlas = leaves.copy()
    bx, by, inner = put_bark(atlas, bark, q, size, GUTTER, PAD)
    atlas[by - PAD:by + inner + PAD, bx - PAD:bx + inner + PAD, 3] = 255  # bark + its wrap padding opaque
    Image.fromarray(atlas, "RGBA").save(d + f"{tex}_Atlas_RGBA.png")
    # inner bark box -> UV (v up)
    u0, u1 = bx / size, (bx + inner) / size
    v1, v0 = 1 - by / size, 1 - (by + inner) / size
    # the bark normal map tiles on the unwrapped bark UVs directly: same period as this rect
    json.dump({"bark_rect": [u0, v0, u1, v1], "bark_cell": q, "leaf_cells": sorted(used)},
              open(d + f"{tex}_Atlas.json", "w"), indent=1)
    print("ATLAS", tex, "bark_cell", q, "bark_rect", [round(x, 5) for x in (u0, v0, u1, v1)])

if __name__ == "__main__":
    main()

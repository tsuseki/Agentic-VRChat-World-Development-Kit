"""One texture set for the whole tree (one material): bark goes into the free quadrant of the 2x2 leaf atlas.

    python tree_atlas.py <tex_dir> <Tex> [--cell 3]

Reads <Tex>_Leaves_RGBA.png (2048^2, 2x2 cells), <Tex>_Leaves_Cards.json (cells used by the leaf cards),
<Tex>_Bark_Albedo.png and <Tex>_Bark_Normal.png (tileable). Writes into <tex_dir>:
  <Tex>_Atlas_RGBA.png    2048^2: leaf cells untouched, bark in the free cell
  <Tex>_Atlas_Normal.png  1024^2: bark normal in the same cell, flat elsewhere
  <Tex>_Atlas.json        {"bark_rect": [u0, v0, u1, v1]}  (the inner, tileable bark area, UV with v up)
Bark cell layout (per side): GUTTER px of alpha 0 next to the leaf cells, then PAD px of wrapped bark, then the
bark tile. The tree shader (TreeAtlas.shader) maps tagged bark UVs into bark_rect with frac() and tex2Dgrad and
never clips bark, so the gutter only protects the leaf cards' bottom rows from bark bleeding at low mips.
--cell: which quadrant takes the bark (0 TL, 1 TR, 2 BL, 3 BR in image space; default = the one no card uses).
"""
import json, sys
import numpy as np
from PIL import Image

GUTTER, PAD = 16, 32  # px at 2048 (halved for the 1024 normal atlas)

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

def main():
    d, tex = sys.argv[1].rstrip("/\\") + "/", sys.argv[2]
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
    if leaves[row * cs:(row + 1) * cs, col * cs:(col + 1) * cs, 3].max() > 8:
        raise SystemExit(f"cell {q} is not empty in the leaf atlas")
    bark = np.array(Image.open(d + f"{tex}_Bark_Albedo.png").convert("RGB"))
    atlas = leaves.copy()
    bx, by, inner = put_bark(atlas, bark, q, size, GUTTER, PAD)
    atlas[by - PAD:by + inner + PAD, bx - PAD:bx + inner + PAD, 3] = 255  # bark + its wrap padding opaque
    Image.fromarray(atlas, "RGBA").save(d + f"{tex}_Atlas_RGBA.png")
    nsize = size // 2
    nrm = np.zeros((nsize, nsize, 3), np.uint8); nrm[...] = (128, 128, 255)
    bn = np.array(Image.open(d + f"{tex}_Bark_Normal.png").convert("RGB"))
    tmp = np.zeros((nsize, nsize, 4), np.uint8)
    put_bark(tmp, bn, q, nsize, GUTTER // 2, PAD // 2)
    c2 = nsize // 2
    blk = tmp[row * c2:(row + 1) * c2, col * c2:(col + 1) * c2, :3]
    nrm[row * c2:(row + 1) * c2, col * c2:(col + 1) * c2] = blk
    Image.fromarray(nrm, "RGB").save(d + f"{tex}_Atlas_Normal.png")
    # inner bark box -> UV (v up)
    u0, u1 = bx / size, (bx + inner) / size
    v1, v0 = 1 - by / size, 1 - (by + inner) / size
    # the normal atlas places the same box at half resolution: identical UVs by construction
    json.dump({"bark_rect": [u0, v0, u1, v1], "bark_cell": q, "leaf_cells": sorted(used)},
              open(d + f"{tex}_Atlas.json", "w"), indent=1)
    print("ATLAS", tex, "bark_cell", q, "bark_rect", [round(x, 5) for x in (u0, v0, u1, v1)])

if __name__ == "__main__":
    main()

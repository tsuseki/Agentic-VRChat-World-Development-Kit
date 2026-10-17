"""Leaf-spray atlas: up to four keyed branch photos (gpt-image on a flat key colour), one per
1024x1024 cell of a 2048x2048 atlas (2x2 grid), each with its stem base pinned to the cell's
bottom-centre so sprig cards can root that point exactly on a branch axis.

  python branch_atlas.py <out_RGBA.png> <out.json> <src_a.png> [src_b.png ...] [--key magenta|green]

Each source is keyed with process_gpt_textures.leaf(soft=True) (anti-aliased matte, despill, colour
dilation); colour is otherwise untouched. The stem end is measured as the centroid x of the opaque
pixels in the bottom STEM_ROWS rows. The fan is scaled (uniformly, no warp) and translated so that point
lands exactly on its cell's bottom-centre: u = cell centre, v = cell bottom. The other three sides keep
MARGIN px of transparency. JSON (UV, v up): {"cells": [{"rect": [u0, v0, u1, v1], "attach": [u, v]}]}
where attach is the cell's bottom-centre, i.e. the card's attach vertex.
"""
import json, os, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from process_gpt_textures import leaf

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
KEY = sys.argv[sys.argv.index("--key") + 1] if "--key" in sys.argv else "magenta"
if KEY in ARGS: ARGS.remove(KEY)
SOURCES = ARGS[2:6]
SIZE, CELL, MARGIN, STEM_ROWS = 2048, 1024, 16, 3


def stem_end(alpha):
    """(x, y) of the stem end: centroid x of opaque pixels in the bottom STEM_ROWS opaque rows."""
    ys, xs = np.nonzero(alpha >= 128)
    yb = ys.max()
    sel = ys > yb - STEM_ROWS
    return xs[sel].mean(), yb


def main(out_png, out_json):
    atlas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cells = []
    tmpdir = tempfile.mkdtemp(prefix="branch_atlas_")  # private per run: parallel runs never share files
    for i, src in enumerate(SOURCES):
        tmp = os.path.join(tmpdir, f"spray_{i}.png")
        leaf(src, tmp, KEY, soft=True)
        im = Image.open(tmp); im.load()
        x_src, _ = stem_end(np.array(im.split()[3]))
        before = x_src - im.width / 2
        im = im.crop(im.split()[3].point(lambda v: 255 if v > 0 else 0).getbbox())
        xe, _ = stem_end(np.array(im.split()[3]))
        half = max(xe, im.width - xe)
        k = min((CELL / 2 - MARGIN - 4) / half, (CELL - MARGIN - 4) / im.height)  # fit with 4 px slack so resampling never reaches the margin
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
        a = np.array(im.split()[3])
        xe, ye = stem_end(a)
        col, row = i % 2, i // 2
        cx0, cy0 = col * CELL, row * CELL
        ox = cx0 + CELL // 2 - int(round(xe))           # stem centroid -> cell centre column
        oy = cy0 + CELL - 1 - ye                         # last opaque row -> cell bottom row
        atlas.alpha_composite(im, (ox, oy))
        cells.append({"rect": [cx0 / SIZE, 1 - (cy0 + CELL) / SIZE, (cx0 + CELL) / SIZE, 1 - cy0 / SIZE],
                      "attach": [(cx0 + CELL / 2) / SIZE, 1 - (cy0 + CELL) / SIZE],
                      "stem_offset_px_before": round(float(before), 2)})
    arr = np.array(atlas).astype(np.float32)
    solid = arr[..., 3] >= 250  # colour of every non-opaque texel comes from the opaque core
    idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    arr[..., :3] = arr[..., :3][idx[0], idx[1]]
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(out_png)
    alpha = arr[..., 3]
    for i, c in enumerate(cells):
        col, row = i % 2, i // 2
        cx = alpha[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL]
        xe, ye = stem_end(cx)
        c["stem_offset_px_after"] = round(float(xe + 0.5 - CELL / 2), 2)   # pixel centre vs cell centre line
        c["stem_rows_from_bottom"] = int(CELL - 1 - ye)
        band = np.zeros(cx.shape, bool); band[:MARGIN] = True; band[:, :MARGIN] = band[:, -MARGIN:] = True
        c["border_alpha_px_top_left_right"] = int(((cx > 0) & band).sum())
        print("CELL", c)
    json.dump({"cells": cells}, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    main(ARGS[0], ARGS[1])

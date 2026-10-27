"""Leaf-spray atlas: keyed branch photos (gpt-image on a flat key colour), one per atlas cell, each with its stem
base pinned to the cell's bottom-centre so sprig cards can root that point exactly on a branch axis.

  python branch_atlas.py <out_RGBA.png> <out.json> <src_a.png> [src_b.png ...] [--key magenta|green|cyan|blue|yellow]
                         [--edge-despill] [--defringe] [--layout <layout.json>]

Default (no --layout): up to four 1024x1024 cells of a 2048x2048 atlas (2x2 grid).
--layout: cells from a layout file (image-space pixels, y down), one source per cell, e.g. the column layout with
a bark strip on the right and rectangular leaf cells:
  {"size": 2048, "bark_w": 512, "cells": [[x, y, w, h], ...]}
The bark strip (x >= size - bark_w) is left transparent here; tree_atlas.py --layout column fills it. Cards built
from rectangular cells get the cell's width/height (tree_family_build.py), so leaves are not distorted. Keep 8 px
transparent at the atlas top and bottom (cells inside [8, size - 8] in y) so the texture's vertical Repeat never
bleeds a stem into a tip. The layout is copied into the JSON ("layout").

Each source is keyed with process_gpt_textures.leaf(soft=True) (anti-aliased matte, despill, colour
dilation; --edge-despill: despill only next to the matte edge, for flowers near the key colour; --defringe:
recolour the despill residue on fine needles from clean texels, see process_gpt_textures); colour is otherwise
untouched. The stem end is measured as the centroid x of the opaque
pixels in the bottom STEM_ROWS rows. The fan is scaled (uniformly, no warp) and translated so that point
lands exactly on its cell's bottom-centre: u = cell centre, v = cell bottom. The other three sides keep
MARGIN px of transparency. JSON (UV, v up): {"cells": [{"rect": [u0, v0, u1, v1], "attach": [u, v]}]}
where attach is the cell's bottom-centre, i.e. the card's attach vertex.

Open-spray check (always on; rule: every leaf cell is a spray, never a leaf mat/patch/carpet): after the build every
cell is measured at the 0.45 cutout (alpha >= 115): opaque fraction of the cell, and the largest solid blob (connected
component after a morphological opening with a disk of radius max(3, 0.008 x cell width), which strips twigs, stalks
and thin leaf contacts, so separate leaves on twigs stay small blobs and a closed leaf mass stays one). A cell FAILS
when opaque > 0.55 or blob > 0.25; the outputs are still written (for inspection) and the run exits 1.
  python branch_atlas.py --check <Leaves_RGBA.png> [--layout <layout.json> | --cards <Leaves_Cards.json>]
measures an existing sheet the same way (exit 1 on any FAIL).
"""
import json, os, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from process_gpt_textures import leaf, EDGE_DESPILL

def _opt(k):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None

KEY = _opt("--key") or "magenta"
LAYOUT_FILE = _opt("--layout")
ARGS = [a for i, a in enumerate(sys.argv[1:], 1)
        if not a.startswith("--") and sys.argv[i - 1] not in ("--key", "--layout", "--check", "--cards")]
EDGE = EDGE_DESPILL if "--edge-despill" in sys.argv else 0
DEFRINGE = "--defringe" in sys.argv
MARGIN, STEM_ROWS = 16, 3
if LAYOUT_FILE:
    LAYOUT = json.load(open(LAYOUT_FILE))
    SIZE = LAYOUT["size"]; CELLS = [tuple(c) for c in LAYOUT["cells"]]
else:
    LAYOUT = None; SIZE = 2048; CELLS = [(c * 1024, r * 1024, 1024, 1024) for r in range(2) for c in range(2)]
SOURCES = ARGS[2:2 + len(CELLS)]
SPRAY_MAX_OPAQUE, SPRAY_MAX_BLOB = 0.55, 0.25


def spray_check(alpha, cells):
    """Open-spray rule per cell (image-space [x, y, w, h]): (opaque, blob, ok) at the 0.45 cutout."""
    out = []
    for (x, y, w, h) in cells:
        a = alpha[y:y + h, x:x + w] >= 115
        r = max(3, round(0.008 * w))
        core = ndimage.distance_transform_edt(a) > r                  # erosion by a disk of radius r
        opened = (ndimage.distance_transform_edt(~core) <= r) & a      # dilation back = opening
        lab, n = ndimage.label(opened)
        blob = float(np.bincount(lab.ravel())[1:].max()) / a.size if n else 0.0
        opq = float(a.mean())
        out.append((round(opq, 3), round(blob, 3), opq <= SPRAY_MAX_OPAQUE and blob <= SPRAY_MAX_BLOB))
    return out


def report_spray(alpha, cells):
    res = spray_check(alpha, cells)
    for i, (o, b, ok) in enumerate(res):
        print(f"SPRAYCHECK cell {i} opaque {o} blob {b} {'PASS' if ok else 'FAIL'} "
              f"(max opaque {SPRAY_MAX_OPAQUE}, blob {SPRAY_MAX_BLOB})")
    bad = [i for i, r in enumerate(res) if not r[2]]
    print(f"SPRAYCHECK {'FAIL cells ' + str(bad) if bad else 'PASS'}: every leaf cell must be an open spray (individual "
          "leaves on visible twigs, gaps, ragged outline), never a solid leaf mat / patch")
    return not bad


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
        cx0, cy0, cw, ch = CELLS[i]
        tmp = os.path.join(tmpdir, f"spray_{i}.png")
        leaf(src, tmp, KEY, soft=True, edge_despill=EDGE, defringe=DEFRINGE)
        im = Image.open(tmp); im.load()
        x_src, _ = stem_end(np.array(im.split()[3]))
        before = x_src - im.width / 2
        im = im.crop(im.split()[3].point(lambda v: 255 if v > 0 else 0).getbbox())
        xe, _ = stem_end(np.array(im.split()[3]))
        half = max(xe, im.width - xe)
        k = min((cw / 2 - MARGIN - 4) / half, (ch - MARGIN - 4) / im.height)  # fit with 4 px slack so resampling never reaches the margin
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
        a = np.array(im.split()[3])
        xe, ye = stem_end(a)
        ox = cx0 + cw // 2 - int(round(xe))           # stem centroid -> cell centre column
        oy = cy0 + ch - 1 - ye                         # last opaque row -> cell bottom row
        atlas.alpha_composite(im, (ox, oy))
        cells.append({"rect": [cx0 / SIZE, 1 - (cy0 + ch) / SIZE, (cx0 + cw) / SIZE, 1 - cy0 / SIZE],
                      "attach": [(cx0 + cw / 2) / SIZE, 1 - (cy0 + ch) / SIZE],
                      "stem_offset_px_before": round(float(before), 2)})
    arr = np.array(atlas).astype(np.float32)
    solid = arr[..., 3] >= 250  # colour of every non-opaque texel comes from the opaque core
    idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    arr[..., :3] = arr[..., :3][idx[0], idx[1]]
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(out_png)
    alpha = arr[..., 3]
    for i, c in enumerate(cells):
        cx0, cy0, cw, ch = CELLS[i]
        cx = alpha[cy0:cy0 + ch, cx0:cx0 + cw]
        xe, ye = stem_end(cx)
        c["stem_offset_px_after"] = round(float(xe + 0.5 - cw / 2), 2)   # pixel centre vs cell centre line
        c["stem_rows_from_bottom"] = int(ch - 1 - ye)
        band = np.zeros(cx.shape, bool); band[:MARGIN] = True; band[:, :MARGIN] = band[:, -MARGIN:] = True
        c["border_alpha_px_top_left_right"] = int(((cx > 0) & band).sum())
        print("CELL", c)
    out = {"cells": cells}
    if LAYOUT: out["layout"] = LAYOUT
    json.dump(out, open(out_json, "w"), indent=1)
    if not report_spray(alpha, CELLS[:len(cells)]):
        raise SystemExit("SPRAYCHECK FAILED: replace the failing cell with an open spray (outputs written for inspection)")


def check_sheet(png):
    cells = CELLS
    if _opt("--cards"):
        d = json.load(open(_opt("--cards")))
        if "layout" in d:
            cells = [tuple(c) for c in d["layout"]["cells"]]
        else:  # UV rects (v up) -> image-space px
            S = Image.open(png).height
            cells = [(round(u0 * S), round((1 - v1) * S), round((u1 - u0) * S), round((v1 - v0) * S))
                     for u0, v0, u1, v1 in (c["rect"] for c in d["cells"])]
    alpha = np.asarray(Image.open(png).convert("RGBA"))[..., 3]
    print("SPRAYCHECK sheet", png)
    if not report_spray(alpha, cells):
        raise SystemExit(1)


if __name__ == "__main__":
    if _opt("--check"):
        check_sheet(_opt("--check"))
    else:
        main(ARGS[0], ARGS[1])

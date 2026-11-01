"""Erase short bare twig stubs in composed leaf-sheet cells (the base's limb ends left past the pieces' cut points),
after compose_cells.py; column_4cells layout. Rewrites <Leaves_RGBA.png> in place:
    python trim_stubs.py <Leaves_RGBA.png> <cells, e.g. c> [--min 12] [--max 90]
Per cell: the opaque mask (alpha > 100) is skeletonised; from every skeleton end the path is walked back to the first
junction. A path of min..max px whose texels are all bark (no foliage, G > R + 4 with alpha > 128, within 6 px) is a
stub, unless another stub tip is within 40 px (a gap join); the texels nearest to it are cleared. The cell's bottom 40 rows (the trunk foot) are kept.
Prints STUBS <cell> <count> <texels cleared>.
"""
import math, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize

CELLS = {"a": (0, 8, 768, 1024), "b": (768, 8, 1536, 1024), "c": (0, 1024, 768, 2040), "d": (768, 1024, 1536, 2040)}
opt = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
path, cells = sys.argv[1], sys.argv[2]
MIN, MAX = opt("--min", 12), opt("--max", 90)
img = np.array(Image.open(path).convert("RGBA"))
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

for c in cells:
    x0, y0, x1, y1 = CELLS[c]
    px = img[y0:y1, x0:x1]
    a = px[..., 3]; r = px[..., 0].astype(int); g = px[..., 1].astype(int)
    opaque = a > 100
    folpx = (g > r + 4) & (a > 128)
    fol = ndi.binary_dilation(folpx, iterations=6)
    sk = skeletonize(ndi.gaussian_filter(opaque.astype(float), 2.0) > 0.5)  # smoothed: no bark-edge spurs
    H, W = sk.shape

    def branches(sk):
        """(path texels from each skeleton end back to the texel before its junction, ends at a junction?) per end."""
        nb = ndi.convolve(sk.astype(np.uint8), np.ones((3, 3), np.uint8), mode="constant") - sk
        out = []
        for y, x in zip(*np.nonzero(sk & (nb == 1))):
            seen, cur, junction = [(y, x)], (y, x), False
            while len(seen) <= MAX:
                nxt = [(cur[0] + dy, cur[1] + dx) for dy, dx in N8
                       if 0 <= cur[0] + dy < H and 0 <= cur[1] + dx < W and sk[cur[0] + dy, cur[1] + dx]
                       and (cur[0] + dy, cur[1] + dx) not in seen]
                if len(nxt) != 1 or nb[nxt[0]] > 2: junction = len(nxt) >= 1; break
                cur = nxt[0]; seen.append(cur)
            out.append((seen, junction))
        return out

    for _ in range(3):  # prune short skeleton spurs first (bark texture bumps)
        for seen, junction in branches(sk):
            if junction and len(seen) < MIN:
                for p in seen: sk[p] = False
    # bare: <= 15 % of the path near foliage and < 120 foliage texels around the tip (a stub's yellow-green cut end
    # passes, a twig ending in a tuft does not)
    cand = []
    for seen, junction in branches(sk):
        (y, x) = seen[0]
        tipfol = folpx[max(0, y - 15):y + 16, max(0, x - 15):x + 16].sum()
        bare = sum(bool(fol[p]) for p in seen) <= 0.15 * len(seen) and tipfol < 120
        if "--debug" in sys.argv: print("BR", c, (int(y), int(x)), len(seen), junction, bare, int(tipfol))
        if bare and junction and y < H - 40 and MIN <= len(seen) <= MAX: cand.append(seen)
    stub = np.zeros_like(sk)
    n = 0
    for seen in cand:
        (y, x) = seen[0]
        # two bare tips within 40 px face each other across a gap (a piece's cut end at the base's limb end): a join
        if any(o is not seen and math.dist(o[0], seen[0]) < 40 for o in cand): continue
        for p in seen[:-8]: stub[p] = True  # the last 8 px run inside the parent limb: keep its outline
        n += 1
    # clear every texel (fringe and the cut end's colour included) whose nearest skeleton texel is a stub texel
    dist, (iy, ix) = ndi.distance_transform_edt(~sk, return_indices=True)
    clear = (a > 0) & stub[iy, ix] & (dist < 16)
    clear[H - 40:] = False
    px[clear] = 0
    img[y0:y1, x0:x1] = px
    print("STUBS", c, n, int(clear.sum()), flush=True)

Image.fromarray(img).save(path)

"""Prune a bare-twig (winter) spray atlas on the same cards: fewer twigs, same cell rects, attach points and bark.
    python twig_prune.py <in_RGBA.png> <Leaves_Cards.json> <out_RGBA.png> [--p1 P | P0 P1 P2 P3] [--p2 A B]
           [--pbud P] [--grey G] [--seed N] [--haze AMP]
A dense bare-twig fan (0.07-0.09 opaque per cell, crown sky 0.34-0.40) reads as brown leaves at 10-25 m; a crown reads
bare at about 0.013-0.03 opaque per cell and crown sky >= 0.60 (crown_fullness.py).
Per cell (the Cards.json "layout" cells, else its UV rects), the twig mask (alpha >= 40) is skeletonised and walked from
the skeleton pixel nearest the cell's bottom-centre (the stem base) as a tree. Each branch follows the child with the
largest subtree; side children start branches one order higher:
  order 0 = the spray's stem: kept;
  order 1 = its main twig axes: an evenly spaced fraction p1 per side of the stem (error diffusion, random phase;
            random or length-weighted keeps dropped whole sides of a spray); --p1 per cell, e.g. 0.2 for a weeping
            strand cell against 0.35 for upright sprays;
  order 2 = side twigs: kept with a probability rising from p2[0] at the base of the parent axis to p2[1] at its tip
            (fine twigs survive only as a fringe at the branch ends);
  order >= 3 and spurs shorter than 14 skeleton px: dropped, except a few spurs (pbud) on the outer half.
The kept image = the original texels within each kept skeleton pixel's local radius + 1.5 px, so kept twigs are
pixel-identical and a removed twig leaves no stub. --grey G desaturates the twigs toward grey-brown (luminance kept),
ramped in from 160 px above the stem base so the card base keeps the colour of the mesh limb it grows from.
--haze AMP (default 0 = none): a far-mip twig haze. Transparent texels around the kept twigs get an alpha BELOW the
cutoff (<= AMP), shaped by the local twig density (gaussian of the twig mask, sigma 12 px) and kept off a 3-8 px ring
next to every twig; their colour fades to a light grey. Up close they are clipped (near twigs unchanged); in the far
mips they average with the twigs above the cutoff, so a fan stays a soft lacy shape instead of breaking into dots
(with Mip Maps Preserve Coverage, alpha reference 0.50 on the winter atlas). It adds perceived mass: on a bare tree use
only a trace (0.22; 0.38 read too full). Alpha-blend shaders show it as a grey glow.
Everything outside the cells (bark strip, gutters) is copied unchanged. Writes <out_RGBA.png> and <out>.json (per-cell
branch counts by order and opaque share before / after). Defaults: --p1 0.35 --p2 0 0.12 --pbud 0.1 --grey 0.5 --seed 7.
Show the result over grey next to the input before any build uses it.
"""
import argparse, json
from collections import deque
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize

CUT = 115                         # opaque = alpha >= 0.45
BUD = 14                          # a branch shorter than this (skeleton px) is a spur / bud
NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def cell_boxes(cards_json, W, H):
    d = json.load(open(cards_json))
    if "layout" in d:
        return [tuple(c) for c in d["layout"]["cells"]]
    out = []
    for c in d["cells"]:
        u0, v0, u1, v1 = c["rect"]
        x0, y0 = int(round(u0 * W)), int(round((1 - v1) * H))
        out.append((x0, y0, int(round(u1 * W)) - x0, int(round((1 - v0) * H)) - y0))
    return out


def prune_cell(A, rng, p1, p2, pbud):
    """A: cell RGBA uint8 view. Returns (keep mask over the cell, stats)."""
    a = A[..., 3]; h, w = a.shape
    m = a >= 40                                    # connectivity mask (soft edges included)
    sk = skeletonize(m)
    ys, xs = np.nonzero(sk)
    if len(ys) == 0: return np.zeros_like(m), {}
    r0 = int(np.argmin((ys - (h - 1)) ** 2 + (xs - w / 2) ** 2))   # stem base = bottom centre
    idx = -np.ones(sk.shape, np.int64); idx[ys, xs] = np.arange(len(ys))
    par = -np.ones(len(ys), np.int64); seen = np.zeros(len(ys), bool); order = []
    q = deque([r0]); seen[r0] = True
    while q:                                       # BFS tree over the 8-connected skeleton
        i = q.popleft(); order.append(i); y, x = ys[i], xs[i]
        for dy, dx in NB:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and sk[yy, xx]:
                j = idx[yy, xx]
                if not seen[j]: seen[j] = True; par[j] = i; q.append(j)
    order = np.array(order)
    sub = np.ones(len(ys), np.int64)               # subtree sizes
    for i in order[::-1]:
        if par[i] >= 0: sub[par[i]] += sub[i]
    kids = [[] for _ in range(len(ys))]
    for i in order[1:]: kids[par[i]].append(i)
    B = []                                         # B[k] = dict(order, parent, pos (0..1 along parent), px list)
    stack = [(r0, 0, -1, 0)]
    while stack:                                   # follow the heaviest child; side children start new branches
        s, o, pb, ppos = stack.pop(); k = len(B); B.append(dict(order=o, parent=pb, pos=ppos, px=[]))
        i = s
        while True:
            B[k]["px"].append(i)
            if not kids[i]: break
            c = sorted(kids[i], key=lambda j: -sub[j])
            for j in c[1:]: stack.append((j, o + 1, k, len(B[k]["px"])))
            i = c[0]
    for b in B:
        if b["parent"] >= 0: b["pos"] = b["pos"] / max(len(B[b["parent"]]["px"]), 1)
    keep = np.zeros(len(B), bool)
    ax = sorted((b["pos"], k) for k, b in enumerate(B) if b["order"] == 1 and len(b["px"]) >= BUD)
    acc = {s: rng.random() for s in (-1, 1)}; keep1 = set()
    for _, k in ax:                                # evenly spaced fraction p1 per side
        f, e = B[k]["px"][0], B[k]["px"][-1]; s = 1 if xs[e] >= xs[f] else -1
        acc[s] += p1
        if acc[s] >= 1.0: acc[s] -= 1.0; keep1.add(k)
    for k, b in enumerate(B):                      # parents come before children in B
        n = len(b["px"]); o = b["order"]
        if o == 0: keep[k] = True; continue
        if not keep[b["parent"]]: continue
        t = b["pos"]
        if n < BUD: keep[k] = o <= 2 and t > 0.5 and rng.random() < pbud
        elif o == 1: keep[k] = k in keep1
        elif o == 2: keep[k] = rng.random() < p2[0] + (p2[1] - p2[0]) * t
        else: keep[k] = False
    ks = np.zeros(sk.shape, bool); kp = np.concatenate([np.array(b["px"]) for k, b in enumerate(B) if keep[k]])
    ks[ys[kp], xs[kp]] = True
    rad = ndimage.distance_transform_edt(m)       # local half-width at each skeleton pixel
    d, (iy, ix) = ndimage.distance_transform_edt(~ks, return_indices=True)
    keepm = (d <= rad[iy, ix] + 1.5) & (a > 0)
    st = dict(branches=len(B), kept=int(keep.sum()), unreached=int((~seen).sum()),
              by_order={str(o): [int(sum(1 for k, b in enumerate(B) if b["order"] == o and keep[k])),
                                 int(sum(1 for b in B if b["order"] == o))] for o in sorted({b["order"] for b in B})})
    return keepm, st


def grey(rgb, g):
    """desaturate toward a grey-brown, luminance kept; g: amount (scalar or per-pixel [..., 1])"""
    rgb = rgb.astype(np.float32); lum = (rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    tint = np.array([1.04, 1.0, 0.98], np.float32)          # faint warm cast left (grey-brown, not grey)
    return np.clip(rgb * (1 - g) + lum * tint * g, 0, 255)


def _smooth(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def haze(img, cells, amp, sigma=12.0, t0=0.05, t1=0.18, gap=(3.0, 8.0), light=1.0, light_r=6.0,
         grey_rgb=(188, 180, 186)):
    """sub-cutoff far-mip haze around the opaque twigs, inside the cells only"""
    assert amp <= CUT / 255 - 0.06, "the haze must stay under the cutoff (0.45 - 0.05 far drop)"
    im = img.astype(np.float32).copy(); a = im[..., 3] / 255.0; op = a >= CUT / 255
    cellmask = np.zeros(a.shape, bool); edge = np.zeros(a.shape, np.float32)
    for (x, y, w, h) in cells:
        cellmask[y:y + h, x:x + w] = True
        yy, xx = np.mgrid[y:y + h, x:x + w]
        e = np.minimum.reduce([yy - y, y + h - 1 - yy, xx - x, x + w - 1 - xx]).astype(np.float32)
        edge[y:y + h, x:x + w] = np.clip((e - 4) / 12, 0, 1)        # clean cell borders
    dens = _smooth((ndimage.gaussian_filter(op.astype(np.float32), sigma) - t0) / (t1 - t0))
    d = ndimage.distance_transform_edt(~op)
    ring = _smooth((d - gap[0]) / max(gap[1] - gap[0], 1e-3))
    halo = amp * dens * ring * edge * cellmask
    a2 = np.where(op, a, np.maximum(a, halo))
    k = (np.clip((d - 2) / light_r, 0, 1) * light * cellmask)[..., None]
    G = np.array(grey_rgb, np.float32)
    im[..., :3] = np.where(op[..., None], im[..., :3], im[..., :3] * (1 - k) + G * k); im[..., 3] = a2 * 255
    out = np.clip(im + 0.5, 0, 255).astype(np.uint8)
    out[~cellmask] = img[~cellmask]
    return out



def main():
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("cards"); ap.add_argument("out")
    ap.add_argument("--p1", type=float, nargs="+", default=[0.35])
    ap.add_argument("--p2", type=float, nargs=2, default=(0.0, 0.12)); ap.add_argument("--pbud", type=float, default=0.1)
    ap.add_argument("--grey", type=float, default=0.5); ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--haze", type=float, default=0.0)
    A_ = ap.parse_args()
    src = np.asarray(Image.open(A_.src).convert("RGBA")); out = src.copy()
    cells = cell_boxes(A_.cards, src.shape[1], src.shape[0]); stats = []
    for ci, (x, y, w, h) in enumerate(cells):
        rng = np.random.default_rng(A_.seed * 100 + ci)
        p1 = A_.p1[ci] if len(A_.p1) > 1 else A_.p1[0]
        km, st = prune_cell(src[y:y + h, x:x + w], rng, p1, A_.p2, A_.pbud)
        cell = out[y:y + h, x:x + w]; cell[..., 3] = np.where(km, cell[..., 3], 0)
        if A_.grey > 0:
            ramp = np.clip((h - 1 - np.arange(h)) / 160.0, 0, 1)[:, None, None]
            g = A_.grey * ramp * ramp * (3 - 2 * ramp)
            cell[..., :3] = np.where(km[..., None], grey(cell[..., :3], g) + 0.5, cell[..., :3]).astype(np.uint8)
        st["opaque_before"] = round(float((src[y:y + h, x:x + w, 3] >= CUT).mean()), 4)
        st["opaque_after"] = round(float((cell[..., 3] >= CUT).mean()), 4); stats.append(st)
    pruned = out.copy()
    if A_.haze > 0:
        out = haze(pruned, cells, A_.haze)
    Image.fromarray(out, "RGBA").save(A_.out)
    inside = np.zeros(src.shape[:2], bool)
    for (x, y, w, h) in cells: inside[y:y + h, x:x + w] = True
    chk = dict(params=vars(A_), cells=stats, outside_cells_identical=bool((out[~inside] == src[~inside]).all()),
               alpha_only_removed_before_haze=bool((pruned[..., 3] <= src[..., 3]).all()),
               haze_keeps_opaque_mask=bool(((out[..., 3] >= CUT) == (pruned[..., 3] >= CUT)).all()))
    json.dump(chk, open(A_.out.rsplit(".", 1)[0] + ".json", "w"), indent=1)
    print("PRUNE", json.dumps(dict(opaque=[(s["opaque_before"], s["opaque_after"]) for s in stats],
                                   orders=[s["by_order"] for s in stats])))


if __name__ == "__main__":
    main()

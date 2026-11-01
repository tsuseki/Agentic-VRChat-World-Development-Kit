"""Per-cell spray metrics for a leaf atlas: opaque share, leaves on the stem network, floating leaves and visible wood.
    python spray_metrics.py atlas <Leaves_or_Atlas_RGBA.png> <Leaves_Cards.json> [--thicken stalk|all]
    python spray_metrics.py sprays <a.png> [<b.png> ...] [--layout <json>] [--key K] [--thin] [--thicken stalk|all]
`atlas`: measures the cells of a built atlas (cells from the Cards.json "layout", else its UV rects).
`sprays`: scores raw candidate sprays: each group of 4 is keyed into a temporary atlas with branch_atlas.py (or
thin_key.py with --thin, magenta only; default layout layouts/column_4cells.json), then measured. Pick the lowest
floating share and the lowest wood.
Per cell (alpha > 115 = the 0.45 cutout):
  opaque   = opaque share of the cell (SPRAYCHECK limit 0.55);
  on_stem  = share of opaque texels in the component that touches the cell's bottom rows (the stem);
  floating = share of opaque texels in pieces more than 8 px from that stem network (leaves with no visible twig);
             target <= ~0.04-0.06 per full cell;
  wood     = opaque texels in the top 80 % of the cell (the bare stem base excluded) that are not foliage-coloured
             (hue outside 55-180 deg, or saturation <= 0.2) / opaque texels there; targets: broadleaf <= 0.18 per
             cell, needle sprays <= 0.08 (shipped broadleaf atlases measured 0.07-0.16).
--thicken (optional, before measuring; apply the same step in your atlas build if you use it): `all` grows dark
non-leaf texels (twigs and stalks) 1 px each side so they survive the cutout and the first mips; `stalk` grows only
dark texels within 6 px of a leaf blade and closes 1 px twig gaps, so twigs keep their drawn width (less wood).
Prints SPRAY <cell|file> opaque X on_stem X floating X wood X.
"""
import json, os, subprocess, sys, tempfile
import numpy as np
import matplotlib.colors as mc
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = 115


def _opt(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def cell_boxes(cards_json, W, H):
    """image-space (x, y, w, h) per cell"""
    d = json.load(open(cards_json))
    if "layout" in d:
        return [tuple(c) for c in d["layout"]["cells"]]
    out = []
    for c in d["cells"]:
        u0, v0, u1, v1 = c["rect"]
        x0, y0 = int(round(u0 * W)), int(round((1 - v1) * H))
        out.append((x0, y0, int(round(u1 * W)) - x0, int(round((1 - v0) * H)) - y0))
    return out


def connected(alpha_cell):
    """(share on the stem network, share in pieces > 8 px from it)"""
    m = alpha_cell > CUT; lab, n = ndi.label(m, np.ones((3, 3)))
    r = lab[-3:][m[-3:]]
    if not len(r) or not m.any(): return 0.0, 1.0
    k = np.bincount(r).argmax(); dist = ndi.distance_transform_edt(lab != k)
    near = np.array([ndi.minimum(dist, lab, i) for i in range(1, n + 1)])
    fl = np.isin(lab, np.nonzero(near > 8)[0] + 1)
    return float((lab == k).sum() / max(m.sum(), 1)), float(fl.sum() / max(m.sum(), 1))


def wood_share(cell):
    c = cell[: int(cell.shape[0] * 0.8)]; m = c[..., 3] > CUT
    hsv = mc.rgb_to_hsv(c[..., :3] / 255.0)
    fol = (hsv[..., 0] * 360 >= 55) & (hsv[..., 0] * 360 <= 180) & (hsv[..., 1] > 0.2)
    return float((m & ~fol).sum() / max(m.sum(), 1))


def thicken(C, stalk_only=False):
    """one cell (RGBA uint8) -> copy with thin dark twigs / stalks grown 1 px each side"""
    hsv = mc.rgb_to_hsv(C[..., :3] / 255.0)
    leafy = (hsv[..., 1] > 0.25) & (hsv[..., 0] > 0.12) & (hsv[..., 0] < 0.5)
    sel = (C[..., 3] > 60) & ~leafy & (hsv[..., 2] < 0.5)
    sel0 = (C[..., 3] > 20) & ~leafy & (hsv[..., 2] < 0.5)
    if stalk_only:
        yy, xx = np.mgrid[-3:4, -3:4]
        blade = ndi.binary_opening(leafy & (C[..., 3] > 128), structure=(xx * xx + yy * yy) <= 9)
        sel &= ndi.binary_dilation(blade, iterations=6)
    up = ndi.grey_dilation(np.where(sel, C[..., 3], 0).astype(np.uint8), size=(3, 3))
    if stalk_only:
        up = np.maximum(up, ndi.grey_closing(np.where(sel0, C[..., 3], 0).astype(np.uint8), size=(3, 3)))
    D = C.copy(); D[..., 3] = np.maximum(C[..., 3], up)
    return D


def measure(A, boxes, names):
    th = _opt("--thicken")
    for nm, (x, y, w, h) in zip(names, boxes):
        C = A[y:y + h, x:x + w]
        if th: C = thicken(C, th == "stalk")
        on, fl = connected(C[..., 3])
        print(f"SPRAY {nm} opaque {float((C[..., 3] > CUT).mean()):.3f} on_stem {on:.3f} floating {fl:.3f} "
              f"wood {wood_share(C):.3f}", flush=True)


def main():
    mode = sys.argv[1]
    if mode == "atlas":
        A = np.asarray(Image.open(sys.argv[2]).convert("RGBA"))
        boxes = cell_boxes(sys.argv[3], A.shape[1], A.shape[0])
        measure(A, boxes, ["cell %s" % "abcdefgh"[i] for i in range(len(boxes))])
        return
    skip = {"--layout", "--key", "--thicken"}
    srcs = [a for i, a in enumerate(sys.argv[2:], 2) if not a.startswith("--") and sys.argv[i - 1] not in skip]
    layout = _opt("--layout", os.path.join(HERE, "layouts", "column_4cells.json"))
    key = _opt("--key", "magenta"); thin = "--thin" in sys.argv
    tool = os.path.join(HERE, "thin_key.py" if thin else "branch_atlas.py")
    n = len(json.load(open(layout))["cells"])
    for i in range(0, len(srcs), n):
        grp = srcs[i:i + n]; full = grp + [grp[0]] * (n - len(grp))
        d = tempfile.mkdtemp(prefix="spray_metrics_")
        # SPRAYCHECK may fail on a dense candidate; its outputs are still written, so measure anyway
        subprocess.run([sys.executable, tool, f"{d}/t.png", f"{d}/t.json", *full, "--key", key, "--layout", layout],
                       capture_output=True)
        if not os.path.exists(f"{d}/t.json"):
            raise SystemExit(f"keying failed for {grp}")
        A = np.asarray(Image.open(f"{d}/t.png").convert("RGBA"))
        boxes = cell_boxes(f"{d}/t.json", A.shape[1], A.shape[0])[:len(grp)]
        measure(A, boxes, [os.path.basename(s) for s in grp])


if __name__ == "__main__":
    main()

"""Key-spill check for an RGBA leaf atlas, at every box-filtered mip level.

  python check_key_spill.py <atlas.png>

Per mip (straight-alpha box filter, as Unity's default mip generation): over pixels with alpha > 0.01,
the max of (R+B)/2 - G on edge pixels (0.01 < alpha < 0.99) and the count of pixels whose hue is in
280-340 deg (magenta) with saturation > 0.25 and value > 0.15 (near-black twig shadows have a noisy,
invisible hue and are not key spill).
"""
import sys
import numpy as np
from PIL import Image


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1); d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-9), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(d == 0, 0, np.where(mx == r, ((g - b) / np.maximum(d, 1e-9)) % 6,
                 np.where(mx == g, (b - r) / np.maximum(d, 1e-9) + 2, (r - g) / np.maximum(d, 1e-9) + 4))) * 60
    return h, s


def main(path):
    a = np.array(Image.open(path).convert("RGBA")).astype(np.float64) / 255
    lvl = 0
    while True:
        rgb, al = a[..., :3], a[..., 3]
        vis = al > 0.01
        edge = vis & (al < 0.99)
        spill = ((rgb[..., 0] + rgb[..., 2]) / 2 - rgb[..., 1])
        h, s = hsv(rgb)
        mag = vis & (h >= 280) & (h <= 340) & (s > 0.25) & (rgb.max(-1) > 0.15)
        print(f"MIP {lvl} {a.shape[1]}x{a.shape[0]} edge_px={int(edge.sum())} "
              f"max_spill_edge={spill[edge].max() * 255 if edge.any() else 0:.1f} magenta_px={int(mag.sum())}")
        if min(a.shape[:2]) <= 1:
            break
        a = a[: a.shape[0] // 2 * 2, : a.shape[1] // 2 * 2]
        a = a.reshape(a.shape[0] // 2, 2, a.shape[1] // 2, 2, 4).mean((1, 3))
        lvl += 1


if __name__ == "__main__":
    main(sys.argv[1])

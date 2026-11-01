"""Magenta keyer that keeps thin leaf stalks: branch_atlas.py placement with this keyer in place of
process_gpt_textures.leaf(). Use it for long-stalked leaves (birch, maple, aspen).
    python thin_key.py <out_RGBA.png> <out_Cards.json> <a.png> <b.png> [<c.png> <d.png>] [--layout <json>]
Same arguments and outputs as branch_atlas.py (SPRAYCHECK included); magenta key only.
Why: leaf()'s opening + 1 px erosion deletes the 1-3 px leaf stalks, so after the fit into a ~1000 px cell 25-60 % of
the opaque texels were leaves floating > 8 px from any twig (spray_metrics.py; short-stalked oak sprays: 0 %).
Keyer, at source resolution: keyness = min(R, B) - G; threshold = 0.45 x the border median (as leaf()); soft ramp, NO
opening and NO erosion; solid (alpha > 0.5) components under 60 px dropped, the ramp kept only within 2 px of solid
texels; despill: R and B lowered by max(0, min(R, B) - G); every texel that is not solid takes the colour of the nearest
solid texel (no magenta at any mip). Afterwards every texel with min(R, B) > G + 8 is recoloured from the nearest clean
texel (Lanczos ringing from the cell fit). Run check_key_spill.py on the result as usual.
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import branch_atlas as BA  # noqa: E402


def thin_key(src, dst, key, soft=True, edge_despill=0, defringe=False):
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    keyness = np.minimum(r, b) - g
    border = np.concatenate([keyness[:8].ravel(), keyness[-8:].ravel(), keyness[:, :8].ravel(), keyness[:, -8:].ravel()])
    thr = np.median(border) * 0.45
    a = np.clip((thr * 1.2 - keyness) / (thr * 0.9), 0.0, 1.0)
    solid = a > 0.5
    lab, n = ndimage.label(solid, structure=np.ones((3, 3)))
    if n:
        sizes = ndimage.sum(solid, lab, range(1, n + 1))
        solid = np.isin(lab, np.nonzero(sizes >= 60)[0] + 1)
    a = np.where(ndimage.binary_dilation(solid, iterations=2), a, 0.0)
    core = solid & (a >= 0.98)
    sp = np.maximum(np.minimum(r, b) - g, 0)
    im[..., 0] -= sp; im[..., 2] -= sp
    idx = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    rgb = im[idx[0], idx[1]]
    out = np.dstack([rgb, a * 255]).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(dst)
    print("KEY", os.path.basename(src), "coverage", round(float((a > 0.45).mean()), 3), "thr", round(float(thr), 1), flush=True)


if __name__ == "__main__":
    if BA.KEY != "magenta":
        raise SystemExit("thin_key.py keys magenta only")
    BA.leaf = thin_key
    BA.main(BA.ARGS[0], BA.ARGS[1])
    arr = np.asarray(Image.open(BA.ARGS[0])).copy()
    r, g, b = (arr[..., i].astype(np.int16) for i in range(3))
    bad = (arr[..., 3] > 0) & (np.minimum(r, b) > g + 8)
    if bad.any():
        idx = ndimage.distance_transform_edt(bad | (arr[..., 3] == 0), return_distances=False, return_indices=True)
        arr[..., :3][bad] = arr[..., :3][idx[0][bad], idx[1][bad]]
    Image.fromarray(arr, "RGBA").save(BA.ARGS[0]); print("KEY magenta-ringing texels recoloured", int(bad.sum()))

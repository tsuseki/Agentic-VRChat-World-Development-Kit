"""Finish a billboard sheet rendered by tree_booth_pack.py: every texel below the cutoff takes the colour of the
nearest opaque texel (no dark/black fringe in the mips), alpha kept as rendered.
    python tree_billboard_fix.py <Species>_Billboard_raw.png <Species>_Billboard.png
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
a = np.array(Image.open(src).convert("RGBA")).astype(np.float32)
alpha = a[..., 3]
core = alpha >= 0.6 * 255
if not core.any(): raise SystemExit("billboard is empty")
_, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
rgb = a[..., :3].copy()
# rendered colour is premultiplied-looking at soft edges: replace every non-core texel by its nearest core colour
rgb[~core] = a[..., :3][iy[~core], ix[~core]]
out = np.dstack([rgb, alpha]).clip(0, 255).astype(np.uint8)
Image.fromarray(out, "RGBA").save(dst)
os.remove(src) if os.path.abspath(src) != os.path.abspath(dst) else None
print("BILLBOARD", dst, "opaque_px", int(core.sum()))

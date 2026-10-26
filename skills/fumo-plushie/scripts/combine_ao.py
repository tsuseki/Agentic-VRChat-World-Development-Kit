"""Multiply a baked AO map lightly into a cleaned 2K BaseColor and write the shipped sizes.
Usage: python combine_ao.py <clean_2k.png> <ao.npy> <uvpos.npz> <strength=0.35> <out_prefix> [sizes=1024,512]
AO is padded like the colour (nearest island texel), so no black ever leaks across island borders. Writes <prefix>_<size>.png and <prefix>_ao_preview.png"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, aon, npz, strength, pre = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
sizes = [int(s) for s in (sys.argv[6] if len(sys.argv) > 6 else "1024,512").split(",")]
t = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
ao = np.load(aon).astype(np.float32); tri = np.load(npz)["tri"]
core = ndi.binary_erosion(tri >= 0, iterations=1)
dist, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
ao = ao[iy, ix]; ao = np.clip(ao, 0, 1)
mul = 1 - strength * (1 - ao)
res = np.clip(t * mul[..., None], 0, 255).astype(np.uint8)
Image.fromarray((ao * 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS).save(pre + "_ao_preview.png")
for s in sizes:
    im = Image.fromarray(res)
    (im.resize((s, s), Image.LANCZOS) if s != im.width else im).save(f"{pre}_{s}.png", optimize=True)
print("COMBINE_OK", pre, sizes, "AO mean (island)", round(float(ao[core].mean()), 3), "min", round(float(ao[core].min()), 3), "mul mean", round(float(mul[core].mean()), 3))

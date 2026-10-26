"""Optional: use only when review shows scuffed clothing. Cleans the flat-colour clothing regions of a Tripo plush texture, in UV space, then pad the UV islands.
Usage: python clean_flat_regions.py <src_2k.png> <uvpos.npz> <out_2k.png> [--white-sat 0.35] [--debug dir]
 1. black clothing (L < 75): snapped to one flat near-black (soft ramp, so anti-aliased edges and the eye outlines survive)
 2. (legwear only, z < --sock-z=0.055 m via the UV->3D map) thin grey/white hairlines in black areas (seam highlights, 1-3 px) removed; wide white bands (sock stripes) re-thresholded crisp with a 0.7 px blur
 3. white clothing (L > 205, low chroma): median-denoised and chroma reduced (Tripo tints white lilac)
 4. island padding: texels outside every UV0 island take the colour of the nearest island texel (24 px) instead of the tan background,
    so mip-mapping/bilinear never pulls tan into black or white clothes at island edges.
Face (skin, eyes, blush), hair and everything coloured are untouched."""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import cv2
a = sys.argv[1:]; src, npz, out = a[0], a[1], a[2]
WS = float(a[a.index("--white-sat") + 1]) if "--white-sat" in a else 0.35
d = np.load(npz); inm = d["tri"] >= 0
ZMAX = float(a[a.index("--sock-z") + 1]) if "--sock-z" in a else 0.055
BODYZ = float(a[a.index("--body-z") + 1]) if "--body-z" in a else 0.15
bodyzone = inm & (d["pos"][..., 2] < BODYZ)   # below the chin: face, eyes, ears and hair are never touched
sockzone = inm & (d["pos"][..., 2] < ZMAX)     # stripes/hairline handling only on the legwear
t = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
L = t @ np.array([0.299, 0.587, 0.114], np.float32); sat = t.max(2) - t.min(2)
MX = t.max(2)      # darkness is judged by the brightest channel, so dark red (eyes) is never flattened
def smooth(x, e0, e1): y = np.clip((x - e0) / (e1 - e0), 0, 1); return y * y * (3 - 2 * y)
res = t.copy()
black = bodyzone & (MX < 75)
# island interior only (1 px erosion), so the padding is applied from clean texels
core = ndi.binary_erosion(inm, iterations=1)
# --- 2: stripes / hairlines. bright grey-white pixels near black
near_black = ndi.binary_dilation(black & (MX < 45), iterations=7)
grey = sat < 0.15 * np.maximum(t.max(2), 1)          # chroma ratio: skin ~0.32, white/grey < 0.1
bright = sockzone & near_black & (L > 105) & grey
wide = ndi.binary_opening(bright, structure=np.ones((3, 3)))            # >= 3 px wide: real stripes
wide = ndi.binary_dilation(wide, iterations=1) & bright
lab, n = ndi.label(wide); sizes = ndi.sum(wide, lab, range(1, n + 1))
keep = np.isin(lab, 1 + np.where(sizes >= 40)[0])                          # tiny specks are not stripes
stripe_w = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.7)
hair = bright & ~ndi.binary_dilation(keep, iterations=2)                   # thin lines/noise next to black
# --- 1: flat black
wb = smooth(-MX, -75, -45) * (bodyzone & ~ndi.binary_dilation(keep, iterations=1) & ~(ndi.binary_dilation(sockzone & (L > 105) & grey, iterations=2)))   # 1 where L<45
flat_black = np.array([16, 16, 18], np.float32)
res = res * (1 - wb[..., None]) + flat_black * wb[..., None]
hl = hair & (L < 170)
res[hl] = flat_black
# crisp stripes
stripe_col = np.array([236, 236, 242], np.float32)
sw = stripe_w * sockzone
res = res * (1 - sw[..., None]) + stripe_col * sw[..., None]
# --- 2b: legwear repaint in 3D (Tripo projects the sock stripes as zig-zags and leaves skin slivers on the sock): every texel whose 3D position lies on the
# sock (--sock-y: y < SOCK_Y, z < --sock-z, x in --sock-x) is repainted flat black with straight stripes at constant y (--stripes y0:y1,y0:y1)
if "--sock-y" in a:
    SY = float(a[a.index("--sock-y") + 1]); SOCKTOP = float(a[a.index("--sock-top") + 1]) if "--sock-top" in a else ZMAX; xr = [[float(v) for v in r.split(":")] for r in a[a.index("--sock-x") + 1].split(",")]
    bands = [[float(v) for v in b.split(":")] for b in a[a.index("--stripes") + 1].split(",")] if "--stripes" in a else []
    P = d["pos"]; sock = inm & (P[..., 2] < SOCKTOP) & (P[..., 1] < SY) & np.any([(P[..., 0] > x0) & (P[..., 0] < x1) for x0, x1 in xr], axis=0)
    yy = P[..., 1]; sw2 = np.zeros(yy.shape, np.float32)
    for lo, hi in bands: sw2 = np.maximum(sw2, smooth(yy, lo - 0.0004, lo + 0.0004) * (1 - smooth(yy, hi - 0.0004, hi + 0.0004)))
    sw2 *= sock
    if bands:
        res[sock] = flat_black; res = res * (1 - sw2[..., None]) + stripe_col * sw2[..., None]
    else:      # no procedural stripes: only repaint skin/tan slivers on the sock black (stripes keep their painted layout)
        skin = sock & (res[..., 0] > 150) & ((res.max(2) - res.min(2)) > 0.18 * res.max(2))
        skin = ndi.binary_dilation(skin, iterations=2) & sock & (L < 235)
        res[skin] = flat_black
    print("sock texels", int(sock.sum()))
# --- 3: white clothing
white = bodyzone & (L > 205) & (sat < 60)
white = ndi.binary_opening(white, structure=np.ones((5, 5)))
ww = cv2.GaussianBlur(white.astype(np.float32), (0, 0), 1.5) * bodyzone
med = cv2.medianBlur(np.clip(res, 0, 255).astype(np.uint8), 7).astype(np.float32)
g = med.mean(2, keepdims=True); med = g + (med - g) * WS
res = res * (1 - ww[..., None]) + med * ww[..., None]
res = np.clip(res, 0, 255)
# --- 4: padding
dist, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
pad = (~core) & (dist <= 24)
res[pad] = res[iy[pad], ix[pad]]
Image.fromarray(res.astype(np.uint8)).save(out)
print("CLEAN_OK", out, "black", int(black.sum()), "stripe px", int(keep.sum()), "hairline px", int(hl.sum()), "white px", int(white.sum()), "padded", int(pad.sum()))

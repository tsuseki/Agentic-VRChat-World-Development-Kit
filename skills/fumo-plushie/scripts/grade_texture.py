"""Selective colour match of a Tripo (Remove Lighting) texture to the approved concept front.
Tripo's texture comes out more saturated and warmer than the concept (pale blond arrived orange, dark brown arrived red-purple). This script measures the median colour of
a colour class in the TEXTURE and moves it to a target median measured on the CONCEPT image, with a soft mask so everything outside the class is untouched
(black clothes, whites, eyes, accents).

Usage:
  python grade_texture.py measure <texture.png> <class>            # print median colour of the class mask
  python grade_texture.py grade <in.png> <out.png> <class>=<R,G,B>[@strength] [...]     (strength 0-1 = fraction of the full correction in log space; 1 default)
Classes are HSV windows (hue 0-360, sat/val 0-1) defined in CLASSES below; add one per character, e.g. 'hair_blond'. Target = median RGB (0-255) of the same area on the concept.
Measure concept medians with `measure` on a crop of the concept, with the same class window.
Per-channel gains are clamped to 0.5..1.8 and applied with the class mask, so the grade can never invent colour.
"""
import sys, colorsys
import numpy as np
from PIL import Image
CLASSES = {   # name: (hue_lo, hue_hi, sat_lo, sat_hi, val_lo, val_hi)
    "hair_blond": (25, 55, 0.20, 0.75, 0.55, 1.0),            # concept-side window (soft blond, sat ~0.37)
    "hair_blond_tex": (28, 50, 0.50, 0.85, 0.60, 1.0),         # Tripo-side window (oversaturated orange, sat ~0.63): excludes skin (sat ~0.33)
    "hair_ash": (20, 50, 0.10, 0.45, 0.55, 1.0),
    "hair_brown": (340, 40, 0.10, 0.90, 0.03, 0.55),           # wide on purpose: unmasked dark patches would show as blotches next to the graded hair
    "skin": (10, 35, 0.08, 0.40, 0.75, 1.0),
    "red": (345, 15, 0.60, 1.0, 0.30, 1.0),
    "blue": (200, 250, 0.45, 1.0, 0.35, 1.0),
}
def hsv(a):
    mx = a.max(2); mn = a.min(2); d = np.maximum(mx - mn, 1e-6)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, (mx - mn) / np.maximum(mx, 1e-6), mx
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def mask(a, cls):
    h, s, v = hsv(a); h0, h1, s0, s1, v0, v1 = CLASSES[cls]
    hm = ((h >= h0) & (h <= h1)) if h0 <= h1 else ((h >= h0) | (h <= h1))
    soft = ss(s, s0 - 0.04, s0 + 0.04) * (1 - ss(s, s1 - 0.04, s1 + 0.04)) * ss(v, v0 - 0.04, v0 + 0.04) * (1 - ss(v, v1 - 0.04, v1 + 0.001))
    return hm.astype(np.float32) * soft
def load(p): return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255
if sys.argv[1] == "measure":
    a = load(sys.argv[2]); m = mask(a, sys.argv[3]) > 0.5
    print(sys.argv[3], "texels", int(m.sum()), "median RGB", (np.median(a[m], 0) * 255).round().astype(int).tolist() if m.any() else None)
else:
    a = load(sys.argv[2]); out = a.copy()
    for spec in sys.argv[4:]:
        cls, tgt = spec.split("="); st = float(tgt.split("@")[1]) if "@" in tgt else 1.0; tgt = tgt.split("@")[0]; tgt = np.array([float(v) for v in tgt.split(",")]) / 255
        m = mask(a, cls); sel = m > 0.5
        if not sel.any(): print("class", cls, "has no texels; skipped"); continue
        med = np.median(a[sel], 0); gain = np.clip(tgt / np.maximum(med, 1e-4), 0.5, 1.8) ** st
        out = out * (1 - m[..., None]) + np.clip(out * gain[None, None, :], 0, 1) * m[..., None]
        print(cls, "median", (med * 255).round().astype(int).tolist(), "-> target", (tgt * 255).round().astype(int).tolist(), "gain", gain.round(3).tolist(), "texels", int(sel.sum()))
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(sys.argv[3]); print("graded", sys.argv[3])

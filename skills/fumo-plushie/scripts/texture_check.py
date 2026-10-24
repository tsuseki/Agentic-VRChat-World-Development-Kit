"""Headless Blender: compare a written plush texture with its source (catches the AgX desaturation bug,
wrong colour space, a bake that missed the source).
Median RGB (0-255) and mean chroma over content pixels (alpha > 0.5, not black padding) of both images.
Usage: python .omp/scripts/tool.py blender --script texture_check.py -- <written.png> <source.png> [tol=10]
Prints TEXCHECK PASS|FAIL written=(r,g,b) source=(r,g,b) delta=(..) chroma=<written/source>.
PASS: every median channel within tol and chroma ratio >= 0.9 (AgX gave (238,198,156) -> (191,171,152), ratio ~0.5).
"""
import bpy, sys, os
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
written, source = os.path.abspath(argv[0]), os.path.abspath(argv[1])
tol = float(argv[2]) if len(argv) > 2 else 10.0
bpy.ops.wm.read_factory_settings(use_empty=True)


def stats(path):
    img = bpy.data.images.load(path)
    # byte PNGs: Image.pixels holds the stored values / 255 (no colour management), so both sides compare 1:1
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); px = px.reshape(-1, 4)
    rgb = px[:, :3]
    keep = (px[:, 3] > 0.5) & (rgb.max(1) > 0.02)
    rgb = rgb[keep] if keep.any() else rgb
    return np.median(rgb, 0) * 255, float((rgb.max(1) - rgb.min(1)).mean()), (w, h), float(keep.mean())


mw, cw, sw, fw = stats(written)
ms, cs, ss, fs = stats(source)
delta = mw - ms
ratio = cw / cs if cs > 1e-6 else 1.0
ok = bool(np.all(np.abs(delta) <= tol) and ratio >= 0.9)
fmt = lambda v: "(" + ",".join(f"{x:.0f}" for x in v) + ")"
print(f"TEXCHECK {'PASS' if ok else 'FAIL'} written={fmt(mw)} {sw[0]}x{sw[1]} source={fmt(ms)} {ss[0]}x{ss[1]} "
      f"delta={fmt(delta)} chroma={ratio:.2f} content={fw:.2f}/{fs:.2f}")

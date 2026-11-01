"""Conifer fresh shoot tips: lighter, fresher green on the outer ends of the shoots, so the crown is not one flat dark
tone; --young also brightens and yellows the whole crown for a young variant's own atlas (CFG tex=<Variant>).
    python fresh_tips.py <tex dir> <in Tex> <out Tex> [--young]
Per cell: geodesic distance over the alpha mask from the cell's attach point (Leaves_Cards.json); the needle texels in
the outermost TIP share of each cell's distance range blend toward a fresh green (smoothstep). Alpha unchanged. Writes
<out Tex>_Atlas_RGBA.png, _Atlas.json, _Leaves_RGBA.png, _Leaves_Cards.json, _Bark_* (copies) into <tex dir>."""
import json, shutil, sys
import numpy as np, matplotlib.colors as mc
from PIL import Image
from skimage.graph import MCP_Geometric

D, TIN, TOUT = sys.argv[1], sys.argv[2], sys.argv[3]; YOUNG = "--young" in sys.argv
TIP = 0.30; FRESH = (95 / 360, 0.55, 0.62)


def recolour(A, cells):
    A = A.copy(); H, W = A.shape[:2]; hsv = mc.rgb_to_hsv(A[..., :3] / 255.0)
    leafy = (hsv[..., 0] * 360 > 55) & (hsv[..., 0] * 360 < 180) & (hsv[..., 1] > 0.15) & (A[..., 3] > 0)
    for c in cells:
        u0, v0, u1, v1 = c["rect"]; x0, x1 = int(u0 * W), int(u1 * W); y0, y1 = int((1 - v1) * H), int((1 - v0) * H)
        m = A[y0:y1, x0:x1, 3] > 40
        if not m.any(): continue
        ax = int(c["attach"][0] * W) - x0; ay = min(y1 - y0 - 1, int((1 - c["attach"][1]) * H) - y0)
        ys, xs = np.nonzero(m); k = np.argmin((ys - ay) ** 2 + (xs - ax) ** 2)
        cost = np.where(m, 1.0, 50.0); dist, _ = MCP_Geometric(cost).find_costs([(ys[k], xs[k])])
        dd = np.where(m, dist, 0); top = np.percentile(dd[m], 99)
        t = np.clip((dd / max(top, 1) - (1 - TIP)) / TIP, 0, 1); t = t * t * (3 - 2 * t) * 0.75
        sub = hsv[y0:y1, x0:x1]; lf = leafy[y0:y1, x0:x1]
        for i in range(3): sub[..., i] = np.where(lf, sub[..., i] * (1 - t) + FRESH[i] * t * (sub[..., 2] / max(np.median(sub[..., 2][lf]), 1e-3) if i == 2 else 1), sub[..., i])
    if YOUNG:  # young tree: brighter, yellower fresh green over the whole crown
        hsv[..., 0] = np.where(leafy, hsv[..., 0] * 0.85 + (90 / 360) * 0.15, hsv[..., 0])
        hsv[..., 1] = np.where(leafy, np.clip(hsv[..., 1] * 1.05, 0, 1), hsv[..., 1])
        hsv[..., 2] = np.where(leafy, np.clip(hsv[..., 2] * 1.45 + 0.04, 0, 1), hsv[..., 2])
    rgb = mc.hsv_to_rgb(np.clip(hsv, 0, 1)) * 255
    A[..., :3] = np.where(leafy[..., None], rgb.round(), A[..., :3]).astype(np.uint8)
    return A


cj = json.load(open(f"{D}/{TIN}_Leaves_Cards.json"))
for nm in ("Atlas_RGBA", "Leaves_RGBA"):
    A = np.asarray(Image.open(f"{D}/{TIN}_{nm}.png").convert("RGBA"))
    Image.fromarray(recolour(A, cj["cells"])).save(f"{D}/{TOUT}_{nm}.png")
if TOUT != TIN:
    for nm in ("Atlas.json", "Leaves_Cards.json", "Bark_Albedo.png", "Bark_Normal.png"):
        shutil.copy(f"{D}/{TIN}_{nm}", f"{D}/{TOUT}_{nm}")
print("TIPS", TOUT, "young" if YOUNG else "")

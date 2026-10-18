"""Turns GPT Image 2.5 Sunburst outputs into game textures.

Leaf atlases: chroma-key the flat background to a hard 1-bit alpha, despill the key colour from the
leaf edges, erode one pixel to drop the fringe, then flood the leaf colour into the transparent area
(nearest-pixel dilation) so mipmaps never pull in background colour -> no halos.
Keys: magenta, green (foliage), cyan, blue, yellow (flowers whose colour is near magenta/green; see SKILL.md).
edge_despill=N: despill only the opaque pixels within N px of the matte edge (default 0 = every pixel). The
whole-image despill also strips the key's channels from plant colours that lean towards the key (pink/purple
petals on magenta, green leaves on green); spill only sits at the edge.
defringe=True (--defringe): fine needles/hairs blend the key into opaque texels and the despill leaves a residue of
one key channel (magenta -> pink or purple-blue tips). Every texel whose key channel still exceeds the other
channels by DEFRINGE_THR (while its other key channel is not below them: brown twigs stay clean), plus bright pink
tips on magenta, takes the colour of the nearest clean opaque texel; alpha is unchanged. Off = identical output.
Bark: make tileable (half-offset + edge-weighted blend), resize to 1024, derive a tangent-space
OpenGL normal map from the blurred luminance.

  python process_gpt_textures.py leaf <src.png> <dst_RGBA.png> <magenta|green|cyan|blue|yellow> [triple] [--edge-despill] [--defringe]
  python process_gpt_textures.py bark <src.png> <dst_albedo.png> <dst_normal.png> <strength>
"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# key -> (keyness: high on the key colour, <= 0 on the plant; channels the despill subtracts the excess from)
KEYS = {
    "magenta": (lambda r, g, b: np.minimum(r, b) - g, (0, 2)),
    "green": (lambda r, g, b: g - np.maximum(r, b), (1,)),
    "cyan": (lambda r, g, b: np.minimum(g, b) - r, (1, 2)),
    "blue": (lambda r, g, b: b - np.maximum(r, g), (2,)),
    "yellow": (lambda r, g, b: np.minimum(r, g) - b, (0, 1)),
}
EDGE_DESPILL = 4  # px band for --edge-despill
DEFRINGE_THR = 12.0  # key-channel excess (0-255) left by the despill that counts as fringe (--defringe)


def fringe(im, chans):
    """Texels still carrying a despill residue of the key: some key channel exceeds the max of the other channels by
    DEFRINGE_THR while no key channel is clearly below them (magenta key: pink R>G with B~G). On magenta also any
    purple-blue tint (B-G > DEFRINGE_THR: the despill never touches texels whose R is below G) and bright pink needle
    tips (R-G > 50, B-G > -25, R > 170)."""
    rest = [c for c in range(3) if c not in chans]
    m = im[..., rest].max(-1)
    ex = np.stack([im[..., c] - m for c in chans], -1)
    dirty = (ex.max(-1) > DEFRINGE_THR) & (ex.min(-1) > -4)
    if tuple(chans) == (0, 2):
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        dirty |= (b - g > DEFRINGE_THR) | ((r - g > 50) & (b - g > -25) & (r > 170))
    return dirty


def leaf(src, dst, key, triple=False, soft=False, edge_despill=0, defringe=False):
    im = np.array(Image.open(src).convert("RGB")).astype(np.float32)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    kf, chans = KEYS[key]
    keyness = kf(r, g, b)
    # threshold from the border (pure background) statistics
    border = np.concatenate([keyness[:8].ravel(), keyness[-8:].ravel(), keyness[:, :8].ravel(), keyness[:, -8:].ravel()])
    thr = np.median(border) * 0.45
    alpha = keyness < thr
    # soft matte: linear ramp across the key band instead of a hard threshold (smooth leaf edges)
    soft_a = np.clip((thr * 1.2 - keyness) / (thr * 0.9), 0.0, 1.0) if soft else None
    alpha = ndimage.binary_opening(alpha, iterations=1)
    lab, n = ndimage.label(alpha)  # drop specks
    if n:
        sizes = ndimage.sum(alpha, lab, range(1, n + 1))
        alpha = np.isin(lab, np.nonzero(sizes >= 60)[0] + 1)
    alpha = ndimage.binary_erosion(alpha, iterations=1)
    # despill (whole image, or only the opaque band inside the matte edge)
    ex = np.clip(keyness, 0, None)
    if edge_despill:
        ex = ex * (alpha & ndimage.binary_dilation(~alpha, iterations=edge_despill))
    for c in chans:
        im[..., c] -= ex
    im = np.clip(im, 0, 255)
    src_ok = alpha & ~fringe(im, chans) if defringe else alpha  # colour sources: opaque, and clean with --defringe
    idx = ndimage.distance_transform_edt(~src_ok, return_distances=False, return_indices=True)
    rgb = im[idx[0], idx[1]]
    if soft:  # keep the ramp only next to solid leaf (drops stray key noise)
        near = ndimage.binary_dilation(alpha, iterations=3)
        a8 = np.where(near, soft_a * 255, 0)
        a8 = np.where(alpha, np.maximum(a8, 128), a8)
        # colour is decoupled from alpha: every pixel that is not fully opaque (edge ramp and the
        # transparent area) takes the colour of the nearest opaque interior pixel, so neither the
        # AA edge nor any mip can show key colour
        core = a8 >= 250
        if defringe: core &= src_ok
        idx = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
        rgb = im[idx[0], idx[1]]
    else:
        a8 = np.where(alpha, 255, 0)
    out = np.dstack([rgb, a8]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    if triple:  # narrow plume (cypress): three copies side by side so the square card is filled
        plume = img.crop(img.split()[3].getbbox())
        W, H = img.size; canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for sc, cx in ((0.82, 0.25), (0.82, 0.75), (1.0, 0.5)):
            p2 = plume.resize((int(plume.width * sc * H / plume.height), int(H * sc)), Image.LANCZOS)
            canvas.alpha_composite(p2, (int(W * cx - p2.width / 2), H - p2.height))
        a2 = np.array(canvas.split()[3]) >= 128
        arr = np.array(canvas).astype(np.float32)
        idx = ndimage.distance_transform_edt(~a2, return_distances=False, return_indices=True)
        img = Image.fromarray(np.dstack([arr[..., :3][idx[0], idx[1]], np.where(a2, 255, 0)]).astype(np.uint8), "RGBA")
    if img.width != 2048:
        # upscale to 2048 wide keeping the aspect (portrait sprays for 3:4 cells); colour smooth, alpha re-thresholded to stay hard
        size = (2048, round(2048 * img.height / img.width))
        c = img.convert("RGB").resize(size, Image.LANCZOS)
        a = img.split()[3].resize(size, Image.BICUBIC if soft else Image.BILINEAR)
        if not soft:
            a = a.point(lambda v: 255 if v >= 128 else 0)
        c.putalpha(a); img = c
    img.save(dst)
    print("LEAF", dst, "coverage", round(float(np.array(img.split()[3]).mean() / 255), 3), "thr", round(float(thr), 1))


def tileable(a):
    h, w = a.shape[:2]
    sh = np.roll(np.roll(a, h // 2, 0), w // 2, 1)
    y = np.minimum(np.arange(h), h - 1 - np.arange(h))[:, None] / (h * 0.25)
    x = np.minimum(np.arange(w), w - 1 - np.arange(w))[None, :] / (w * 0.25)
    wgt = np.clip(np.minimum(x, y), 0, 1)[..., None]
    return a * wgt + sh * (1 - wgt)


def bark(src, dst_a, dst_n, strength):
    a = np.array(Image.open(src).convert("RGB")).astype(np.float32)
    t = tileable(a)
    alb = Image.fromarray(np.clip(t, 0, 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
    alb.save(dst_a)
    hgt = np.array(alb.convert("L").filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * strength
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * strength
    n = np.dstack([-dx, dy, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(dst_n)
    print("BARK", dst_a, dst_n)


if __name__ == "__main__":
    if sys.argv[1] == "leaf":
        leaf(sys.argv[2], sys.argv[3], sys.argv[4], "triple" in sys.argv[5:],
             edge_despill=EDGE_DESPILL if "--edge-despill" in sys.argv else 0, defringe="--defringe" in sys.argv)
    else:
        bark(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]))

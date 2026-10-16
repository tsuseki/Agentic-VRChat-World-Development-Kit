"""Fallback leaf/bark textures composed from CC0 scans (the first pass, before gpt-image sources).
Sources: Poly Haven models shrub_01, island_tree_02, fir_tree_01, pine_tree_01 (2k textures, unzipped
as <polyhaven>/<model>/textures/...) and the ambientCG Bark014_2K-JPG.zip.
  python tree_family_textures.py --polyhaven <dir> --bark-zip <Bark014_2K-JPG.zip> --out <dir> [Species ...]
Writes <out>/<Species>/<Species>_Leaves_RGBA.png, _Bark_Albedo.png, _Bark_Normal.png.
"""
import sys, random, math, zipfile, io, os
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

def _opt(k):
    if k not in sys.argv: sys.exit(f"missing {k}")
    i = sys.argv.index(k); v = sys.argv[i + 1]; del sys.argv[i:i + 2]; return v
if __name__ == "__main__":
    PH = os.path.abspath(_opt("--polyhaven")) + "/"
    BARKZIP = _opt("--bark-zip")
    ASSETS = os.path.abspath(_opt("--out")) + "/"
S = 2048

def load_pair(diff, alpha):
    d = Image.open(PH + diff)
    a = np.array(Image.open(PH + alpha).convert("L")) if alpha else np.array(d.split()[3])
    return d.convert("RGB"), a > 128

def extract(src, box, opening=3, narrow=1.0):
    d, a = src
    x0, y0, x1, y1 = box
    m = a[y0:y1, x0:x1]
    core = ndimage.binary_opening(m, iterations=opening) if opening else m
    lab, n = ndimage.label(core)
    if n == 0: raise RuntimeError(f"empty box {box}")
    sizes = ndimage.sum(core, lab, range(1, n + 1))
    keep = lab == int(np.argmax(sizes)) + 1
    if opening:  # grow back the fine edge (serration/needles) but only inside the original mask
        keep = ndimage.binary_dilation(keep, iterations=opening) & m
    ys, xs = np.nonzero(keep)
    keep = keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = d.crop((x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)).convert("RGBA")
    im.putalpha(Image.fromarray((keep * 255).astype(np.uint8)))
    if narrow != 1.0:
        im = im.resize((max(8, int(im.width * narrow)), im.height), Image.LANCZOS)
    return im

def grade(im, tint, sat, bright, mix):
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageEnhance.Color(rgb).enhance(sat)
    rgb = ImageEnhance.Brightness(rgb).enhance(bright)
    rgb = Image.blend(rgb, Image.new("RGB", rgb.size, tint), mix)
    out = rgb.convert("RGBA"); out.putalpha(a)
    return out

def paste_rot(canvas, im, h, ang, anchor):
    """Paste leaf `im` scaled to height h, rotated so its tip points along `ang` (0 = up),
    with its base at `anchor`."""
    im = im.resize((max(4, int(im.width * h / im.height)), int(h)), Image.LANCZOS)
    im = im.rotate(-math.degrees(ang), resample=Image.BICUBIC, expand=True)
    ox, oy = math.sin(ang) * h * 0.5, -math.cos(ang) * h * 0.5
    canvas.alpha_composite(im, (int(anchor[0] + ox - im.width / 2), int(anchor[1] + oy - im.height / 2)))

def finish(canvas, path):
    arr = np.array(canvas).astype(np.float32)
    a = arr[..., 3] > 127
    idx = ndimage.distance_transform_edt(~a, return_distances=False, return_indices=True)
    rgb = arr[..., :3][idx[0], idx[1]]
    Image.fromarray(np.dstack([rgb, np.where(a, 255, 0)]).astype(np.uint8), "RGBA").save(path)
    return a.mean()

def sprig_card(rng, leaf_fn, sprigs, lscale, spread, twig_col, twig_w=7):
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(canvas)
    for ang, ln, n in sprigs:
        cx, cy = S * 0.5, S * 0.97
        dx, dy = math.sin(ang), -math.cos(ang); L = ln * S
        ex, ey = cx + dx * L, cy + dy * L
        dr.line([(cx, cy), (ex, ey)], fill=twig_col, width=twig_w)
        for i in range(n):
            t = 0.15 + 0.85 * i / max(1, n - 1)
            p = (cx + dx * L * t, cy + dy * L * t)
            for side in (-1, 1):
                a = ang + math.radians(rng.uniform(*spread)) * side
                paste_rot(canvas, leaf_fn(), lscale * rng.uniform(0.85, 1.1) * S, a, p)
        paste_rot(canvas, leaf_fn(), lscale * S, ang, (ex, ey))
    return canvas

def spray_card(rng, sprays, n, scale):
    """Conifer: overlapping twig sprays fanned from the bottom centre."""
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for i in range(n):
        ang = (i / (n - 1) - 0.5) * 2.2 + rng.uniform(-0.12, 0.12)
        h = scale * S * rng.uniform(0.8, 1.05) * (1.0 - 0.25 * abs(ang))
        base = (S * 0.5 + math.sin(ang) * S * 0.08, S * 0.98 - abs(math.cos(ang)) * S * 0.02)
        paste_rot(canvas, rng.choice(sprays), h, ang, base)
    return canvas

def palmate(lobe, n=7):
    """Japanese maple leaf built from narrowed serrated lobes radiating from the petiole."""
    h = lobe.height; c = Image.new("RGBA", (int(h * 2.2), int(h * 2.0)), (0, 0, 0, 0))
    for k in range(n):
        a = (k / (n - 1) - 0.5) * math.radians(250)
        sc = 1.0 - 0.45 * abs(k / (n - 1) - 0.5) * 2
        paste_rot(c, lobe, h * sc, a, (c.width / 2, c.height * 0.62))
    bb = c.getbbox(); return c.crop(bb)

def bark_base():
    z = zipfile.ZipFile(BARKZIP)
    col = Image.open(io.BytesIO(z.read("Bark014_2K-JPG_Color.jpg"))).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    nrm = Image.open(io.BytesIO(z.read("Bark014_2K-JPG_NormalGL.jpg"))).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    return col, nrm

def flatten_normal(nrm, k):
    a = np.array(nrm).astype(np.float32)
    a[..., 0] = 128 + (a[..., 0] - 128) * k; a[..., 1] = 128 + (a[..., 1] - 128) * k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def bark(kind, rng):
    col, nrm = bark_base()
    if kind == "maple":
        b = ImageEnhance.Color(col).enhance(0.25).filter(ImageFilter.GaussianBlur(1.5))
        b = Image.blend(b, Image.new("RGB", b.size, (104, 98, 90)), 0.45); n = flatten_normal(nrm, 0.5)
    elif kind == "cypress":
        b = ImageEnhance.Color(col).enhance(0.6)
        b = Image.blend(b, Image.new("RGB", b.size, (92, 72, 58)), 0.3); n = nrm
    elif kind == "birch":
        g = ImageEnhance.Color(col).enhance(0.0).filter(ImageFilter.GaussianBlur(2))
        g = ImageEnhance.Contrast(g).enhance(0.35)
        b = Image.blend(g, Image.new("RGB", g.size, (232, 228, 220)), 0.72)
        dr = ImageDraw.Draw(b)
        for _ in range(260):  # horizontal lenticels
            x, y = rng.randint(0, 1023), rng.randint(0, 1023); w = rng.randint(14, 70)
            dr.line([(x, y), (x + w, y)], fill=(48, 44, 40), width=rng.choice((2, 3, 4)))
        for _ in range(10):  # dark scar patches
            x, y = rng.randint(0, 1023), rng.randint(0, 1023); w = rng.randint(30, 110)
            dr.ellipse([x, y, x + w, y + w * 0.18], fill=(70, 66, 60))
        b = b.filter(ImageFilter.GaussianBlur(0.8)); n = flatten_normal(nrm, 0.3)
    elif kind == "ficus":
        g = ImageEnhance.Color(col).enhance(0.1).filter(ImageFilter.GaussianBlur(5))
        b = Image.blend(g, Image.new("RGB", g.size, (150, 146, 138)), 0.6); n = flatten_normal(nrm, 0.25)
    elif kind == "pine":
        b = ImageEnhance.Contrast(col).enhance(1.25)
        b = Image.blend(b, Image.new("RGB", b.size, (128, 78, 52)), 0.2); n = nrm
    return b, n

SPECIES = {}
def species(f): SPECIES[f.__name__] = f; return f

@species
def JapaneseMaple(rng):
    src = load_pair("shrub_01/textures/shrub_01_diff_2k.jpg", "shrub_01/textures/shrub_01_alpha_2k.png")
    lobes = [extract(src, b, 8, 0.32) for b in [(900, 40, 1400, 740), (410, 840, 970, 1560), (1450, 800, 1900, 1420)]]
    leaves = [palmate(l) for l in lobes]
    tints = [((132, 16, 22), 0.3, 0.7, 0.72), ((104, 12, 26), 0.3, 0.6, 0.75), ((156, 30, 24), 0.3, 0.75, 0.7)]
    fn = lambda: grade(rng.choice(leaves), *rng.choice(tints))
    return sprig_card(rng, fn, [(-0.95, 0.42, 3), (-0.5, 0.6, 4), (-0.15, 0.72, 4), (0.2, 0.7, 4), (0.55, 0.6, 4), (0.95, 0.42, 3)],
                      0.13, (35, 70), (80, 34, 30, 255), 5), "maple"

@species
def ItalianCypress(rng):
    src = load_pair("fir_tree_01/textures/fir_tree_01_twig_diff_2k.png", "fir_tree_01/textures/fir_tree_01_twig_alpha_2k.png")
    sprays = [extract(src, b, 0) for b in [(1336, 82, 1921, 755), (387, 95, 878, 638), (626, 819, 1320, 1588), (1299, 926, 1961, 1700)]]
    sprays = [grade(s, (34, 52, 30), 0.8, 0.85, 0.45) for s in sprays] + [grade(s, (52, 68, 36), 0.8, 1.0, 0.4) for s in sprays]
    c = spray_card(rng, sprays, 15, 0.62)
    c2 = spray_card(rng, sprays, 11, 0.45); c.alpha_composite(c2)
    return c, "cypress"

@species
def BirchClump(rng):
    src = load_pair("shrub_01/textures/shrub_01_diff_2k.jpg", "shrub_01/textures/shrub_01_alpha_2k.png")
    leaves = [extract(src, b, 8) for b in [(900, 40, 1400, 740), (1520, 260, 1800, 680), (410, 840, 970, 1560), (1450, 800, 1900, 1420)]]
    tints = [((84, 118, 46), 0.9, 0.85, 0.3), ((104, 132, 52), 0.9, 0.95, 0.3), ((70, 96, 44), 0.85, 0.75, 0.35)]
    fn = lambda: grade(rng.choice(leaves), *rng.choice(tints))
    return sprig_card(rng, fn, [(-0.7, 0.5, 4), (-0.3, 0.7, 5), (0.05, 0.78, 5), (0.38, 0.7, 5), (0.75, 0.5, 4)],
                      0.13, (40, 70), (70, 52, 44, 255), 4), "birch"

@species
def Ficus(rng):
    src = load_pair("island_tree_02/textures/island_tree_02_leaves_diff_2k.png", "island_tree_02/textures/island_tree_02_leaves_alpha_2k.png")
    leaves = [extract(src, (x, y, x + w, y + h), 2) for x, y, w, h in [(33, 41, 265, 1005), (337, 41, 354, 762), (739, 62, 250, 678), (1059, 101, 271, 643), (444, 1180, 283, 868), (35, 1289, 338, 759)]]
    tints = [((30, 62, 30), 1.0, 0.75, 0.35), ((40, 78, 34), 1.0, 0.85, 0.3), ((24, 50, 28), 1.0, 0.65, 0.4)]
    fn = lambda: grade(rng.choice(leaves), *rng.choice(tints))
    c = sprig_card(rng, fn, [(-0.95, 0.45, 4), (-0.55, 0.62, 5), (-0.2, 0.74, 5), (0.15, 0.76, 5), (0.5, 0.64, 5), (0.9, 0.46, 4)],
                   0.15, (30, 60), (90, 84, 70, 255), 7)
    return c, "ficus"

@species
def StonePine(rng):
    d = Image.open(PH + "pine_tree_01/textures/pine_tree_01_twig_diff_2k.png")
    src = (d.convert("RGB"), np.array(d.split()[3]) > 128)
    sprays = [extract(src, (73, 90, 449, 905), 0), extract(src, (1335, 701, 1917, 1060), 0)]
    sprays[1] = sprays[1].rotate(90, expand=True) if sprays[1].width > sprays[1].height else sprays[1]
    sprays = [grade(s, (46, 70, 36), 1.1, 1.0, 0.35) for s in sprays] + [grade(s, (64, 84, 40), 1.0, 1.1, 0.3) for s in sprays]
    c = spray_card(rng, sprays, 13, 0.7)
    c.alpha_composite(spray_card(rng, sprays, 9, 0.5))
    return c, "pine"

if __name__ == "__main__":
    names = sys.argv[1:] or list(SPECIES)
    for name in names:
        rng = random.Random(sum(map(ord, name)))
        card, kind = SPECIES[name](rng)
        out = ASSETS + name + "/"
        os.makedirs(out, exist_ok=True)
        cov = finish(card, out + f"{name}_Leaves_RGBA.png")
        b, n = bark(kind, random.Random(5))
        b.save(out + f"{name}_Bark_Albedo.png"); n.save(out + f"{name}_Bark_Normal.png")
        print("TEX", name, "coverage", round(float(cov), 3))
    print("TEX_OK")

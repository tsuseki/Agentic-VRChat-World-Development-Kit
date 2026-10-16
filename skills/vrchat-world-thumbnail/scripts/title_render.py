"""Render a VRChat world-thumbnail title onto a clean capture with real fonts.

Exact spelling, exact size and exact position: never ask an image model to
draw the title (it drifts in size and font and can misspell).

Examples
  # Font candidates contact sheet (pick one, then render final):
  python title_render.py --base shot.png --rows "Mountain" "Lodge" --out-dir out --preview
  # Final:
  python title_render.py --base shot.png --rows "Mountain" "Lodge" --out-dir out --font cormorant

Run with any Python that has Pillow.
"""
import argparse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = Path(__file__).parent / "fonts"
GF = "https://github.com/google/fonts/raw/main/"
WIN = Path("C:/Windows/Fonts")

# Layout standard (fixed; matched to the approved "Cozy Airship" thumbnail):
ROW_WIDTH = 0.57   # widest row = 57% of image width, ~21% margin each side
CENTER_Y = 0.45    # block centre 45% from the top: over the hero subject
OUT_SIZE = (1200, 900)  # VRChat world image, 4:3
# Colours are per world (theme); these are only fallbacks.
FILL = "f6e8cc"
GLOW = "ffaa50"

# key: (file, download path or None for Windows font, axes, uppercase, tracking em, line gap em, theme)
FONTS = {
    # luxury / elegant
    "cinzel": ("Cinzel[wght].ttf", "ofl/cinzel/Cinzel%5Bwght%5D.ttf", {"wght": 600}, True, 0.06, 0.18, "luxury"),
    "playfair": ("PlayfairDisplay[wght].ttf", "ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf", {"wght": 500}, False, 0.0, 0.05, "luxury"),
    "cormorant": ("CormorantGaramond[wght].ttf", "ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf", {"wght": 600}, False, 0.0, 0.02, "luxury"),
    "bodoni_moda": ("BodoniModa[opsz,wght].ttf", "ofl/bodonimoda/BodoniModa%5Bopsz,wght%5D.ttf", {"opsz": 96, "wght": 500}, False, 0.0, 0.05, "luxury"),
    "italiana": ("Italiana-Regular.ttf", "ofl/italiana/Italiana-Regular.ttf", None, True, 0.08, 0.2, "luxury"),
    "engravers": ("ENGR.TTF", None, None, True, 0.04, 0.25, "luxury"),
    # cozy / warm / retro
    "fraunces": ("Fraunces[SOFT,WONK,opsz,wght].ttf", "ofl/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf", {"SOFT": 100, "wght": 700, "opsz": 144}, False, 0.0, 0.02, "cozy"),
    "sansita_swashed": ("SansitaSwashed[wght].ttf", "ofl/sansitaswashed/SansitaSwashed%5Bwght%5D.ttf", {"wght": 600}, False, 0.0, 0.02, "cozy"),
    "lobster": ("Lobster-Regular.ttf", "ofl/lobster/Lobster-Regular.ttf", None, False, 0.0, 0.0, "cozy"),
    # playful / cute
    "baloo2": ("Baloo2[wght].ttf", "ofl/baloo2/Baloo2%5Bwght%5D.ttf", {"wght": 700}, False, 0.0, -0.1, "playful"),
    "fredoka": ("Fredoka[wdth,wght].ttf", "ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf", {"wght": 600}, False, 0.0, 0.0, "playful"),
    "pacifico": ("Pacifico-Regular.ttf", "ofl/pacifico/Pacifico-Regular.ttf", None, False, 0.0, -0.1, "playful"),
    # sci-fi / tech
    "orbitron": ("Orbitron[wght].ttf", "ofl/orbitron/Orbitron%5Bwght%5D.ttf", {"wght": 700}, True, 0.08, 0.25, "scifi"),
    "audiowide": ("Audiowide-Regular.ttf", "ofl/audiowide/Audiowide-Regular.ttf", None, True, 0.04, 0.2, "scifi"),
    # spooky / dark
    "cinzel_decorative": ("CinzelDecorative-Bold.ttf", "ofl/cinzeldecorative/CinzelDecorative-Bold.ttf", None, True, 0.04, 0.2, "dark"),
    "creepster": ("Creepster-Regular.ttf", "ofl/creepster/Creepster-Regular.ttf", None, True, 0.04, 0.15, "dark"),
    # clean / modern
    "montserrat": ("Montserrat[wght].ttf", "ofl/montserrat/Montserrat%5Bwght%5D.ttf", {"wght": 600}, True, 0.12, 0.25, "modern"),
    "josefin_sans": ("JosefinSans[wght].ttf", "ofl/josefinsans/JosefinSans%5Bwght%5D.ttf", {"wght": 500}, True, 0.12, 0.25, "modern"),
}


def font_path(key):
    name, url, *_ = FONTS[key]
    if url is None:
        return WIN / name
    p = FONT_DIR / name
    if not p.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(GF + url, p)
    return p


def load(path, size, axes):
    f = ImageFont.truetype(str(path), size)
    if axes:
        vals = []
        for a in f.get_variation_axes():
            n = a["name"] if isinstance(a["name"], str) else a["name"].decode()
            key = {"Weight": "wght", "Optical size": "opsz", "Optical Size": "opsz"}.get(n, n)
            vals.append(axes.get(key, a["default"]))
        f.set_variation_by_axes(vals)
    return f


def row_width(font, text, tr):
    return sum(font.getlength(c) for c in text) + tr * (len(text) - 1)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render(base, rows, key, row_frac=ROW_WIDTH, center_y=CENTER_Y, fill=FILL, glow_col=GLOW):
    _, _, axes, upper, tracking, gap, _ = FONTS[key]
    path = font_path(key)
    fill, glow_col = hexrgb(fill), hexrgb(glow_col)
    img = Image.open(base).convert("RGB")
    W, H = img.size
    if upper:
        rows = [r.upper() for r in rows]
    f = load(path, 100, axes)
    size = int(100 * row_frac * W / max(row_width(f, r, tracking * 100) for r in rows))
    f = load(path, size, axes)
    tr = tracking * size
    asc, desc = f.getmetrics()
    line_h = asc + desc
    top = center_y * H - (line_h * len(rows) + gap * size * (len(rows) - 1)) / 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for i, r in enumerate(rows):
        x = (W - row_width(f, r, tr)) / 2
        for c in r:
            d.text((x, top + i * (line_h + gap * size)), c, font=f, fill=255)
            x += f.getlength(c) + tr
    shadow = mask.filter(ImageFilter.GaussianBlur(size * 0.06))
    img.paste(Image.new("RGB", (W, H), (10, 6, 4)), (0, 0), shadow.point(lambda v: int(v * 0.6)))
    glow = mask.filter(ImageFilter.GaussianBlur(size * 0.14))
    img = Image.composite(Image.new("RGB", (W, H), glow_col), img, glow.point(lambda v: int(v * 0.55)))
    img.paste(Image.new("RGB", (W, H), fill), (0, 0), mask)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="clean capture without text, 4:3")
    ap.add_argument("--rows", nargs="+", required=True, help="title rows, top to bottom")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--font", choices=sorted(FONTS), help="final font")
    ap.add_argument("--preview", action="store_true", help="render candidate fonts + contact sheet")
    themes = sorted({v[6] for v in FONTS.values()})
    ap.add_argument("--themes", nargs="+", choices=themes, help="limit the preview to font themes matching the world")
    ap.add_argument("--fill", default=FILL, help="text colour hex, chosen from the world's palette")
    ap.add_argument("--glow", default=GLOW, help="glow colour hex, chosen from the world's palette")
    ap.add_argument("--row-width", type=float, default=ROW_WIDTH)
    ap.add_argument("--center-y", type=float, default=CENTER_Y)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if a.preview:
        keys = sorted(k for k, v in FONTS.items() if not a.themes or v[6] in a.themes)
    elif a.font:
        keys = [a.font]
    else:
        ap.error("pass --font or --preview")
    made = []
    for k in keys:
        img = render(a.base, a.rows, k, a.row_width, a.center_y, a.fill, a.glow)
        full = out / f"title_{k}.png"
        img.save(full)
        img.resize(OUT_SIZE, Image.LANCZOS).save(out / f"title_{k}_1200x900.png")
        made.append((k, full))
        print(full)
    if a.preview:
        tw, th = 720, 540
        cols = 3
        rows_n = (len(made) + cols - 1) // cols
        sheet = Image.new("RGB", (tw * cols + 10 * (cols + 1), (th + 40) * rows_n + 10), (18, 18, 22))
        d = ImageDraw.Draw(sheet)
        lab = ImageFont.truetype(str(WIN / "arialbd.ttf"), 26)
        for i, (k, p) in enumerate(made):
            x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 40)
            sheet.paste(Image.open(p).resize((tw, th), Image.LANCZOS), (x, y))
            d.text((x + 4, y + th + 4), f"{i + 1}  {k} ({FONTS[k][6]})", font=lab, fill=(240, 200, 120))
        sheet.save(out / "contact_sheet.png")
        print(out / "contact_sheet.png")


if __name__ == "__main__":
    main()

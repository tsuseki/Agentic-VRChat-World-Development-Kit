"""Render a VRChat world-thumbnail title onto a clean capture with real fonts.

Exact spelling, exact size and exact position: never ask an image model to
draw the title (it drifts in size and font and can misspell).

Examples
  # Font candidates contact sheet (pick one, then render final):
  python title_render.py --base shot.png --rows "Mountain" "Lodge" --out-dir out --preview
  # Final:
  python title_render.py --base shot.png --rows "Mountain" "Lodge" --out-dir out --font cormorant
  # Optional small second-language row under the title, a quiet credit in the bottom band (full view only) and the
  # crop previews (full / world-menu tile with the platform badge / hover zoom / portal):
  python title_render.py --base shot.png --rows "Maple Lake" --sub "紅葉の湖" --sub-font klee_one \
      --credit "Trees: Temperate Forest Tree Pack · BOOTH" --out-dir out --font fraunces --crops

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
# Credit line: in the bottom band, which only the full view (website, loading screen) shows.
CREDIT_Y = 0.952   # credit centre, fraction of the height (the world-menu tile ends at 800/900 = 0.889)
CREDIT_PX = 21     # credit cap-to-descender size in px at 1200x900

# Crop geometry at 1200x900, measured from Maebbie's template
# (vrclibrary.com, "World Thumbnail/World Image Guide including a Template", 2025-08):
TILE = (0, 100, 1200, 800)              # world-menu tile (red box)
TILE_BADGE = (697, 100, 1200, 285)      # see-through PC/Quest platform badge on the tile
HOVER = (33, 121, 1167, 778)            # hover zoom (green box)
HOVER_BADGE = (683, 122, 1165, 302)     # badge on hover, nearly opaque
PORTAL_IN = (438, 399)                  # portal: always-visible ellipse semi-axes in the 1200x900 image, centred
PORTAL_OUT = (581, 524)                 # portal: cut-off ellipse (seen close up or at an angle), centred
# The portal squashes the image horizontally before showing it in a circle; on the template both ellipses become
# circles at x 0.91 (the guide's text says "about 33 %"; the drawn ellipses are what the preview trusts).
PORTAL_SQUASH = PORTAL_IN[1] / PORTAL_IN[0]

# key: (file, download path or None for Windows font, axes, uppercase, tracking em, line gap em, theme)
FONTS = {
    # luxury / elegant
    "cinzel": ("Cinzel[wght].ttf", "ofl/cinzel/Cinzel%5Bwght%5D.ttf", {"wght": 600}, True, 0.06, 0.18, "luxury"),
    "playfair": ("PlayfairDisplay[wght].ttf", "ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf", {"wght": 500}, False, 0.0, 0.05, "luxury"),
    "cormorant": ("CormorantGaramond[wght].ttf", "ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf", {"wght": 600}, False, 0.0, 0.02, "luxury"),
    "bodoni_moda": ("BodoniModa[opsz,wght].ttf", "ofl/bodonimoda/BodoniModa%5Bopsz,wght%5D.ttf", {"opsz": 96, "wght": 500}, False, 0.0, 0.05, "luxury"),
    "italiana": ("Italiana-Regular.ttf", "ofl/italiana/Italiana-Regular.ttf", None, True, 0.08, 0.2, "luxury"),
    "engravers": ("ENGR.TTF", None, None, True, 0.04, 0.25, "luxury"),
    # classical / sunlit Mediterranean (Roman inscriptional and humanist forms)
    "marcellus": ("Marcellus-Regular.ttf", "ofl/marcellus/Marcellus-Regular.ttf", None, False, 0.02, 0.05, "classical"),
    "marcellus_caps": ("Marcellus-Regular.ttf", "ofl/marcellus/Marcellus-Regular.ttf", None, True, 0.08, 0.2, "classical"),
    "forum": ("Forum-Regular.ttf", "ofl/forum/Forum-Regular.ttf", None, True, 0.08, 0.2, "classical"),
    "tenor_sans": ("TenorSans-Regular.ttf", "ofl/tenorsans/TenorSans-Regular.ttf", None, True, 0.1, 0.25, "classical"),
    "philosopher": ("Philosopher-Regular.ttf", "ofl/philosopher/Philosopher-Regular.ttf", None, False, 0.0, 0.05, "classical"),
    # Japanese (mincho families that carry both Latin and Japanese glyphs)
    "shippori_mincho": ("ShipporiMincho-SemiBold.ttf", "ofl/shipporimincho/ShipporiMincho-SemiBold.ttf", None, False, 0.02, 0.05, "japanese"),
    "shippori_b1": ("ShipporiMinchoB1-SemiBold.ttf", "ofl/shipporiminchob1/ShipporiMinchoB1-SemiBold.ttf", None, False, 0.02, 0.05, "japanese"),
    "zen_old_mincho": ("ZenOldMincho-SemiBold.ttf", "ofl/zenoldmincho/ZenOldMincho-SemiBold.ttf", None, False, 0.02, 0.05, "japanese"),
    "kaisei_decol": ("KaiseiDecol-Medium.ttf", "ofl/kaiseidecol/KaiseiDecol-Medium.ttf", None, False, 0.02, 0.05, "japanese"),
    "yu_mincho": ("yumindb.ttf", None, None, False, 0.02, 0.05, "japanese"),
    # rustic / woodland storybook
    "alegreya": ("Alegreya[wght].ttf", "ofl/alegreya/Alegreya%5Bwght%5D.ttf", {"wght": 600}, False, 0.0, 0.02, "rustic"),
    "young_serif": ("YoungSerif-Regular.ttf", "ofl/youngserif/YoungSerif-Regular.ttf", None, False, 0.0, 0.02, "rustic"),
    "vollkorn": ("Vollkorn[wght].ttf", "ofl/vollkorn/Vollkorn%5Bwght%5D.ttf", {"wght": 600}, False, 0.0, 0.02, "rustic"),
    "cormorant_sc": ("CormorantSC-SemiBold.ttf", "ofl/cormorantsc/CormorantSC-SemiBold.ttf", None, False, 0.04, 0.1, "rustic"),
    "cormorant_infant": ("CormorantInfant[wght].ttf", "ofl/cormorantinfant/CormorantInfant%5Bwght%5D.ttf", {"wght": 600}, False, 0.0, 0.02, "rustic"),
    "spectral": ("Spectral-Medium.ttf", "ofl/spectral/Spectral-Medium.ttf", None, False, 0.0, 0.02, "rustic"),
    # cozy / warm / retro
    "fraunces": ("Fraunces[SOFT,WONK,opsz,wght].ttf", "ofl/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf", {"SOFT": 100, "wght": 700, "opsz": 144}, False, 0.0, 0.02, "cozy"),
    "sansita_swashed": ("SansitaSwashed[wght].ttf", "ofl/sansitaswashed/SansitaSwashed%5Bwght%5D.ttf", {"wght": 600}, False, 0.0, 0.02, "cozy"),
    "lobster": ("Lobster-Regular.ttf", "ofl/lobster/Lobster-Regular.ttf", None, False, 0.0, 0.0, "cozy"),
    # beach / island
    "kaushan": ("KaushanScript-Regular.ttf", "ofl/kaushanscript/KaushanScript-Regular.ttf", None, False, 0.0, 0.0, "beach"),
    "yeseva": ("YesevaOne-Regular.ttf", "ofl/yesevaone/YesevaOne-Regular.ttf", None, False, 0.0, 0.02, "beach"),
    "grand_hotel": ("GrandHotel-Regular.ttf", "ofl/grandhotel/GrandHotel-Regular.ttf", None, False, 0.0, 0.0, "beach"),
    "caveat": ("Caveat[wght].ttf", "ofl/caveat/Caveat%5Bwght%5D.ttf", {"wght": 700}, False, 0.0, -0.05, "beach"),
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
    # subtitle rows in Japanese (--sub-font; never in a --preview: they are not title faces)
    "zen_maru": ("ZenMaruGothic-Medium.ttf", "ofl/zenmarugothic/ZenMaruGothic-Medium.ttf", None, False, 0.12, 0.0, "ja_sub"),
    "klee_one": ("KleeOne-SemiBold.ttf", "ofl/kleeone/KleeOne-SemiBold.ttf", None, False, 0.12, 0.0, "ja_sub"),
    "mplus_rounded": ("MPLUSRounded1c-Medium.ttf", "ofl/mplusrounded1c/MPLUSRounded1c-Medium.ttf", None, False, 0.12, 0.0, "ja_sub"),
    "zen_kaku": ("ZenKakuGothicNew-Medium.ttf", "ofl/zenkakugothicnew/ZenKakuGothicNew-Medium.ttf", None, False, 0.12, 0.0, "ja_sub"),
    "yu_gothic": ("YuGothM.ttc", None, None, False, 0.12, 0.0, "ja_sub"),
    # credit line (--credit-font)
    "josefin_light": ("JosefinSans[wght].ttf", "ofl/josefinsans/JosefinSans%5Bwght%5D.ttf", {"wght": 400}, False, 0.04, 0.0, "credit"),
    "montserrat_light": ("Montserrat[wght].ttf", "ofl/montserrat/Montserrat%5Bwght%5D.ttf", {"wght": 400}, False, 0.03, 0.0, "credit"),
}
NOT_TITLE = {"ja_sub", "credit"}


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


def load_key(key, size):
    return load(font_path(key), size, FONTS[key][2])


def row_width(font, text, tr):
    return sum(font.getlength(c) for c in text) + tr * (len(text) - 1)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _draw_row(d, W, y, text, font, tr):
    x = (W - row_width(font, text, tr)) / 2
    for c in text:
        d.text((x, y), c, font=font, fill=255)
        x += font.getlength(c) + tr


def _halo(img, mask, size, fill, glow_col, glow_alpha, shadow_alpha, glow_blur=0.14):
    W, H = img.size
    shadow = mask.filter(ImageFilter.GaussianBlur(size * 0.06))
    img.paste(Image.new("RGB", (W, H), (10, 6, 4)), (0, 0), shadow.point(lambda v: int(v * shadow_alpha)))
    glow = mask.filter(ImageFilter.GaussianBlur(size * glow_blur))
    if glow_blur > 0.14:   # a wide glow spreads thin: renormalise so its core still reaches glow_alpha
        peak = max(1, glow.getextrema()[1])
        glow = glow.point(lambda v: min(255, int(v * 255 / peak)))
    img = Image.composite(Image.new("RGB", (W, H), glow_col), img, glow.point(lambda v: int(v * glow_alpha)))
    img.paste(Image.new("RGB", (W, H), fill), (0, 0), mask)
    return img


def render(base, rows, key, row_frac=ROW_WIDTH, center_y=CENTER_Y, fill=FILL, glow_col=GLOW,
           sub=None, sub_key=None, sub_scale=0.38, sub_gap=0.22, sub_fill=None, sub_glow_alpha=None, sub_glow_blur=0.14,
           glow_alpha=0.55, shadow_alpha=0.6, credit=None, credit_key="josefin_light", credit_fill="ffffff",
           credit_alpha=0.82, credit_px=CREDIT_PX):
    """Title rows (widest = row_frac of the width, block centred at center_y). Without `sub` the layout is the
    standard line-box layout. With `sub` (a smaller row, e.g. a Japanese name, in `sub_key`, default the title font,
    `sub_scale` x the title size, `sub_gap` x the title size below the title ink) the ink box of the whole block is
    centred at center_y instead. `sub_glow_alpha` / `sub_glow_blur` (x the sub size) give the sub row its own, wider
    and stronger glow: a soft local dark band for a small row over a busy band such as a treeline.
    `credit`: one small line centred in the bottom band (full view only)."""
    _, _, axes, upper, tracking, gap, _ = FONTS[key]
    path = font_path(key)
    fill, glow_col = hexrgb(fill), hexrgb(glow_col)
    img = Image.open(base).convert("RGB") if not isinstance(base, Image.Image) else base.convert("RGB")
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
        _draw_row(d, W, top + i * (line_h + gap * size), r, f, tr)
    if sub:
        sk = sub_key or key
        _, _, _, s_upper, s_track, _, _ = FONTS[sk]
        stext = sub.upper() if s_upper else sub
        ssize = max(8, int(size * sub_scale))
        sf = load_key(sk, ssize)
        sw = row_width(sf, stext, s_track * ssize)
        if sw > row_frac * W:   # never wider than the title standard
            ssize = int(ssize * row_frac * W / sw)
            sf = load_key(sk, ssize)
        smask = Image.new("L", (W, H), 0)
        _draw_row(ImageDraw.Draw(smask), W, 0, stext, sf, s_track * ssize)
        tb, sb = mask.getbbox(), smask.getbbox()
        sy = tb[3] + sub_gap * size - sb[1]                  # sub ink top sits sub_gap below the title ink bottom
        block_top, block_bot = tb[1], sb[3] + sy
        dy = center_y * H - (block_top + block_bot) / 2       # centre the whole ink block
        mask = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(mask)
        for i, r in enumerate(rows):
            _draw_row(d, W, top + dy + i * (line_h + gap * size), r, f, tr)
        smask = Image.new("L", (W, H), 0)
        _draw_row(ImageDraw.Draw(smask), W, sy + dy, stext, sf, s_track * ssize)
        img = _halo(img, smask, ssize * 1.6, hexrgb(sub_fill) if sub_fill else fill, glow_col,
                    glow_alpha if sub_glow_alpha is None else sub_glow_alpha, shadow_alpha, sub_glow_blur)
    img = _halo(img, mask, size, fill, glow_col, glow_alpha, shadow_alpha)
    if credit:
        img = render_credit(img, credit, credit_key, credit_fill, credit_alpha, credit_px)
    return img


def render_credit(img, text, key="josefin_light", fill="ffffff", alpha=0.82, px=CREDIT_PX):
    """A small, quiet line centred in the bottom band (full view only), with a soft dark shadow."""
    W, H = img.size
    size = max(8, round(px * H / OUT_SIZE[1]))
    _, _, _, upper, tracking, _, _ = FONTS[key]
    text = text.upper() if upper else text
    f = load_key(key, size)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    _draw_row(d, W, 0, text, f, tracking * size)
    bb = mask.getbbox()
    mask = Image.new("L", (W, H), 0)
    _draw_row(ImageDraw.Draw(mask), W, CREDIT_Y * H - (bb[1] + bb[3]) / 2, text, f, tracking * size)
    img = img.copy()
    for blur, a in ((size * 0.7, 0.45), (size * 0.15, 0.6)):   # soft halo for bright ground, tight edge shadow
        sh = mask.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: min(255, int(v * 2.5)))
        img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh.point(lambda v: int(v * a)))
    img.paste(Image.new("RGB", (W, H), hexrgb(fill)), (0, 0), mask.point(lambda v: int(v * alpha)))
    return img


def _rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), r, fill=255)
    out = Image.new("RGB", im.size, (24, 24, 28))
    out.paste(im, (0, 0), m)
    return out


def _badge(im, box, alpha):
    """A stand-in for the PC/Quest platform badge: dark rounded panel with three platform circles."""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, (y1 - y0) // 3, fill=(20, 20, 24, alpha))
    r = (y1 - y0) * 0.3
    for k in range(3):
        cx, cy = x0 + (x1 - x0) * (0.22 + 0.28 * k), (y0 + y1) / 2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(235, 235, 235, min(255, alpha + 80)), width=max(2, int(r * 0.12)))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def crop_views(img):
    """The four places the image is shown, from a 1200x900 render: full, world-menu tile (with the see-through
    platform badge), hover zoom (badge nearly opaque) and the portal (squashed, ellipse cut-off)."""
    img = img.convert("RGB").resize(OUT_SIZE, Image.LANCZOS) if img.size != OUT_SIZE else img.convert("RGB")
    tile = _badge(img, TILE_BADGE, 110).crop(TILE)
    hover = _badge(img, HOVER_BADGE, 225).crop(HOVER)
    sq = img.resize((int(OUT_SIZE[0] * PORTAL_SQUASH), OUT_SIZE[1]), Image.LANCZOS)
    w, h = sq.size
    cx, cy = w / 2, h / 2
    ai, bi = PORTAL_IN[0] * PORTAL_SQUASH, PORTAL_IN[1]
    ao, bo = PORTAL_OUT[0] * PORTAL_SQUASH, PORTAL_OUT[1]
    m = Image.new("L", (w, h), 0)
    dm = ImageDraw.Draw(m)
    dm.ellipse((cx - ao, cy - bo, cx + ao, cy + bo), fill=110)
    dm.ellipse((cx - ai, cy - bi, cx + ai, cy + bi), fill=255)
    x0 = int(round(cx - h / 2))
    portal = Image.composite(sq, Image.new("RGB", (w, h), (8, 8, 10)), m).crop((x0, 0, x0 + h, h))
    return dict(full=img, tile=_rounded(tile, 40), hover=_rounded(hover, 40), portal=portal)


def crop_sheet(img, title=""):
    v = crop_views(img)
    lab = ImageFont.truetype(str(WIN / "arialbd.ttf"), 22)
    pw = 600
    panels = [("Full view (website, loading screen)", v["full"]), ("World menu tile (badge see-through)", v["tile"]),
              ("Hover zoom (badge nearly opaque)", v["hover"]), ("Portal (squashed; dim ring = seen at an angle only)", v["portal"])]
    ims = [(t, p.resize((pw, round(pw * p.size[1] / p.size[0])) if p is not v["portal"] else (450, 450), Image.LANCZOS)) for t, p in panels]
    W = 2 * pw + 30
    rows = [ims[0:2], ims[2:4]]
    hs = [max(i.size[1] for _, i in r) + 40 for r in rows]
    S = Image.new("RGB", (W, sum(hs) + 10 + (40 if title else 0)), (18, 18, 22))
    d = ImageDraw.Draw(S)
    y = 10
    if title:
        d.text((10, y), title, font=lab, fill=(240, 200, 120))
        y += 40
    for r, hh in zip(rows, hs):
        for k, (t, im) in enumerate(r):
            x = 10 + k * (pw + 10) + (pw - im.size[0]) // 2
            S.paste(im, (x, y))
            d.text((10 + k * (pw + 10), y + im.size[1] + 6), t, font=lab, fill=(220, 220, 220))
        y += hh
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="clean capture without text, 4:3")
    ap.add_argument("--rows", nargs="+", required=True, help="title rows, top to bottom")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--font", choices=sorted(FONTS), help="final font")
    ap.add_argument("--preview", action="store_true", help="render candidate fonts + contact sheet")
    themes = sorted({v[6] for v in FONTS.values()} - NOT_TITLE)
    ap.add_argument("--themes", nargs="+", choices=themes, help="limit the preview to font themes matching the world")
    ap.add_argument("--fonts", nargs="+", choices=sorted(FONTS), help="preview exactly these fonts")
    ap.add_argument("--fill", default=FILL, help="text colour hex, chosen from the world's palette")
    ap.add_argument("--glow", default=GLOW, help="glow colour hex, chosen from the world's palette")
    ap.add_argument("--glow-alpha", type=float, default=0.55)
    ap.add_argument("--shadow-alpha", type=float, default=0.6)
    ap.add_argument("--row-width", type=float, default=ROW_WIDTH)
    ap.add_argument("--center-y", type=float, default=CENTER_Y)
    ap.add_argument("--sub", help="optional smaller row under the title (e.g. the Japanese name)")
    ap.add_argument("--sub-font", choices=sorted(FONTS), help="font of the sub row (default: the title font)")
    ap.add_argument("--sub-scale", type=float, default=0.38, help="sub row size as a fraction of the title size")
    ap.add_argument("--sub-glow-alpha", type=float, help="sub row glow strength (default: --glow-alpha)")
    ap.add_argument("--sub-glow-blur", type=float, default=0.14,
                    help="sub row glow radius x its size; 0.3-0.5 = a soft local dark band over a busy treeline")
    ap.add_argument("--credit", help="small quiet line in the bottom band (full view only)")
    ap.add_argument("--credit-font", choices=sorted(FONTS), default="josefin_light")
    ap.add_argument("--credit-px", type=float, default=CREDIT_PX, help="credit size in px at 1200x900")
    ap.add_argument("--crops", action="store_true", help="also write <name>_crops.png (tile, hover, portal)")
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if a.preview:
        keys = a.fonts or sorted(k for k, v in FONTS.items() if v[6] not in NOT_TITLE and (not a.themes or v[6] in a.themes))
    elif a.font:
        keys = [a.font]
    else:
        ap.error("pass --font or --preview")
    made = []
    for k in keys:
        img = render(a.base, a.rows, k, a.row_width, a.center_y, a.fill, a.glow, sub=a.sub, sub_key=a.sub_font,
                     sub_scale=a.sub_scale, sub_glow_alpha=a.sub_glow_alpha, sub_glow_blur=a.sub_glow_blur,
                     glow_alpha=a.glow_alpha, shadow_alpha=a.shadow_alpha, credit=a.credit,
                     credit_key=a.credit_font, credit_px=a.credit_px)
        full = out / f"title_{k}.png"
        img.save(full)
        small = img.resize(OUT_SIZE, Image.LANCZOS)
        small.save(out / f"title_{k}_1200x900.png")
        if a.crops:
            crop_sheet(small, k).save(out / f"title_{k}_crops.png")
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

import sys
from PIL import Image, ImageDraw
# usage: compose.py out.png dir view name:label ...   (all tiles same scale; shared floor line)
out, d, view = sys.argv[1:4]; items = [a.split(":", 1) for a in sys.argv[4:]]
ims = []
for n, l in items:
    p = n if n.endswith(".png") else f"{d}/{n}_{view}.png"
    ims.append((Image.open(p).convert("RGB"), l))
W = sum(i.width for i, _ in ims); H = ims[0][0].height + 26
s = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(s); x = 0
for i, l in ims:
    s.paste(i, (x, 26)); dr.text((x + 8, 8), l, fill=(0, 0, 0)); x += i.width
s.save(out); print(out, s.size)

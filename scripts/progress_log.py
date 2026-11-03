#!/usr/bin/env python3
"""Append-only visual progress log for a world project: pictures first, a line or two of text.

Entries live in <project>/Design/progress/entries.json (append only); the page
<project>/Design/progress/index.html is rebuilt from them on every add (oldest first, newest at the bottom).

  python .omp/scripts/progress_log.py add <project> --stage "B.2" --title "Greybox built" \
      --text "One or two sentences." --img Design/concepts/gen07-grey/A_aerial_SE.png "caption" ...
  python .omp/scripts/progress_log.py build <project>

--img takes a path (relative to the project, or absolute inside it) and an optional caption; repeat it.
--when "YYYY-MM-DD HH:MM" backdates an entry (backfill); default is now.
Pictures are embedded in the page as JPEG thumbnails (data URIs): editor HTML previews (VS Code) block
relative local files, so a linked <img> shows nothing there. The full-size path is printed under each one.
Needs Pillow.
"""
import argparse
import base64
import datetime as dt
import html
import io
import json
import shutil
import sys
from pathlib import Path


def paths(project):
    root = Path(project).resolve()
    d = root / "Design" / "progress"
    d.mkdir(parents=True, exist_ok=True)
    return root, d, d / "entries.json", d / "index.html"


def load(f):
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def parse_imgs(argv_imgs, root, d):
    """Copy each image into <progress>/img/ so later renames or regenerations never break the log."""
    out = []
    snap = d / "img"
    snap.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    for item in argv_imgs or []:
        p = Path(item[0])
        p = (root / p) if not p.is_absolute() else p
        p = p.resolve()
        if not p.exists():
            sys.exit(f"image not found: {p}")
        try:
            src = p.relative_to(root).as_posix()
        except ValueError:
            sys.exit(f"image must be inside the project: {p}")
        copy = snap / f"{stamp}_{p.name}"
        shutil.copy2(p, copy)
        out.append({"path": copy.relative_to(root).as_posix(), "source": src,
                    "caption": item[1] if len(item) > 1 else ""})
    return out


CSS = """
:root{color-scheme:light}
html,body{background:#fff;color:#1f2328;margin:0;font:15px/1.45 system-ui,Segoe UI,sans-serif}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid #d0d7de;padding:10px 24px;z-index:2;
  display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
header h1{font-size:18px;margin:0} header a{color:#0969da;text-decoration:none;font-size:13px}
main{max-width:1400px;margin:0 auto;padding:8px 24px 80px}
section{border-bottom:1px solid #eaeef2;padding:18px 0}
.meta{color:#57606a;font-size:12px} .stage{display:inline-block;background:#ddf4ff;color:#0550ae;border-radius:10px;
  padding:0 8px;margin-right:6px;font-weight:600}
h2{font-size:16px;margin:4px 0 6px} p{margin:0 0 10px;max-width:900px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px}
figure{margin:0} figure img{width:100%;height:auto;display:block;border:1px solid #d0d7de;border-radius:4px;background:#f6f8fa}
figcaption{font-size:12px;color:#57606a;margin-top:3px}
.path{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#8c959f;word-break:break-all}
blockquote{margin:0 0 8px;padding:4px 10px;border-left:3px solid #bf8700;background:#fff8c5;max-width:900px;font-size:14px}
.who{font-weight:600;color:#7d4e00;margin-right:4px}
"""


def thumb_uri(p, width=960, quality=80):
    from PIL import Image
    with Image.open(p) as im:
        im = im.convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build(root, d, ef, hf):
    entries = load(ef)
    name = root.name
    rows = []
    for i, e in enumerate(entries):
        figs = []
        for im in e.get("images", []):
            absw = str((root / im["path"]).resolve())
            shown = str((root / im.get("source", im["path"])).resolve())
            img = (f'<img src="{thumb_uri(absw)}" alt="">' if Path(absw).exists()
                   else '<div class="path">(image no longer on disk)</div>')
            figs.append(
                f'<figure>{img}'
                f'<figcaption>{html.escape(im.get("caption", ""))}</figcaption>'
                f'<div class="path">{html.escape(shown)}</div></figure>')
        rows.append(
            f'<section id="e{i}"><div class="meta"><span class="stage">{html.escape(e.get("stage", ""))}</span>'
            f'{html.escape(e["when"])}</div><h2>{html.escape(e["title"])}</h2>'
            + (f'<p>{html.escape(e["text"])}</p>' if e.get("text") else "")
            + "".join(f'<blockquote><span class="who">User steered</span> “{html.escape(q)}”</blockquote>'
                      for q in e.get("steer", []))
            + f'<div class="grid">{"".join(figs)}</div></section>')
    last = f"#e{len(entries) - 1}" if entries else "#"
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(name)} progress</title>'
            f'<style>{CSS}</style></head><body><header><h1>{html.escape(name)} — progress log</h1>'
            f'<span class="meta">{len(entries)} entries · newest at the bottom</span><a href="{last}">jump to latest ↓</a>'
            f'</header><main>{"".join(rows)}</main></body></html>')
    hf.write_text(page, encoding="utf-8")
    return hf


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("add")
    a.add_argument("project")
    a.add_argument("--stage", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--text", default="")
    a.add_argument("--img", nargs="+", action="append", metavar=("PATH", "CAPTION"))
    a.add_argument("--steer", action="append", default=[], help="the user's exact words that steered this step (repeat)")
    a.add_argument("--when")
    b = sp.add_parser("build")
    b.add_argument("project")
    args = ap.parse_args()
    root, d, ef, hf = paths(args.project)
    if args.cmd == "add":
        entries = load(ef)
        when = args.when or dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        entries.append({"when": when, "stage": args.stage, "title": args.title, "text": args.text,
                        "steer": args.steer, "images": parse_imgs(args.img, root, d)})
        ef.write_text(json.dumps(entries, indent=1, ensure_ascii=False), encoding="utf-8")
    print(build(root, d, ef, hf))


if __name__ == "__main__":
    main()

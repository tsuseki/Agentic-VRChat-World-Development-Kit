#!/usr/bin/env python3
"""Append-only visual progress log for a world project: pictures first, a line or two of text.

Entries live in <project>/Design/progress/entries.json (append only); the page
<project>/Design/progress/index.html is rebuilt from them on every add (oldest first, newest at the bottom).

  python .omp/scripts/progress_log.py add <project> --stage "B.2" --title "Greybox built" \
      --text "One or two sentences." --img Design/concepts/gen07-grey/A_aerial_SE.png "caption" ...
  python .omp/scripts/progress_log.py build <project>

--img takes a path (relative to the project, or absolute inside it) and an optional caption; repeat it.
--when "YYYY-MM-DD HH:MM" backdates an entry (backfill); default is now.
"""
import argparse
import datetime as dt
import html
import json
import os
import sys
from pathlib import Path


def paths(project):
    root = Path(project).resolve()
    d = root / "Design" / "progress"
    d.mkdir(parents=True, exist_ok=True)
    return root, d, d / "entries.json", d / "index.html"


def load(f):
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def parse_imgs(argv_imgs, root):
    out = []
    for item in argv_imgs or []:
        p = Path(item[0])
        p = (root / p) if not p.is_absolute() else p
        p = p.resolve()
        if not p.exists():
            sys.exit(f"image not found: {p}")
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            sys.exit(f"image must be inside the project: {p}")
        out.append({"path": rel, "caption": item[1] if len(item) > 1 else ""})
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
"""


def build(root, d, ef, hf):
    entries = load(ef)
    name = root.name
    rows = []
    for i, e in enumerate(entries):
        figs = []
        for im in e.get("images", []):
            rel = os.path.relpath(root / im["path"], d).replace(os.sep, "/")
            absw = str((root / im["path"]).resolve())
            figs.append(
                f'<figure><a href="{html.escape(rel)}"><img loading="lazy" src="{html.escape(rel)}" alt=""></a>'
                f'<figcaption>{html.escape(im.get("caption", ""))}</figcaption>'
                f'<div class="path">{html.escape(absw)}</div></figure>')
        rows.append(
            f'<section id="e{i}"><div class="meta"><span class="stage">{html.escape(e.get("stage", ""))}</span>'
            f'{html.escape(e["when"])}</div><h2>{html.escape(e["title"])}</h2>'
            + (f'<p>{html.escape(e["text"])}</p>' if e.get("text") else "")
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
    a.add_argument("--when")
    b = sp.add_parser("build")
    b.add_argument("project")
    args = ap.parse_args()
    root, d, ef, hf = paths(args.project)
    if args.cmd == "add":
        entries = load(ef)
        when = args.when or dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        entries.append({"when": when, "stage": args.stage, "title": args.title, "text": args.text,
                        "images": parse_imgs(args.img, root)})
        ef.write_text(json.dumps(entries, indent=1, ensure_ascii=False), encoding="utf-8")
    print(build(root, d, ef, hf))


if __name__ == "__main__":
    main()

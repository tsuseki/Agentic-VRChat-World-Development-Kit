"""Scenario: is subject A drawn in observer B's personal mirror at a far spot?

Present/absent method (works for avatars a few pixels tall): B holds still with its mirror open; A is
parked at a reference spot out of view, two median frames give the noise map (TVs, fires, video);
A then teleports to --far-wp and a third median frame is diffed. Pixels that changed (d > --thresh)
where the noise map is quiet (< --noise) inside --roi are A. Repeated for each far clip in --fars
(screen camera far, metres; 0 = world default restore). The run with a far clip larger than the
distance is the positive control: it must find pixels, else the geometry or ROI is wrong.

B must already stand with its mirror open (see personal_mirror.py / toggle_personal_mirror).
Outputs per far clip: frame, zoomed crop around the detected (or control) spot, mask; summary.txt.

Usage: python mirror_presence.py --park-wp S1B_A_near --far-wp Spawn --fars 0,400 --repeat 2 \
          --roi 0.5,0.2,0.76,0.7 [--resize 3400x2000]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vrc_e2e as v  # noqa: E402


def frames(c: v.Client, n: int = 10, gap: float = 0.4) -> np.ndarray:
    """n frames over n * gap seconds: the median is the still image, the per-pixel range is the
    noise (idle sway of the observer's own reflection, fires, screens)."""
    fs = []
    for _ in range(n):
        fs.append(np.asarray(c.grab(), float))
        time.sleep(gap)
    return np.stack(fs)


def spread(st: np.ndarray) -> np.ndarray:
    return (st.max(axis=0) - st.min(axis=0)).max(axis=2)


def set_far(b: v.Client, far: int) -> None:
    if far <= 0:
        b.cmd(v.OP_RESTORE, 1)
    else:
        b.cmd(v.OP_FAR10, max(1, round(far / 10)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--park-wp", required=True, help="where A waits while absent")
    ap.add_argument("--far-wp", required=True, help="the far spot under test")
    ap.add_argument("--fars", default="0,400")
    ap.add_argument("--repeat", type=int, default=2)
    ap.add_argument("--roi", default="0,0,1,1")
    ap.add_argument("--thresh", type=float, default=12)
    ap.add_argument("--noise", type=float, default=6)
    ap.add_argument("--resize", default="", help="WxH for observer window during the test")
    ap.add_argument("--zoom", type=int, default=8)
    ap.add_argument("--observer", type=int, default=0)
    ap.add_argument("--subject", type=int, default=1)
    ap.add_argument("--project", default=".")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    man = v.load_manifest(a.project)
    cs = v.load()
    b, s = cs[a.observer], cs[a.subject]
    for c in (b, s):
        c.find_log()
        c.read_new()
    out = Path(a.project) / "E2E" / "runs" / ("presence_" + (a.tag + "_" if a.tag else "") + time.strftime("%Y%m%d_%H%M%S"))
    out.mkdir(parents=True, exist_ok=True)
    if a.resize:
        w, h = (int(t) for t in a.resize.split("x"))
        b.place(0, 0, w, h)
        time.sleep(3)
    x0, y0, x1, y1 = (float(t) for t in a.roi.split(","))
    lines, spot = [], None
    results = []
    for rep in range(a.repeat):
        for far in (int(f) for f in a.fars.split(",")):
            set_far(b, far)
            s.tp(a.park_wp, man)
            time.sleep(3.5)
            ab = frames(b)
            s.tp(a.far_wp, man)
            time.sleep(3.5)
            pr = frames(b)
            a2, t = np.median(ab, axis=0), np.median(pr, axis=0)
            noise = np.maximum(spread(ab), spread(pr))
            d = np.abs(t - a2).max(axis=2)
            H, W = d.shape
            m = (d > a.thresh) & (noise < a.noise)
            roi = np.zeros_like(m)
            roi[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = True
            m &= roi
            ys, xs = np.nonzero(m)
            c = (int(np.median(xs)), int(np.median(ys))) if len(xs) else None
            if c and spot is None:
                spot = c
            name = f"far{far or 'default'}_r{rep}"
            Image.fromarray(t.astype("uint8")).save(out / f"{name}_present.png")
            Image.fromarray(a2.astype("uint8")).save(out / f"{name}_absent.png")
            Image.fromarray((m * 255).astype("uint8")).save(out / f"{name}_mask.png")
            results.append((name, t, a2))
            line = f"{name:18s} pixels={len(xs):5d} centre={c}"
            print(line, flush=True)
            lines.append(line)
    set_far(b, 0)
    if spot:  # zoomed present/absent crops around the detected spot, same box for every run
        r = 40
        box = (spot[0] - r * 2, spot[1] - r, spot[0] + r * 2, spot[1] + r)
        tiles = []
        for name, t, a2 in results:
            for img in (t, a2):
                tiles.append(Image.fromarray(img.astype("uint8")).crop(box).resize(
                    ((box[2] - box[0]) * a.zoom // 2, (box[3] - box[1]) * a.zoom // 2), Image.NEAREST))
        tw, th = tiles[0].size
        sheet = Image.new("RGB", (tw * 2 + 10, (th + 10) * len(results)), "white")
        for i, tile in enumerate(tiles):
            sheet.paste(tile, ((i % 2) * (tw + 10), (i // 2) * (th + 10)))
        sheet.save(out / "zoom_sheet.png")
        lines.append(f"zoom_sheet rows: {[n for n, _, _ in results]} (left = A present, right = A absent); box={box}")
    if a.resize:  # menu templates are matched at the default tile size
        b.place(b.index * 1600, 0, 1600, 940)
    (out / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()

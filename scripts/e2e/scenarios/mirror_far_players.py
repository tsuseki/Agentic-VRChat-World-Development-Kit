"""Scenario: is a far-away player drawn in the personal mirror, and does the screen far clip cut it?

A distant avatar is a few pixels, so visibility is measured by motion: subject A jumps repeatedly
and B's window is diffed against a still frame; a run with A standing still gives the idle noise
(B's own reflection, TVs, fires), which is subtracted; B's own reflection band and anything
outside --roi are masked out.

Geometry: B stands at --b-wp, turns to yaw (--b-yaw-arg - 1) * 5 so that the line to A's far spot
is ~15 deg off the mirror axis (else B's own reflection hides A), then opens the personal mirror
(it spawns in front of B). The near control puts A at B's spot and walks it backwards
--near-walk seconds, i.e. a few metres toward the far spot, on the same bearing.

Runs: control_near (A a few m away; must be detected), far_default (world far clip),
      far_m (screen far clip --far10 * 10 m via op 20, more than the distance).

Usage: python mirror_far_players.py --b-wp S1B_MirrorB_FaceAwayHouse --b-yaw-arg 49 \
          --far-wp Spawn --near-walk 1.5 --far10 40 --roi 0.5,0.15,0.76,0.7
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


def motion(b: v.Client, s: v.Client, jump: bool, n: int = 8) -> np.ndarray:
    base = np.asarray(b.grab(), float)
    m = np.zeros(base.shape[:2])
    for _ in range(n):
        if jump:
            s.button("Jump", 0.1)
        time.sleep(0.35)
        m = np.maximum(m, np.abs(np.asarray(b.grab(), float) - base).max(axis=2))
        time.sleep(0.5)
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--b-wp", required=True)
    ap.add_argument("--b-yaw-arg", type=int, required=True)
    ap.add_argument("--far-wp", required=True)
    ap.add_argument("--near-walk", type=float, default=1.5)
    ap.add_argument("--far10", type=int, default=40)
    ap.add_argument("--thresh", type=float, default=20)
    ap.add_argument("--self-band", default="0.33,0.66", help="x fraction band of B's own reflection to ignore")
    ap.add_argument("--roi", default="", help="x0,y0,x1,y1 fractions to analyse (exclude TVs, fires)")
    ap.add_argument("--runs", default="control_near,far_default,far_m")
    ap.add_argument("--mirror-on", action="store_true", help="mirror on somewhere else: toggle it off first")
    ap.add_argument("--keep-mirror", action="store_true", help="B already placed with the mirror open")
    ap.add_argument("--project", default=".")
    a = ap.parse_args()

    man = v.load_manifest(a.project)
    b, s = v.load()[:2]
    for c in (b, s):
        c.find_log()
        c.read_new()
    out = Path(a.project) / "E2E" / "runs" / ("farplayers_" + time.strftime("%Y%m%d_%H%M%S"))
    out.mkdir(parents=True, exist_ok=True)
    if not a.keep_mirror:
        if a.mirror_on:
            b.toggle_personal_mirror()
            time.sleep(1)
        b.tp(a.b_wp, man)
        b.cmd(v.OP_YAW, a.b_yaw_arg)
        time.sleep(1.5)
        b.toggle_personal_mirror()
        time.sleep(1.5)

    lo, hi = (float(x) for x in a.self_band.split(","))
    runs = a.runs.split(",")
    lines = []
    for key, op in (("control_near", v.OP_RESTORE), ("far_default", v.OP_RESTORE), ("far_m", v.OP_FAR10)):
        if key not in runs:
            continue
        name = f"far_{a.far10 * 10}m" if key == "far_m" else key
        b.cmd(op, a.far10 if op == v.OP_FAR10 else 1)
        if key == "control_near":
            s.tp(a.b_wp, man)
            time.sleep(1)
            s.walk(-1.0, a.near_walk)
        else:
            s.tp(a.far_wp, man)
        time.sleep(4)
        still = motion(b, s, jump=False)
        moving = motion(b, s, jump=True)
        only = (moving > a.thresh) & (still <= a.thresh / 2)
        h, w = only.shape
        only[:, int(lo * w):int(hi * w)] = False
        if a.roi:
            x0, y0, x1, y1 = (float(t) for t in a.roi.split(","))
            roi = np.zeros_like(only)
            roi[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = True
            only &= roi
        ys, xs = np.nonzero(only)
        box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
        b.screenshot(str(out / f"{name}.png"))
        Image.fromarray((only * 255).astype("uint8")).save(out / f"{name}_jumpmask.png")
        line = f"{name:14s} jump-only pixels={len(xs):5d} box={box}"
        print(line)
        lines.append(line)
    b.cmd(v.OP_RESTORE)
    for c in (b, s):
        lines += [f"client{c.index}: {ln}" for ln in c.e2e_lines() if "tick" not in ln]
    (out / "log.txt").write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()

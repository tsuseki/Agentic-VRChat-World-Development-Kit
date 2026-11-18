"""Scenario: does the VRChat personal mirror follow world camera settings?

Two clients in a local test build with E2EHarness injected (E2EBuild.Start()).
Client 0 = viewer B (holds the personal mirror), client 1 = subject A (stands behind B, offset
sideways so B's own reflection doesn't hide A).
B goes to --b-wp, opens the personal mirror (Action Menu > Tools > Personal Mirror) and takes a
screenshot for every combination of A position x screen-camera setting:

  baseline : nothing changed
  cull<D>  : VRCCameraSettings.ScreenCamera player-layer cull distance D m (Player, PlayerLocal,
             MirrorReflection) + occlusion culling
  far<D>   : VRCCameraSettings.ScreenCamera far clip D m
  restore  : start settings back

Pick D between the near and far distances. Distances come from the harness state logs.
Reading: A gone from the mirror at the far spot only under cull/far -> the personal mirror follows
the screen camera (a world-side fix exists). A still visible -> it does not.

Usage (project folder with E2E/manifest.json, clients launched with vrc_e2e.py launch):
  python personal_mirror.py --b-wp S1B_MirrorB --near-wp S1B_A_near --far-wp S1B_A_far --dist 4
Outputs: E2E/runs/<timestamp>/*.png, sheet.jpg, log.txt
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vrc_e2e as v  # noqa: E402

POS = re.compile(r"pos=\((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)")


def my_pos(c: v.Client) -> tuple[float, ...]:
    c.cmd(v.OP_STATE)
    m = POS.search(c.wait_for(r"\[E2E\] state cmd", 10))
    return tuple(float(x) for x in m.groups())


def sheet(out: Path, names: list[str]) -> Path:
    from PIL import Image, ImageDraw
    w, h = 640, 358
    img = Image.new("RGB", (w * 2, len(names) // 2 * (h + 22)), (20, 20, 20))
    dr = ImageDraw.Draw(img)
    for i, n in enumerate(names):
        x, y = (i % 2) * w, (i // 2) * (h + 22) + 22
        img.paste(Image.open(out / f"{n}.png").convert("RGB").resize((w, h)), (x, y))
        dr.text((x + 6, y - 17), n, fill=(255, 255, 255))
    p = out / "sheet.jpg"
    img.save(p, quality=88)
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--b-wp", required=True)
    ap.add_argument("--near-wp", required=True)
    ap.add_argument("--far-wp", required=True)
    ap.add_argument("--dist", type=int, default=4)
    ap.add_argument("--project", default=".")
    ap.add_argument("--no-mirror-toggle", action="store_true", help="mirror already open on B")
    a = ap.parse_args()

    man = v.load_manifest(a.project)
    cs = {c.index: c for c in v.load()}
    b, s = cs[0], cs[1]
    out = Path(a.project) / "E2E" / "runs" / time.strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    names: list[str] = []

    def note(msg: str) -> None:
        print(msg)
        log.append(msg)

    for c in (b, s):
        c.find_log()
        c.read_new()
    b.tp(a.b_wp, man)
    s.tp(a.far_wp, man)
    time.sleep(2)
    if not a.no_mirror_toggle:
        b.toggle_personal_mirror()
        time.sleep(1.5)

    for setting, op in (("baseline", None), (f"cull{a.dist}", v.OP_CULL), ("restoreA", v.OP_RESTORE),
                        (f"far{a.dist}", v.OP_FAR), ("restoreB", v.OP_RESTORE)):
        if op is not None:
            b.cmd(op, a.dist)
        for spot, wp in (("near", a.near_wp), ("far", a.far_wp)):
            s.tp(wp, man)
            time.sleep(2.5)  # remote position sync + avatar settle
            pb, ps = my_pos(b), my_pos(s)
            d = math.dist((pb[0], pb[2]), (ps[0], ps[2]))
            name = f"B_{setting}_{spot}"
            b.screenshot(str(out / f"{name}.png"))
            names.append(name)
            note(f"{setting:9s} A {spot:4s} {d:5.2f} m from B  B@{pb}")
    for c in (b, s):
        for ln in c.e2e_lines():
            if "tick" not in ln:
                log.append(f"client{c.index}: {ln}")
    (out / "log.txt").write_text("\n".join(log), encoding="utf-8")
    print(sheet(out, names))


if __name__ == "__main__":
    main()

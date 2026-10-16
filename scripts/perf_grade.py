#!/usr/bin/env python3
"""Grade PerfSample JSON against this machine's benchmark bands and build attribution tables.

    python .omp/scripts/perf_grade.py --baseline base1.json [--baseline base2.json ...] \
        [variant.json ...] [--label variant.json=Name] [--static textureVramMB=339] \
        [--sort drawCalls] [--profile PATH]

Baselines are PerfSample runs with nothing disabled; give two or more (start and end of the
session) to measure the noise floor. Each variant is a run with one system disabled; its label is
the JSON's disabledRoots, or --label for systems toggled by hand via execute_code.

The profile defaults to .omp/local/benchmarks/<hostname>.json (personal, outside the kit's git), then
.omp/benchmarks/<hostname>.json. Bands are calibrated for one machine and
one editor setup only (see the profile's standardSetup); other machines get an error, not a grade.

Every run is also translated to the in-game benchmark scale: estimated VRChat desktop FPS from the
editor main thread (profile machine.editorToInGame) and its place among the worlds of the
worst-spot scale. Report that FPS with every editor measurement, next to the raw stats.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path

OMP = Path(__file__).resolve().parent.parent
# PerfSample JSON key -> profile band key; order is the report order.
SAMPLED = ["mainThreadMs", "cameraRenderMs", "gpuFrameMs", "behaviourUpdateMs", "drawCalls", "setPassCalls", "batches", "triangles"]
MS_METRICS = {"mainThreadMs", "cameraRenderMs", "gpuFrameMs", "behaviourUpdateMs"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def median(sample: dict, key: str) -> float | None:
    block = sample.get(key)
    return None if block is None else float(block["median"])


def band(profile: dict, key: str, value: float) -> str:
    b = profile["bands"].get(key)
    if b is None:
        return "-"
    if value <= b["green"]:
        return "GREEN"
    if value <= b["amber"]:
        return "AMBER"
    return "RED"


class InGame:
    """Editor main thread -> in-game desktop FPS, placed on the worst-spot world scale."""

    def __init__(self, profile: dict):
        t = profile.get("machine", {}).get("editorToInGame") or {}
        self.factor = t.get("factor")
        self.range = t.get("fittedRangeMs") or [0.0, float("inf")]
        self.worlds: list[dict] = []
        ref = t.get("scale", "")
        path, _, key = ref.partition("#")
        if path and (OMP / path).exists():
            ws = load_json(OMP / path).get(key or "worstSpotScale", {}).get("worlds", [])
            refs = [w for w in ws if w.get("reference")]
            self.worlds = refs or ws  # the user's reference worlds when marked, else every world

    def fps(self, main_thread_ms: float | None) -> float | None:
        if not self.factor or not main_thread_ms:
            return None
        return 1000.0 / (self.factor * main_thread_ms)

    def place(self, fps: float) -> str:
        """'between A (185) and B (184)', ranked among the scale's worlds (fastest first)."""
        ws = sorted(self.worlds, key=lambda w: -w["fps"])
        if not ws:
            return "no world scale"
        rank = sum(1 for w in ws if w["fps"] > fps) + 1
        above = ws[rank - 2] if rank >= 2 else None
        below = ws[rank - 1] if rank - 1 < len(ws) else None
        where = (f"below {above['world']} ({above['fps']:.0f})" if above else "fastest") + ", " + \
                (f"above {below['world']} ({below['fps']:.0f})" if below else "slowest")
        return f"#{rank} of {len(ws) + 1}: {where}"

    def note(self, main_thread_ms: float) -> str:
        lo, hi = self.range
        return "" if lo <= main_thread_ms <= hi else f" [outside the fitted {lo}-{hi} ms editor range: extrapolated]"


def fmt(key: str, v: float | None) -> str:
    if v is None:
        return "n/a"
    return f"{v:.2f}" if key in MS_METRICS else f"{v:,.0f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", action="append", required=True, type=Path)
    ap.add_argument("variants", nargs="*", type=Path)
    ap.add_argument("--label", action="append", default=[], help="variant.json=Name")
    ap.add_argument("--static", action="append", default=[], help="metric=value, e.g. textureVramMB=339")
    ap.add_argument("--sort", default="drawCalls", choices=SAMPLED)
    ap.add_argument("--profile", type=Path)
    a = ap.parse_args()

    host = socket.gethostname()
    profile_path = a.profile or next(
        (p for p in (OMP / "local" / "benchmarks" / f"{host}.json", OMP / "benchmarks" / f"{host}.json") if p.exists()),
        OMP / "local" / "benchmarks" / f"{host}.json")
    if not profile_path.exists():
        print(f"ERROR no benchmark profile for host {host} ({profile_path}); bands are machine-specific", file=sys.stderr)
        return 2
    profile = load_json(profile_path)

    bases = [load_json(p) for p in a.baseline]
    for p, b in zip(a.baseline, bases):
        if b.get("disabledRoots"):
            print(f"ERROR baseline {p} has disabledRoots {b['disabledRoots']}", file=sys.stderr)
            return 2

    base: dict[str, float | None] = {}
    noise: dict[str, float] = {}
    for k in SAMPLED:
        vals = [v for v in (median(b, k) for b in bases) if v is not None]
        base[k] = sum(vals) / len(vals) if vals else None
        noise[k] = (max(vals) - min(vals)) if len(vals) > 1 else 0.0

    print(f"Profile: {profile_path.name}  baselines: {len(bases)}  frames: {[b.get('frames') for b in bases]}")
    print("\n## Baseline vs bands\n")
    print("| metric | median | noise (range) | band | green <= | amber <= |")
    print("|---|---|---|---|---|---|")
    for k in SAMPLED:
        if base[k] is None:
            continue
        b = profile["bands"].get(k, {})
        print(f"| {k} | {fmt(k, base[k])} | {fmt(k, noise[k]) if len(bases) > 1 else 'one run'} | {band(profile, k, base[k])} "
              f"| {fmt(k, b.get('green'))} | {fmt(k, b.get('amber'))} |")
    for item in a.static:
        k, _, v = item.partition("=")
        val = float(v)
        b = profile["bands"].get(k, {})
        print(f"| {k} | {fmt(k, val)} | static | {band(profile, k, val)} | {fmt(k, b.get('green'))} | {fmt(k, b.get('amber'))} |")

    ig = InGame(profile)
    mt = base.get("mainThreadMs")
    est = ig.fps(mt)
    if est is None:
        print("\nIn-game estimate: n/a (no mainThreadMs in the sample or no machine.editorToInGame factor in the profile)")
    else:
        print(f"\n**In-game estimate: {est:.0f} FPS** (frame {1000 / est:.2f} ms = {ig.factor} x editor main thread {mt:.2f} ms), "
              f"{ig.place(est)}{ig.note(mt)}")

    if not a.variants:
        return 0

    labels = {}
    for item in a.label:
        path, _, name = item.partition("=")
        labels[Path(path).resolve()] = name
    rows = []
    for p in a.variants:
        v = load_json(p)
        name = labels.get(p.resolve()) or ", ".join(v.get("disabledRoots") or []) or p.stem
        delta = {}
        for k in SAMPLED:
            m = median(v, k)
            delta[k] = None if m is None or base[k] is None else base[k] - m
        rows.append((name, v.get("disabledRenderers"), delta))
    rows.sort(key=lambda r: -(r[2][a.sort] or 0.0))

    print(f"\n## Attribution (cost = baseline - run with the system off; sorted by {a.sort})\n")
    print("`~` marks a delta inside twice the baseline noise range.\n")
    head = ["system", "renderers off", "in-game FPS", "d in-game FPS"] + [f"d {k}" for k in SAMPLED] + [f"% of base {a.sort}"]
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    totals = {k: 0.0 for k in SAMPLED}
    for name, nr, delta in rows:
        cells = [name, "-" if nr is None else str(nr)]
        d_mt = delta.get("mainThreadMs")
        v_fps = ig.fps(mt - d_mt) if est is not None and d_mt is not None else None
        cells += ["n/a", "n/a"] if v_fps is None else [f"{v_fps:.0f}", f"{v_fps - est:+.0f}"]
        for k in SAMPLED:
            d = delta[k]
            if d is None:
                cells.append("n/a")
                continue
            totals[k] += d
            mark = "~" if len(bases) > 1 and abs(d) <= 2 * noise[k] else ""
            cells.append(mark + fmt(k, d))
        share = delta[a.sort]
        cells.append("n/a" if share is None or not base[a.sort] else f"{100 * share / base[a.sort]:.0f}%")
        print("| " + " | ".join(cells) + " |")
    print("| **sum of deltas** | | | | " + " | ".join(fmt(k, totals[k]) for k in SAMPLED) + " | |")
    print("| **baseline** | | " + ("n/a" if est is None else f"{est:.0f}") + " | | " + " | ".join(fmt(k, base[k]) for k in SAMPLED) + " | |")
    print("\n`in-game FPS` is the run's own estimate: the FPS the world would have with that system off.")
    print("\nDeltas are not additive: shared passes, batching and the per-frame floor make the sum differ from the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

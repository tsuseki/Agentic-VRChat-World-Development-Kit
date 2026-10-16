#!/usr/bin/env python3
"""Join VRChat-log markers from PerfCaptureTour with a PresentMon CSV, per viewpoint.

Usage:
  parse_capture.py --run LABEL VRCHAT_LOG PRESENTMON_CSV [--run LABEL2 LOG2 CSV2 ...]
                   [--trim 1.0] [--json out.json]

PresentMon must be run with --date_time (and v2 metrics, the default in 2.x), e.g.
  PresentMon-2.6.0-x64.exe --process_name VRChat.exe --date_time --output_file run.csv --no_console_stats

The VRChat log has one-second timestamps, so each window is trimmed by --trim seconds at both ends.
Prints one table per run and, with two runs, a per-viewpoint comparison (second vs first).
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import statistics
import sys

LOG_RX = re.compile(r"^(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}).*\[AWDK_PERF\] (begin|end) (\S+) loop=(\d+)")
FRAME_COLS = ["MsBetweenPresents", "FrameTime", "msBetweenPresents"]
GPU_COLS = ["MsGPUBusy", "GPUBusy", "MsGPUActive", "msGPUActive"]
CPU_COLS = ["MsCPUBusy", "CPUBusy"]
TIME_COLS = ["CPUStartDateTime", "TimeInDateTime", "CPUStartTime"]


def windows(log_path):
    begins, out = {}, []
    with open(log_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOG_RX.search(line)
            if not m:
                continue
            t = dt.datetime.strptime(m.group(1), "%Y.%m.%d %H:%M:%S")
            key = (m.group(3), int(m.group(4)))
            if m.group(2) == "begin":
                begins[key] = t
            elif key in begins:
                out.append((key[0], key[1], begins.pop(key), t))
    return out


def pick(header, names):
    for n in names:
        if n in header:
            return n
    return None


def parse_time(s):
    s = s.strip()
    # PresentMon --date_time: "2026-10-12 13:00:00.123456789" (nanoseconds); keep microseconds.
    m = re.match(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})(?:\.(\d+))?", s)
    if not m:
        return None
    base = dt.datetime.strptime(m.group(1).replace("T", " "), "%Y-%m-%d %H:%M:%S")
    frac = (m.group(2) or "0")[:6].ljust(6, "0")
    return base + dt.timedelta(microseconds=int(frac))


def frames(csv_path, offset_hours):
    """offset_hours: None = auto. PresentMon 2.6 date-times were observed 2 h ahead of local time
    on a UTC+2 host; auto aligns the last frame with the CSV's modification time (local)."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig", errors="replace") as f:
        r = csv.DictReader(f)
        h = r.fieldnames or []
        tc, fc, gc, cc = pick(h, TIME_COLS), pick(h, FRAME_COLS), pick(h, GPU_COLS), pick(h, CPU_COLS)
        if not tc or not fc:
            sys.exit(f"{csv_path}: need a date-time column ({TIME_COLS}) and a frame-time column ({FRAME_COLS}); got {h}")
        for row in r:
            t = parse_time(row[tc])
            try:
                ft = float(row[fc])
            except (TypeError, ValueError):
                continue
            g = _num(row.get(gc)) if gc else None
            c = _num(row.get(cc)) if cc else None
            if t:
                rows.append((t, ft, g, c))
    rows.sort()
    if rows:
        if offset_hours is None:
            mtime = dt.datetime.fromtimestamp(os.path.getmtime(csv_path))
            off = round((rows[-1][0] - mtime).total_seconds() / 1800) * 1800
        else:
            off = offset_hours * 3600
        if off:
            shift = dt.timedelta(seconds=off)
            rows = [(t - shift, ft, g, c) for t, ft, g, c in rows]
    return rows


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pct(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]


def summarize(log_path, csv_path, trim, offset_hours):
    fr = frames(csv_path, offset_hours)
    out = {}
    for name, loop, t0, t1 in windows(log_path):
        a, b = t0 + dt.timedelta(seconds=trim), t1 - dt.timedelta(seconds=trim)
        sel = [x for x in fr if a <= x[0] <= b]
        if not sel:
            continue
        ft = [x[1] for x in sel]
        g = [x[2] for x in sel if x[2] is not None]
        c = [x[3] for x in sel if x[3] is not None]
        e = out.setdefault(name, {"frames": 0, "ft": [], "gpu": [], "cpu": []})
        e["frames"] += len(sel)
        e["ft"] += ft
        e["gpu"] += g
        e["cpu"] += c
    res = {}
    for name, e in out.items():
        med = statistics.median(e["ft"])
        res[name] = {
            "frames": e["frames"],
            "frameMsMedian": med,
            "frameMsP95": pct(e["ft"], 95),
            "frameMsP99": pct(e["ft"], 99),
            "fpsMedian": 1000 / med if med else None,
            "gpuBusyMsMedian": statistics.median(e["gpu"]) if e["gpu"] else None,
            "cpuBusyMsMedian": statistics.median(e["cpu"]) if e["cpu"] else None,
        }
    return res


def fmt(v, d=2):
    return "-" if v is None else f"{v:.{d}f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", nargs=3, action="append", metavar=("LABEL", "LOG", "CSV"), required=True)
    ap.add_argument("--trim", type=float, default=1.0)
    ap.add_argument("--pm-offset-hours", type=float, default=None,
                    help="hours PresentMon date-times are ahead of the VRChat log clock (default: auto from CSV mtime)")
    ap.add_argument("--json", dest="out")
    a = ap.parse_args()

    runs = {label: summarize(log, csv_path, a.trim, a.pm_offset_hours) for label, log, csv_path in a.run}
    for label, res in runs.items():
        print(f"\n## {label}\n| viewpoint | frames | frame ms median | p95 | p99 | FPS median | GPU busy ms | CPU busy ms |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|")
        for vp, r in res.items():
            print(f"| {vp} | {r['frames']} | {fmt(r['frameMsMedian'])} | {fmt(r['frameMsP95'])} | {fmt(r['frameMsP99'])} | "
                  f"{fmt(r['fpsMedian'], 1)} | {fmt(r['gpuBusyMsMedian'])} | {fmt(r['cpuBusyMsMedian'])} |")
    labels = list(runs)
    if len(labels) >= 2:
        A, B = labels[0], labels[1]
        print(f"\n## {B} vs {A} (median frame ms; negative = faster)\n| viewpoint | {A} | {B} | delta ms | delta % |\n|---|---:|---:|---:|---:|")
        for vp in runs[A]:
            if vp in runs[B]:
                x, y = runs[A][vp]["frameMsMedian"], runs[B][vp]["frameMsMedian"]
                print(f"| {vp} | {fmt(x)} | {fmt(y)} | {fmt(y - x)} | {fmt(100 * (y - x) / x, 1)} |")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(runs, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

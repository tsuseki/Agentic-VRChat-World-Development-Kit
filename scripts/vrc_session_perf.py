#!/usr/bin/env python3
"""Record VRChat desktop frame times with PresentMon and split them per world visit and per spot.

    python .omp/scripts/vrc_session_perf.py record [--once] [--presentmon PATH]
    python .omp/scripts/vrc_session_perf.py analyze SESSION_DIR [SESSION_DIR ...] [--settle 15] [--spot 30]

record   waits for VRChat.exe, captures its frames with PresentMon (works without admin for a
         member of "Performance Log Users", by targeting the PID) until VRChat exits, then waits
         for the next launch (relaunches get their own session) until Ctrl+C; --once stops after
         one. Raw data goes to SESSIONS_ROOT/<stamp>/ (frames.csv + session.json), outside git.
analyze  reads those CSVs (one or more consecutive segments) and the VRChat output logs. Visits
         start at the first OnPlayerJoined after a "Joining" line (the world finished loading)
         plus --settle seconds, and end 5 s before the next join. Every F12 screenshot inside a
         visit marks a spot: the frames from 3 s after it (screenshot stall) to --spot seconds
         or the next screenshot. The printed table is spots only; whole-visit stats stay in
         report.json (written to the last SESSION_DIR with report.md). Reported verdicts (what
         players say about a world) go in SESSIONS_ROOT/verdicts.json:
         {"<world name>": {"verdict": "smooth|ok|laggy", "source": "..."}}; a
         SESSION_DIR/verdicts.json overrides them.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PRESENTMON = Path.home() / "Tools" / "PresentMon" / "PresentMon.exe"
SESSIONS_ROOT = Path.home() / "Tools" / "PresentMon" / "sessions"
VRC_LOG_DIR = Path.home() / "AppData" / "LocalLow" / "VRChat" / "VRChat"
SESSION_NAME = "VRCPerf"
SCREENSHOT_HITCH_S = 3.0  # the 4K F12 capture stalls frames for up to ~2.5 s
LEAVE_TRIM_S = 5.0  # the frames just before the next "Joining" are the portal/world-switch stall
LOG_TS = re.compile(r"^(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})")


def vrchat_pid() -> int | None:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq VRChat.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    for row in csv.reader(out.splitlines()):
        if len(row) > 1 and row[0].lower() == "vrchat.exe":
            return int(row[1])
    return None


def record_one(pm: Path) -> bool:
    """Record one VRChat launch; returns False when interrupted (Ctrl+C)."""
    print("Waiting for VRChat.exe ...", flush=True)
    try:
        while (pid := vrchat_pid()) is None:
            time.sleep(2)
    except KeyboardInterrupt:
        return False
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = SESSIONS_ROOT / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "frames.csv"
    start = datetime.now()
    proc = subprocess.Popen([str(pm), "--process_id", str(pid), "--output_file", str(csv_path),
                             "--date_time", "--no_console_stats", "--session_name", SESSION_NAME,
                             "--stop_existing_session"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (out_dir / "session.json").write_text(json.dumps(
        {"startLocal": start.isoformat(timespec="seconds"), "vrchatPid": pid, "csv": str(csv_path)},
        indent=2), encoding="utf-8")
    print(f"Recording VRChat pid {pid} -> {out_dir}", flush=True)
    interrupted = False
    try:
        while vrchat_pid() == pid and proc.poll() is None:
            time.sleep(5)
    except KeyboardInterrupt:
        interrupted = True
    subprocess.run([str(pm), "--terminate_existing_session", "--session_name", SESSION_NAME],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
    end = datetime.now()
    meta = json.loads((out_dir / "session.json").read_text(encoding="utf-8"))
    meta["endLocal"] = end.isoformat(timespec="seconds")
    (out_dir / "session.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Stopped after {(end - start).total_seconds():.0f} s. Session: {out_dir}", flush=True)
    return not interrupted


def record(args: argparse.Namespace) -> int:
    pm = Path(args.presentmon)
    if not pm.exists():
        print(f"PresentMon not found at {pm}", file=sys.stderr)
        return 1
    # Each VRChat launch becomes its own session; keep waiting for the next one (relaunches,
    # quick restarts) until --once or Ctrl+C.
    while record_one(pm) and not args.once:
        pass
    return 0


def parse_pm_time(s: str) -> datetime:
    # "2026-10-14 21:26:37.627231300": trim nanoseconds to microseconds for datetime.
    head, _, frac = s.partition(".")
    return datetime.strptime(f"{head}.{(frac + '000000')[:6]}", "%Y-%m-%d %H:%M:%S.%f")


def load_frames(csv_path: Path, start_local: datetime) -> list[tuple[datetime, float, float, float]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return []
    # VRChat can own more than one swap chain (e.g. a splash window); keep the busiest one.
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["SwapChainAddress"]] = counts.get(r["SwapChainAddress"], 0) + 1
    main = max(counts, key=counts.get)
    frames = []
    for r in rows:
        if r["SwapChainAddress"] != main:
            continue
        try:
            frames.append((parse_pm_time(r["CPUStartDateTime"]), float(r["MsBetweenPresents"]),
                           float(r["MsCPUBusy"]), float(r["MsGPUBusy"])))
        except (ValueError, KeyError):
            continue
    if frames:
        # PresentMon's --date_time clock can sit a whole time-zone offset away from local time on
        # this machine (observed +2 h under CEST). Snap the offset to 15 min and remove it.
        skew = (frames[0][0] - start_local).total_seconds()
        offset = timedelta(seconds=round(skew / 900) * 900)
        frames = [(t - offset, ft, c, g) for t, ft, c, g in frames]
    return frames


def load_events(start: datetime, end: datetime) -> list[tuple[datetime, str, str]]:
    events = []
    for log in sorted(VRC_LOG_DIR.glob("output_log_*.txt")):
        if datetime.fromtimestamp(log.stat().st_mtime) < start:
            continue
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            m = LOG_TS.match(line)
            if not m:
                continue
            t = datetime.strptime(m.group(1), "%Y.%m.%d %H:%M:%S")
            if t < start - timedelta(minutes=5) or t > end:
                continue
            if "[Behaviour] Entering Room: " in line:
                events.append((t, "room", line.split("Entering Room: ", 1)[1].strip()))
            elif "[Behaviour] Joining " in line and "Joining or Creating" not in line:
                events.append((t, "join", line.split("Joining ", 1)[1].strip()))
            elif "[Behaviour] OnPlayerJoined " in line:
                events.append((t, "player+", line.split("OnPlayerJoined ", 1)[1].strip()))
            elif "[Behaviour] OnPlayerLeft " in line:
                events.append((t, "player-", line.split("OnPlayerLeft ", 1)[1].strip()))
            elif "[VRC Camera] Took screenshot to: " in line:
                events.append((t, "shot", line.split("Took screenshot to: ", 1)[1].strip()))
    events.sort(key=lambda e: e[0])
    return events


def build_visits(events, end: datetime, settle: float) -> list[dict]:
    visits: list[dict] = []
    cur: dict | None = None
    room = None
    for t, kind, val in events:
        if kind == "room":
            room = val
        elif kind == "join":
            if cur:
                cur["end"] = t - timedelta(seconds=LEAVE_TRIM_S)
            cur = {"world": room, "instance": val, "joinedAt": t, "start": None, "end": end,
                   "players": 0, "maxPlayers": 0, "shots": []}
            visits.append(cur)
        elif cur is None:
            continue
        elif kind == "player+":
            if cur["start"] is None:
                cur["start"] = t + timedelta(seconds=settle)
            cur["players"] += 1
            cur["maxPlayers"] = max(cur["maxPlayers"], cur["players"])
        elif kind == "player-":
            cur["players"] = max(0, cur["players"] - 1)
        elif kind == "shot":
            cur["shots"].append((t, val))
    return [v for v in visits if v["start"] is not None and v["start"] < v["end"]]


def pct(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return float("nan")
    k = min(len(sorted_vals) - 1, max(0, round(p / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[k]


def stats(frames) -> dict | None:
    if len(frames) < 30:
        return None
    ft = sorted(f[1] for f in frames)
    cpu = sorted(f[2] for f in frames)
    gpu = sorted(f[3] for f in frames)
    worst = ft[-max(1, len(ft) // 100):]
    med = statistics.median(ft)
    gpu_med = statistics.median(gpu)
    return {
        "frames": len(ft),
        "seconds": round(sum(ft) / 1000, 1),
        "fpsAvg": round(1000 * len(ft) / sum(ft), 1),
        "fps1Low": round(1000 / statistics.mean(worst), 1),
        "frameMs": {"median": round(med, 2), "p95": round(pct(ft, 95), 2), "p99": round(pct(ft, 99), 2)},
        "cpuBusyMs": {"median": round(statistics.median(cpu), 2), "p95": round(pct(cpu, 95), 2)},
        "gpuBusyMs": {"median": round(gpu_med, 2), "p95": round(pct(gpu, 95), 2)},
        "hitchesPerMin": round(sum(1 for x in ft if x > max(3 * med, 50)) / (sum(ft) / 60000), 2),
        "bound": "GPU" if gpu_med >= 0.85 * med else "CPU",
    }


def window(frames, a: datetime, b: datetime):
    return [f for f in frames if a <= f[0] < b]


def analyze_session(sdir: Path, settle: float, spot: float) -> list[dict]:
    meta = json.loads((sdir / "session.json").read_text(encoding="utf-8"))
    start = datetime.fromisoformat(meta["startLocal"])
    frames = load_frames(sdir / "frames.csv", start)
    if not frames:
        print(f"{sdir.name}: no frames in frames.csv", file=sys.stderr)
        return []
    end = datetime.fromisoformat(meta["endLocal"]) if "endLocal" in meta else frames[-1][0]
    entries = []
    for v in build_visits(load_events(start, end), end, settle):
        entry = {"session": sdir.name, "world": v["world"], "instance": v["instance"],
                 "joinedAt": v["joinedAt"].isoformat(timespec="seconds"), "maxPlayers": v["maxPlayers"],
                 "visit": stats(window(frames, v["start"], v["end"])), "spots": []}
        spot_frames = []
        shots = v["shots"]
        for i, (t, path) in enumerate(shots):
            a = t + timedelta(seconds=SCREENSHOT_HITCH_S)
            b = min(t + timedelta(seconds=spot), v["end"],
                    shots[i + 1][0] if i + 1 < len(shots) else v["end"])
            w = window(frames, a, b) if (b - a).total_seconds() >= 10 else []
            s = stats(w)
            if s:
                spot_frames += w
                entry["spots"].append({"screenshot": path, "at": t.isoformat(timespec="seconds"), **s})
        entry["allSpots"] = stats(spot_frames)
        entries.append(entry)
    return entries


def analyze(args: argparse.Namespace) -> int:
    # Owner verdicts: SESSIONS_ROOT/verdicts.json, overridden per session by <session>/verdicts.json.
    verdicts: dict = {}
    for p in [SESSIONS_ROOT / "verdicts.json"] + [Path(s) / "verdicts.json" for s in args.sessions]:
        if p.exists():
            verdicts.update(json.loads(p.read_text(encoding="utf-8")))
    entries = []
    for s in args.sessions:
        entries += analyze_session(Path(s), args.settle, args.spot)
    for e in entries:
        e.update(verdicts.get(e["world"] or "", {}))
    out = Path(args.sessions[-1])
    (out / "report.json").write_text(json.dumps({"sessions": args.sessions, "visits": entries}, indent=2,
                                                ensure_ascii=False), encoding="utf-8")

    # Spots only: the frames after each F12, standing still at a view the owner chose as
    # representative. Whole-visit stats (walking, menus) stay in report.json. Worlds are ranked by
    # FPS over all their spots (uncapped, every frame's whole cost), fastest first.
    lines = ["| world | spot | FPS avg | 1% low | frame ms med/p95 | CPU busy med | GPU busy med | bound | hitches/min | reported |",
             "|---|---|---:|---:|---|---:|---:|---|---:|---|"]
    for e in sorted((e for e in entries if e["allSpots"]), key=lambda e: -e["allSpots"]["fpsAvg"]):
        rows = [(f"{s['at'][11:]}", s) for s in e["spots"]]
        if len(rows) > 1:
            rows.append(("all spots", e["allSpots"]))
        for where, s in rows:
            lines.append(f"| {e['world']} | {where} | {s['fpsAvg']} | {s['fps1Low']} | "
                         f"{s['frameMs']['median']}/{s['frameMs']['p95']} | {s['cpuBusyMs']['median']} | "
                         f"{s['gpuBusyMs']['median']} | {s['bound']} | {s['hitchesPerMin']} | "
                         f"{e.get('verdict', '')} |")
    md = "\n".join(lines)
    (out / "report.md").write_text(md + "\n", encoding="utf-8")
    print(md)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--presentmon", default=str(PRESENTMON))
    r.add_argument("--once", action="store_true", help="stop after one VRChat launch")
    a = sub.add_parser("analyze")
    a.add_argument("sessions", nargs="+", help="one or more session dirs (consecutive segments of a tour)")
    a.add_argument("--settle", type=float, default=15.0, help="seconds skipped after the world loads")
    a.add_argument("--spot", type=float, default=30.0, help="seconds measured after each F12 screenshot")
    args = ap.parse_args()
    return record(args) if args.cmd == "record" else analyze(args)


if __name__ == "__main__":
    sys.exit(main())

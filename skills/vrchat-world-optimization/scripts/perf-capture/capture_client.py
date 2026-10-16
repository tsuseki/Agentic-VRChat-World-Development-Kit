#!/usr/bin/env python3
"""Record one Build & Test client run end to end (Windows).

Run right after PerfCaptureRunner.StartBuildAndTest(). It:
  1. waits for VRChat.exe to start (the SDK launches it after the build),
  2. records VRChat.exe frames with PresentMon,
  3. waits for "[AWDK_PERF] done label=<label>" in the newest VRChat output log,
  4. closes the client, stops PresentMon, copies the log next to the CSV.

Usage:
  capture_client.py --label originals --out-dir DIR [--presentmon PATH]
                    [--launch-timeout 900] [--tour-timeout 900]
Exit code 0 = done marker seen; 2 = client never started; 3 = tour timed out (partial data kept).
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

LOG_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "LocalLow", "VRChat", "VRChat")


def running(name="VRChat.exe"):
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"], capture_output=True, text=True).stdout
    return name.lower() in out.lower()


def newest_log(since):
    logs = [p for p in glob.glob(os.path.join(LOG_DIR, "output_log_*.txt")) if os.path.getmtime(p) >= since - 5]
    return max(logs, key=os.path.getmtime) if logs else None


def find_presentmon(explicit):
    if explicit:
        return explicit
    hits = sorted(glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "PresentMon", "PresentMon-*-x64.exe")))
    if not hits:
        sys.exit("PresentMon not found; download the console exe from github.com/GameTechDev/PresentMon releases")
    return hits[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--presentmon")
    ap.add_argument("--launch-timeout", type=float, default=900)
    ap.add_argument("--tour-timeout", type=float, default=900)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    csv_path = os.path.join(a.out_dir, f"{a.label}.csv")
    log_copy = os.path.join(a.out_dir, f"{a.label}_output_log.txt")
    pm = find_presentmon(a.presentmon)
    t0 = time.time()

    if running():
        sys.exit("VRChat.exe is already running; close it first so the run is clean")
    print(f"waiting for VRChat.exe (build + launch, up to {a.launch_timeout:.0f}s)", flush=True)
    while not running():
        if time.time() - t0 > a.launch_timeout:
            print("client never started")
            return 2
        time.sleep(2)
    started = time.time()
    print(f"VRChat.exe up after {started - t0:.0f}s; recording", flush=True)

    rec = subprocess.Popen([pm, "--process_name", "VRChat.exe", "--date_time", "--output_file", csv_path,
                            "--no_console_stats", "--session_name", "awdk_capture", "--stop_existing_session",
                            "--terminate_on_proc_exit"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    marker = f"[AWDK_PERF] done label={a.label}"
    status = 3
    log = None
    while time.time() - started < a.tour_timeout:
        time.sleep(3)
        log = log or newest_log(started)
        if log:
            with open(log, encoding="utf-8", errors="replace") as f:
                if marker in f.read():
                    status = 0
                    break
        if not running():
            print("client exited before the tour finished")
            break
    print("tour complete" if status == 0 else "tour NOT complete", flush=True)

    subprocess.run(["taskkill", "/IM", "VRChat.exe", "/F"], capture_output=True)
    try:
        rec.wait(timeout=30)
    except subprocess.TimeoutExpired:
        subprocess.run([pm, "--terminate_existing_session", "--session_name", "awdk_capture"], capture_output=True)
        rec.kill()
    if log:
        shutil.copy2(log, log_copy)
    print(f"csv={csv_path}\nlog={log_copy if log else 'none'}")
    return status


if __name__ == "__main__":
    sys.exit(main())

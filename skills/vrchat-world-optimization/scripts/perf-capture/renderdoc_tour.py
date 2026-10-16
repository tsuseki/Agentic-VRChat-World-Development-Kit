#!/usr/bin/env python3
"""In-client RenderDoc frame captures at each PerfCaptureTour viewpoint (Windows, D3D11).

LOCAL BUILD & TEST ONLY, and only with the world owner's explicit approval (it injects RenderDoc
into the VRChat client). Never use it on a normal VRChat session.

Run right after PerfCaptureRunner.StartBuildAndTest(). It:
  1. waits for the Build & Test VRChat.exe, reads its exact command line and working dir, closes it,
  2. relaunches the same command under `renderdoccmd capture` (RenderDoc must hook at startup),
  3. on every "[AWDK_PERF] begin <viewpoint>" log marker, waits --delay seconds and sends F12
     (RenderDoc's capture key) to the VRChat window; renames each new .rdc to <viewpoint>.rdc,
  4. waits for "[AWDK_PERF] done label=<label>", closes the client,
  5. converts every capture to XML and counts draw calls per viewpoint.

Usage:
  renderdoc_tour.py --label merged --out-dir DIR [--renderdoc DIR] [--delay 3]
                    [--launch-timeout 900] [--tour-timeout 900]
  renderdoc_tour.py --count-only DIR      # re-count existing captures
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

LOG_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "LocalLow", "VRChat", "VRChat")
BEGIN_RX = re.compile(r"\[AWDK_PERF\] begin (\S+) loop=(\d+)")
DRAW_RX = re.compile(r'name="ID3D11(?:Device)?Context\d*::(Draw\w*)"')


def ps(cmd):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True).stdout.strip()


def vrchat_proc():
    out = ps("Get-CimInstance Win32_Process -Filter \"Name='VRChat.exe'\" | "
             "Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress")
    if not out:
        return None
    data = json.loads(out)
    return data[0] if isinstance(data, list) else data


def send_f12():
    # Bring VRChat to the foreground and press F12 (RenderDoc's default capture key).
    ps("Add-Type -AssemblyName Microsoft.VisualBasic; Add-Type -AssemblyName System.Windows.Forms; "
       "$p = Get-Process VRChat -ErrorAction SilentlyContinue | Select-Object -First 1; "
       "if ($p) { [Microsoft.VisualBasic.Interaction]::AppActivate($p.Id); Start-Sleep -Milliseconds 400; "
       "[System.Windows.Forms.SendKeys]::SendWait('{F12}') }")


def newest_log(since):
    logs = [p for p in glob.glob(os.path.join(LOG_DIR, "output_log_*.txt")) if os.path.getmtime(p) >= since - 5]
    return max(logs, key=os.path.getmtime) if logs else None


def count_draws(rdc, renderdoccmd):
    xml = rdc + ".xml"
    subprocess.run([renderdoccmd, "convert", "-f", rdc, "-o", xml, "-c", "xml"], capture_output=True)
    counts = {}
    if os.path.exists(xml):
        with open(xml, encoding="utf-8", errors="replace") as f:
            for m in DRAW_RX.finditer(f.read()):
                counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return {"draws": sum(counts.values()), "byCall": counts}


def count_dir(out_dir, renderdoccmd):
    res = {}
    for rdc in sorted(glob.glob(os.path.join(out_dir, "*.rdc"))):
        res[os.path.splitext(os.path.basename(rdc))[0]] = count_draws(rdc, renderdoccmd)
    print("| capture | draw calls |\n|---|---:|")
    for k, v in res.items():
        print(f"| {k} | {v['draws']} |")
    with open(os.path.join(out_dir, "renderdoc_draws.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label")
    ap.add_argument("--out-dir")
    ap.add_argument("--renderdoc", default=max(glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "RenderDoc", "RenderDoc_*_64")) or [""]))
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--launch-timeout", type=float, default=900)
    ap.add_argument("--tour-timeout", type=float, default=900)
    ap.add_argument("--count-only")
    a = ap.parse_args()
    rdcmd = os.path.join(a.renderdoc, "renderdoccmd.exe")
    if not os.path.exists(rdcmd):
        sys.exit("renderdoccmd.exe not found; download the portable zip from renderdoc.org/builds")
    if a.count_only:
        count_dir(a.count_only, rdcmd)
        return 0
    if not (a.label and a.out_dir):
        sys.exit("--label and --out-dir are required")
    os.makedirs(a.out_dir, exist_ok=True)

    t0 = time.time()
    print("waiting for the Build & Test client", flush=True)
    proc = None
    while not proc:
        if time.time() - t0 > a.launch_timeout:
            print("client never started")
            return 2
        time.sleep(2)
        proc = vrchat_proc()
    exe, cmdline = proc["ExecutablePath"], proc["CommandLine"]
    args = cmdline[cmdline.lower().find("vrchat.exe") + len("vrchat.exe"):].lstrip('" ')
    with open(os.path.join(a.out_dir, f"{a.label}_launch.txt"), "w", encoding="utf-8") as f:
        f.write(cmdline)
    subprocess.run(["taskkill", "/PID", str(proc["ProcessId"]), "/F"], capture_output=True)
    while vrchat_proc():
        time.sleep(1)

    template = os.path.join(a.out_dir, f"{a.label}_frame")
    launch = f'& "{rdcmd}" capture -d "{os.path.dirname(exe)}" -c "{template}" "{exe}" {args}'
    subprocess.Popen(["powershell", "-NoProfile", "-Command", launch])
    started = time.time()
    print("relaunched under RenderDoc", flush=True)

    seen, log, done = set(), None, False
    marker = f"[AWDK_PERF] done label={a.label}"
    while time.time() - started < a.tour_timeout:
        time.sleep(1)
        log = log or newest_log(started)
        if not log:
            continue
        with open(log, encoding="utf-8", errors="replace") as f:
            text = f.read()
        for m in BEGIN_RX.finditer(text):
            key = (m.group(1), m.group(2))
            if key in seen:
                continue
            seen.add(key)
            time.sleep(a.delay)
            before = set(glob.glob(template + "*.rdc"))
            send_f12()
            for _ in range(30):
                time.sleep(1)
                new = set(glob.glob(template + "*.rdc")) - before
                if new:
                    time.sleep(2)
                    dst = os.path.join(a.out_dir, f"{a.label}_{m.group(1)}_loop{m.group(2)}.rdc")
                    shutil.move(new.pop(), dst)
                    print(f"captured {dst}", flush=True)
                    break
            else:
                print(f"NO capture for {m.group(1)} (key not received?)", flush=True)
        if marker in text:
            done = True
            break
        if not vrchat_proc():
            print("client exited early")
            break

    subprocess.run(["taskkill", "/IM", "VRChat.exe", "/F"], capture_output=True)
    if log:
        shutil.copy2(log, os.path.join(a.out_dir, f"{a.label}_renderdoc_output_log.txt"))
    count_dir(a.out_dir, rdcmd)
    return 0 if done else 3


if __name__ == "__main__":
    sys.exit(main())

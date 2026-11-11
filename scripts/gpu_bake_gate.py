"""GPU gate for lightmap bakes: only one bake on the machine at a time.

Usage:
  python .omp/scripts/gpu_bake_gate.py check                 # exit 0 = free, 1 = busy (prints why)
  python .omp/scripts/gpu_bake_gate.py acquire --owner "<project>/<agent>"   # check + take the lock
  python .omp/scripts/gpu_bake_gate.py release --owner "<project>/<agent>"

Busy when ANY of:
  1. the lock file exists and is younger than its TTL (another agent announced a bake);
  2. a Bakery tracer process is running (ftrace*.exe, lmrebake*.exe, denoiser*.exe);
  3. GPU utilization averages >= 60 % over a 10 s sample (nvidia-smi; catches Progressive GPU,
     GLIM or anything else heavy). Idle editors sit around 10-25 %.
"""
import argparse, json, os, subprocess, sys, tempfile, time

LOCK = os.path.join(tempfile.gettempdir(), "awdk_gpu_bake.lock")
TTL_S = 3 * 3600  # stale lock after 3 h (crashed agent)
UTIL_BUSY = 60
SAMPLE_S = 10
BAKE_PROCS = ("ftrace", "lmrebake", "denoiser", "oidn", "optix")


def lock_state():
    if not os.path.exists(LOCK):
        return None
    try:
        with open(LOCK, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    age = time.time() - os.path.getmtime(LOCK)
    if age > TTL_S:
        return None
    d["age_min"] = round(age / 60, 1)
    return d


def bake_processes():
    try:
        out = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout
    except Exception:
        return []
    names = {line.split('","')[0].strip('"') for line in out.splitlines() if line}
    return sorted(n for n in names if n.lower().startswith(BAKE_PROCS))


def gpu_util():
    vals = []
    for _ in range(SAMPLE_S):
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=5)
            vals.append(int(r.stdout.split()[0]))
        except Exception:
            return None
        time.sleep(1)
    return sum(vals) / len(vals)


def check():
    reasons = []
    lk = lock_state()
    if lk:
        reasons.append(f"lock held by {lk.get('owner', '?')} for {lk['age_min']} min ({LOCK})")
    procs = bake_processes()
    if procs:
        reasons.append("bake processes running: " + ", ".join(procs))
    util = gpu_util()
    if util is None:
        reasons.append("nvidia-smi unavailable: cannot prove the GPU is free")
    elif util >= UTIL_BUSY:
        reasons.append(f"GPU utilization {util:.0f}% (>= {UTIL_BUSY}%) over {SAMPLE_S}s")
    return reasons, util


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "acquire", "release"])
    ap.add_argument("--owner", default="unknown")
    a = ap.parse_args()
    if a.cmd == "release":
        lk = lock_state()
        if lk and lk.get("owner") not in (a.owner, None):
            print(f"lock belongs to {lk.get('owner')}, not removed"); return 1
        if os.path.exists(LOCK):
            os.remove(LOCK)
        print("released"); return 0
    reasons, util = check()
    if reasons:
        print("BUSY: " + "; ".join(reasons)); return 1
    if a.cmd == "acquire":
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:  # stale lock past TTL, or a race
            if lock_state():
                print("BUSY: lock taken concurrently"); return 1
            os.remove(LOCK)
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"owner": a.owner, "since": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
        print(f"ACQUIRED by {a.owner} (GPU {util:.0f}%)"); return 0
    print(f"FREE (GPU {util:.0f}%)"); return 0


if __name__ == "__main__":
    sys.exit(main())

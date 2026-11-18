"""AWDK multi-client E2E driver for LOCAL VRChat test worlds (Build & Test style).

What it does, using only unmodified clients and their official interfaces:
  * launches N desktop clients on a local .vrcw, exactly like the SDK's Build & Test
    (--url=create?roomId=..&hidden=true&name=BuildAndRun&url=file:///..), each with its own
    --profile and its own --osc port, windowed and tiled;
  * drives each client through VRChat's official OSC input (/input/*, /chatbox/*);
  * sends E2EHarness commands (teleport to waypoint, interact with a target, log state, camera
    probe) through the OSC movement axes (see .omp/templates/e2e/E2EHarness.cs.txt);
  * reads each client's own output_log and returns its "[E2E]" lines;
  * screenshots a client window and clicks inside it (client menus such as the personal mirror).

Safety rules (enforced here, keep them):
  * never inject into, patch or attach to a VRChat process; no mods, no memory access;
  * only touch processes this module launched (tracked by pid); never the user's own client;
  * OSC ports 9100+ only (a normal client listens on 9000);
  * test clients only join local test worlds (file:// .vrcw), never online instances.

CLI: python vrc_e2e.py --help
"""
from __future__ import annotations

import argparse
import ctypes
import glob
import json
import os
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from pythonosc.udp_client import SimpleUDPClient

STEAM_EXE = Path(r"C:\Program Files (x86)\Steam\steamapps\common\VRChat\VRChat.exe")
LOG_DIR = Path(os.environ["LOCALAPPDATA"]).parent / "LocalLow" / "VRChat" / "VRChat"
WORLDS_DIR = LOG_DIR / "Worlds"
BASE_PORT = 9100
STATE_FILE = Path(__file__).with_name("clients.json")

OP_TP, OP_INTERACT, OP_STATE, OP_LIST, OP_YAW, OP_RESPAWN, OP_CAMS, OP_CULL, OP_FAR, OP_RESTORE, OP_FAR10 = 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()  # window rects, cursor and screenshots all in physical pixels


@dataclass
class Client:
    index: int
    pid: int
    profile: int
    osc_port: int
    log: str = ""
    started: float = 0.0
    log_pos: int = field(default=0)

    @property
    def osc(self) -> SimpleUDPClient:
        return SimpleUDPClient("127.0.0.1", self.osc_port)

    # ---- OSC input -------------------------------------------------------
    def axis(self, name: str, value: float) -> None:
        self.osc.send_message(f"/input/{name}", float(value))

    def button(self, name: str, hold: float = 0.15) -> None:
        self.osc.send_message(f"/input/{name}", 1)
        time.sleep(hold)
        self.osc.send_message(f"/input/{name}", 0)

    def walk(self, forward: float = 1.0, seconds: float = 1.0, right: float = 0.0) -> None:
        self.axis("Vertical", forward)
        self.axis("Horizontal", right)
        time.sleep(seconds)
        self.axis("Vertical", 0.0)
        self.axis("Horizontal", 0.0)

    def turn(self, value: float = 1.0, seconds: float = 0.5) -> None:
        self.axis("LookHorizontal", value)
        time.sleep(seconds)
        self.axis("LookHorizontal", 0.0)

    def say(self, text: str) -> None:
        self.osc.send_message("/chatbox/input", [text[:144], True, False])

    # ---- harness commands --------------------------------------------------
    @staticmethod
    def encode(code: int) -> float:
        """The client remaps OSC movement axes through a 0.1 deadzone before Udon sees them:
        udon = (osc - 0.1) / 0.9 (measured: 0.2->0.1111, 0.5->0.4444, 0.9->0.8889; 0.05->0).
        Invert it so Udon receives exactly code/100."""
        return 0.1 + 0.9 * code / 100.0

    def cmd(self, op: int, arg: int = 1, settle: float = 0.25) -> None:
        if not (1 <= arg <= 98 and 2 <= op <= 98):
            raise ValueError("op 2..98, arg 1..98")
        self.axis("Vertical", self.encode(arg))
        time.sleep(settle)
        self.axis("Horizontal", self.encode(op))
        time.sleep(settle)
        self.axis("Horizontal", 0.0)
        self.axis("Vertical", 0.0)
        time.sleep(settle)

    def indexed(self, op: int, index: int) -> None:
        """Ops 10/11 take a 1-based list index; lists longer than 98 are paged (op 9)."""
        page, a = divmod(index - 1, 98)
        self.cmd(9, page + 1)
        self.cmd(op, a + 1)

    def tp(self, waypoint: int | str, manifest: dict | None = None) -> None:
        self.indexed(OP_TP, resolve(waypoint, manifest, "waypoints", "name"))

    def interact(self, target: int | str, manifest: dict | None = None) -> None:
        self.indexed(OP_INTERACT, resolve(target, manifest, "targets", "path"))

    # ---- log ---------------------------------------------------------------
    def find_log(self, timeout: float = 120) -> str:
        """The client's output_log: the newest log created after launch that names our port."""
        end = time.time() + timeout
        while time.time() < end:
            for f in sorted(glob.glob(str(LOG_DIR / "output_log_*.txt")), key=os.path.getmtime, reverse=True):
                if os.path.getctime(f) < self.started - 2:
                    continue
                try:
                    head = Path(f).read_text(encoding="utf-8", errors="ignore")[:400000]
                except OSError:
                    continue
                if re.search(rf"\b{self.osc_port}\b", head):
                    self.log = f
                    return f
            time.sleep(2)
        raise TimeoutError(f"no output_log for client {self.index} (port {self.osc_port})")

    def read_new(self) -> list[str]:
        if not self.log:
            self.find_log()
        with open(self.log, "r", encoding="utf-8", errors="ignore") as fh:
            fh.seek(self.log_pos)
            data = fh.read()
            self.log_pos = fh.tell()
        return [ln.strip() for ln in data.splitlines() if ln.strip()]

    def e2e_lines(self) -> list[str]:
        return [ln[ln.index("[E2E]"):] for ln in self.read_new() if "[E2E]" in ln]

    def wait_for(self, pattern: str, timeout: float = 60) -> str:
        rx = re.compile(pattern)
        end = time.time() + timeout
        while time.time() < end:
            for ln in self.read_new():
                if rx.search(ln):
                    return ln
            time.sleep(0.5)
        raise TimeoutError(f"client {self.index}: no line matching {pattern!r}")

    # ---- window ------------------------------------------------------------
    def hwnd(self) -> int:
        found = []

        def cb(h, _):
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
            if pid.value == self.pid and user32.IsWindowVisible(h):
                found.append(h)
            return True

        user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)
        if not found:
            raise RuntimeError(f"client {self.index}: no window")
        return found[0]

    def place(self, x: int, y: int, w: int, h: int) -> None:
        user32.MoveWindow(self.hwnd(), x, y, w, h, True)

    def focus(self) -> None:
        import win32con, win32gui
        h = self.hwnd()
        win32gui.ShowWindow(h, win32con.SW_RESTORE)
        # Alt tap lets SetForegroundWindow succeed from a background process.
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        win32gui.SetForegroundWindow(h)
        time.sleep(0.3)

    def rect(self) -> tuple[int, int, int, int]:
        import win32gui
        h = self.hwnd()
        l, t, r, b = win32gui.GetClientRect(h)
        x, y = win32gui.ClientToScreen(h, (0, 0))
        return x, y, r - l, b - t

    def screenshot(self, path: str) -> str:
        import mss, mss.tools
        self.focus()
        x, y, w, h = self.rect()
        with mss.mss() as s:
            img = s.grab({"left": x, "top": y, "width": w, "height": h})
            mss.tools.to_png(img.rgb, img.size, output=path)
        return path

    def click(self, fx: float, fy: float) -> None:
        """Click at a fraction of the client area (0..1)."""
        self.focus()
        x, y, w, h = self.rect()
        user32.SetCursorPos(int(x + fx * w), int(y + fy * h))
        time.sleep(0.1)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.3)

    def mouse(self, dx: int = 0, dy: int = 0, click: bool = False, steps: int = 10) -> None:
        """Relative mouse motion (raw input, what the locked desktop camera and the Action Menu
        radial read), optionally followed by a left click at the current position."""
        self.focus()
        for _ in range(steps):
            user32.mouse_event(0x0001, int(dx / steps), int(dy / steps), 0, 0)
            time.sleep(0.02)
        time.sleep(0.2)
        if click:
            user32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.05)
            user32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(0.4)

    # ---- client menus (desktop, 2026.4 UI; re-check with screenshots after client updates) ----
    # The Action Menu (R) reopens on the last submenu it showed, so every navigation first reads
    # which page is open from the icon at the top of the radial (templates in ui/, captured at a
    # 1578x884 client area) and only then moves. Radial items are chosen by direction from the
    # centre; the pointer recentres on open and on entering a submenu.
    AM_TOP = (887, 465, 947, 525)  # top icon box at 1578x884

    def grab(self):
        import mss
        from PIL import Image
        x, y, w, h = self.rect()
        with mss.mss() as s:
            img = s.grab({"left": x, "top": y, "width": w, "height": h})
        return Image.frombytes("RGB", img.size, img.rgb)

    def action_menu_page(self) -> str:
        import numpy as np
        from PIL import Image
        img = self.grab()
        sx, sy = img.width / 1578, img.height / 884
        l, t, r, b = self.AM_TOP
        patch = np.asarray(img.crop((int(l * sx), int(t * sy), int(r * sx), int(b * sy))).resize((60, 60)), float)
        best, name = 1e9, "unknown"
        for page in ("root", "submenu_tools"):
            ref = np.asarray(Image.open(Path(__file__).with_name("ui") / f"am_{page}.png").convert("RGB"), float)
            d = float(np.abs(patch - ref).mean())
            if d < best:
                best, name = d, page
        return name if best < 25 else "unknown"

    def toggle_personal_mirror(self) -> None:
        """Action Menu > Tools > Personal Mirror. The mirror spawns ~1 m in front of the player;
        stand with free space ahead or it clips into walls."""
        self.key(0x52)
        time.sleep(0.8)
        page = self.action_menu_page()
        if page == "root":
            self.mouse(-150, -80, click=True)  # Tools (up-left)
            time.sleep(0.6)
            page = self.action_menu_page()
        if page != "submenu_tools":
            self.key(0x52)
            raise RuntimeError(f"client {self.index}: Action Menu page {page!r}, expected Tools")
        self.mouse(320, 0, click=True)  # Personal Mirror (right)
        time.sleep(0.5)
        self.key(0x52)
        time.sleep(0.5)

    def key(self, vk: int, hold: float = 0.08) -> None:
        """Press a key in this client's window. Sent as a hardware scancode (SendInput with
        KEYEVENTF_SCANCODE): Unity reads raw keyboard input and ignores virtual-key-only events."""
        self.focus()
        if user32.GetForegroundWindow() != self.hwnd():
            raise RuntimeError(f"client {self.index}: window did not take focus")
        scan = user32.MapVirtualKeyW(vk, 0)
        _send_scan(scan, False)
        time.sleep(hold)
        _send_scan(scan, True)
        time.sleep(0.3)

class _KI(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_size_t)]


class _INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KI), ("pad", ctypes.c_byte * 32)]
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_ulong), ("u", _U)]


def _send_scan(scan: int, up: bool) -> None:
    inp = _INPUT(type=1)  # INPUT_KEYBOARD
    inp.ki = _KI(0, scan, 0x0008 | (0x0002 if up else 0), 0, 0)  # KEYEVENTF_SCANCODE | KEYUP
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))



def resolve(key: int | str, manifest: dict | None, section: str, field_: str) -> int:
    if isinstance(key, int):
        return key
    if manifest is None:
        raise ValueError("pass the manifest to address by name")
    for item in manifest[section]:
        if item[field_] == key or item[field_].endswith("/" + key):
            return item["index"]
    raise KeyError(f"{key!r} not in manifest {section}")


def load_manifest(project: str) -> dict:
    return json.loads((Path(project) / "E2E" / "manifest.json").read_text(encoding="utf-8"))


def latest_vrcw(scene_hint: str = "") -> Path:
    files = sorted(WORLDS_DIR.glob(f"scene-standalonewindows64-{scene_hint.lower()}*.vrcw"), key=os.path.getmtime)
    if not files:
        raise FileNotFoundError(f"no PC .vrcw in {WORLDS_DIR}")
    return files[-1]


def launch(vrcw: Path, count: int = 2, profiles: list[int] | None = None, width: int = 960, height: int = 540,
           extra: list[str] | None = None) -> list[Client]:
    """profiles: --profile per client (default 0..count-1). A profile that never logged in shows the
    QR/device login and needs the owner once; several clients may share a logged-in profile."""
    if not STEAM_EXE.exists():
        raise FileNotFoundError(STEAM_EXE)
    profiles = profiles or list(range(count))
    room = random.randint(10000, 99999)
    url = f"create?roomId={room}&hidden=true&name=BuildAndRun&url=file:///{str(vrcw).replace(os.sep, '/')}"
    clients = []
    for i in range(count):
        port = BASE_PORT + 10 * i
        prof = profiles[i % len(profiles)]
        args = [str(STEAM_EXE), f"--url={url}", "--no-vr", f"--profile={prof}",
                f"--osc={port}:127.0.0.1:{port + 1}", "--enable-debug-gui", "--enable-udon-debug-logging",
                "--skip-registry-install", "--fps=45", "-screen-fullscreen", "0",
                "-screen-width", str(width), "-screen-height", str(height)] + (extra or [])
        started = time.time()
        p = subprocess.Popen(args, cwd=str(STEAM_EXE.parent))
        clients.append(Client(index=i, pid=p.pid, profile=prof, osc_port=port, started=started))
        time.sleep(8)  # stagger: the second client must join the first one's instance
    save(clients)
    return clients


def save(clients: list[Client]) -> None:
    STATE_FILE.write_text(json.dumps([c.__dict__ for c in clients], indent=1), encoding="utf-8")


def load() -> list[Client]:
    if not STATE_FILE.exists():
        return []
    return [Client(**d) for d in json.loads(STATE_FILE.read_text(encoding="utf-8"))]


def alive(c: Client) -> bool:
    import psutil
    try:
        p = psutil.Process(c.pid)
        return p.is_running() and p.name().lower() == "vrchat.exe" and p.create_time() >= c.started - 5
    except psutil.Error:
        return False


def kill_all() -> int:
    """Terminate only the clients this module launched (pid + start time checked)."""
    import psutil
    n = 0
    for c in load():
        if alive(c):
            psutil.Process(c.pid).terminate()
            n += 1
    STATE_FILE.unlink(missing_ok=True)
    return n


def tile(clients: list[Client], width: int = 960, height: int = 560) -> None:
    for c in clients:
        c.place(c.index * width, 0, width, height)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("launch"); s.add_argument("--vrcw"); s.add_argument("--scene", default="")
    s.add_argument("-n", type=int, default=2); s.add_argument("--profiles", default="", help="comma list, e.g. 0,0")
    sub.add_parser("kill")
    sub.add_parser("status")
    s = sub.add_parser("op"); s.add_argument("client", type=int); s.add_argument("op", type=int); s.add_argument("arg", type=int, nargs="?", default=1)
    s = sub.add_parser("tp"); s.add_argument("client", type=int); s.add_argument("waypoint"); s.add_argument("--project", default=".")
    s = sub.add_parser("interact"); s.add_argument("client", type=int); s.add_argument("target"); s.add_argument("--project", default=".")
    s = sub.add_parser("walk"); s.add_argument("client", type=int); s.add_argument("seconds", type=float); s.add_argument("--forward", type=float, default=1); s.add_argument("--right", type=float, default=0)
    s = sub.add_parser("shot"); s.add_argument("client", type=int); s.add_argument("path")
    s = sub.add_parser("click"); s.add_argument("client", type=int); s.add_argument("fx", type=float); s.add_argument("fy", type=float)
    s = sub.add_parser("log"); s.add_argument("client", type=int); s.add_argument("--all", action="store_true")
    a = ap.parse_args()

    if a.cmd == "launch":
        vrcw = Path(a.vrcw) if a.vrcw else latest_vrcw(a.scene)
        cs = launch(vrcw, a.n, [int(x) for x in a.profiles.split(",")] if a.profiles else None)
        print(json.dumps([c.__dict__ for c in cs]))
        return
    if a.cmd == "kill":
        print("killed", kill_all())
        return
    cs = {c.index: c for c in load()}
    if a.cmd == "status":
        for c in cs.values():
            print(c.index, c.pid, "alive" if alive(c) else "dead", c.osc_port, c.log)
        return
    c = cs[a.client]
    if a.cmd == "op":
        c.cmd(a.op, a.arg)
    elif a.cmd == "tp":
        c.tp(int(a.waypoint) if a.waypoint.isdigit() else a.waypoint, load_manifest(a.project))
    elif a.cmd == "interact":
        c.interact(int(a.target) if a.target.isdigit() else a.target, load_manifest(a.project))
    elif a.cmd == "walk":
        c.walk(a.forward, a.seconds, a.right)
    elif a.cmd == "shot":
        print(c.screenshot(a.path))
    elif a.cmd == "click":
        c.click(a.fx, a.fy)
    elif a.cmd == "log":
        c.find_log()
        lines = c.read_new()
        print("\n".join(ln for ln in lines if a.all or "[E2E]" in ln))
    save(list(cs.values()))


if __name__ == "__main__":
    main()

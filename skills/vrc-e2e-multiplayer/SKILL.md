---
name: vrc-e2e-multiplayer
description: Autonomous multi-client tests of a VRChat world in local Build & Test clients: launch N clients, move players to waypoints, interact with world objects, open client menus (personal mirror), screenshot and read logs. Use for anything single-player ClientSim can't show (sync, other players, mirrors, ownership).
---

# Multi-client E2E tests (local Build & Test clients)

## Rules (non-negotiable)

- **Test clients only.** Only clients this kit launched on a local `.vrcw` (`--url=create?...&url=file:///...`,
  the same launch the SDK's Build & Test uses). Never touch the owner's own VRChat client, never
  join online instances with automation.
- **No client modification.** No mods, DLL injection, memory access, patched files or loaders. Everything
  here uses the unmodified client's official interfaces: OSC input, launch options, the output log,
  window screenshots and ordinary keyboard/mouse input. The world side is a test-only Udon harness.
- **The harness never ships.** `E2EHarness` is injected into the *build copy* of the scene only by
  `E2EBuild.Start()` (SessionState flag, cleared in `finally`); SDK uploads never carry it. A real
  gamepad or VR stick sends fractional axis values that the harness would read as commands.
- **Profile settings are the owner's.** Clients on profile 0 share the owner's real settings
  (registry PlayerPrefs). Change a client setting only when the test needs it, screenshot it before
  and after, and put it back before closing the clients. Never click blind in settings pages: a
  "hover" click once flipped Immersive Move.
- Only pids this kit started are killed (`vrc_e2e.py kill` checks pid + start time). OSC ports 9100+.
- The clients log into the owner's account and VRChat's servers (the "Local Test" room). Keep runs
  short and close the clients afterwards.

## Pieces

| File | Role |
|---|---|
| `.omp/templates/e2e/E2EHarness.cs.txt` | UdonSharp harness: OSC-axis command channel, waypoint teleports, `_interact` on any target, state/camera logging as `[E2E]` lines |
| `.omp/templates/e2e/E2EBuild.cs.txt` | Editor: `AWDK.E2E.E2EBuild.Start()` builds a local test `.vrcw` with the harness injected; waypoints + targets written to `<project>/E2E/manifest.json` |
| `.omp/scripts/e2e/vrc_e2e.py` | Driver + CLI: launch/tile/kill clients, OSC movement, harness commands, logs, screenshots, clicks, keys, Action Menu, personal mirror |
| `.omp/scripts/e2e/ui/*.png` | Radial-menu page templates (1578x884 client area) |
| `.omp/scripts/e2e/scenarios/personal_mirror.py` | Example scenario: personal mirror vs world camera settings |
| `.omp/scripts/e2e/scenarios/mirror_presence.py` | Is a far-away player drawn in the observer's mirror? Present/absent diff with a positive control |

## Install in a project (once)

1. Copy `E2EHarness.cs.txt` -> `Assets/AWDK/E2E/E2EHarness.cs` and `E2EBuild.cs.txt` ->
   `Assets/AWDK/E2E/Editor/E2EBuild.cs`; refresh; read the console for `error CS`.
2. Create the U# program asset `Assets/AWDK/E2E/E2EHarness.asset` (`UdonSharpProgramAsset`,
   `sourceCsScript` = the script).
3. `pip install python-osc mss` (also uses numpy, Pillow, psutil, pywin32).
4. Waypoints: `<project>/E2E/waypoints.json` `[{"name":..,"pos":[x,y,z],"yaw":deg}]`. EditorOnly
   objects (e.g. `POI_*`) are stripped before the build callback, so list test spots in the JSON.
   Raycast the floor in the editor for `y`; give players free space for menus that spawn in front.

## Run

```
# Editor (MCP): AWDK.E2E.E2EBuild.Start() (queue it with EditorApplication.delayCall: the build
# outlives the MCP timeout). Done when Status() says "OK <vrcw>" or a new *.vrcw appears in
# %LOCALAPPDATA%Low\VRChat\VRChat\Worlds (~5-7 min). With several editors open, Editor.log may
# belong to another instance; don't rely on it.
cd <project>
python ../.omp/scripts/e2e/vrc_e2e.py launch --vrcw <path> -n 2 --profiles 0,0
python ../.omp/scripts/e2e/vrc_e2e.py tp 0 S1B_MirrorB      # client 0 to a waypoint (name or index)
python ../.omp/scripts/e2e/vrc_e2e.py interact 1 <path-suffix> # press a world button as client 1
python ../.omp/scripts/e2e/vrc_e2e.py log 0                  # [E2E] lines of client 0
python ../.omp/scripts/e2e/vrc_e2e.py shot 0 out.png
python ../.omp/scripts/e2e/vrc_e2e.py kill
```
From Python: `import vrc_e2e as v; cs = v.load(); cs[0].walk(1, 2); cs[0].tp('Spawn', v.load_manifest('.'))`.
Wait for `[E2E] ready` in every client's log (~60 s) before commands; the harness logs a `state tick`
with every player's position every 2 s, which is the multiplayer assertion source.

## Harness command channel

OSC `/input/Vertical` latches an argument, `/input/Horizontal` fires an opcode on its rising edge.
The client remaps OSC movement axes through a 0.1 deadzone before Udon sees them:
`udon = (osc - 0.1) / 0.9`; the driver sends `0.1 + 0.9 * code/100` so Udon receives exactly
`code/100`. During a command the harness immobilises the player and puts them back afterwards
(non-moving ops), so commands don't drift the player.

| Op | Effect |
|---|---|
| 9 | page = arg-1 (ops 10/11 address `page*98 + arg`; the driver pages automatically) |
| 10 | teleport to waypoint |
| 11 | `SendCustomEvent("_interact")` on target (every UdonBehaviour exporting `_interact`) |
| 12 | log state now |
| 13 | list waypoints and targets |
| 14 | yaw to (arg-1)*5 deg in place |
| 15 | respawn |
| 16 | log screen + photo camera settings |
| 17 | screen camera player-layer cull distance arg m + occlusion |
| 18 | screen camera far clip arg m |
| 19 | restore screen camera settings |
| 20 | screen camera far clip arg*10 m |

Add world-specific ops in the harness copy of that project, never in the shipped scene.

## Client facts (measured 2026-11-17, client w_2026.4.1p3)

- Launching `VRChat.exe` directly (as Build & Test does) runs without Easy Anti-Cheat: the log says
  "Anti-cheat client not available. Verify that the game was started using the anti-cheat bootstrapper".
  This changes nothing about the rules above: no client modification is needed or used.
- `--profile=N` other than the owner's logged-in profile shows a QR/device login (owner needed once).
  Several clients can share profile 0; both join the same `local:` room as the same user and each
  sees the other (`OnPlayerJoined`, positions in `GetPlayers`).
- Each client writes its own `output_log_*.txt`; the driver finds it by the OSC port in the log head.
  `"OSC enabled: False"` early in the log is not authoritative; OSC input works when the profile's
  OSC setting is on.
- OSC `/input/*` works while the window is unfocused. Keyboard/mouse need focus: keys must be
  hardware scancodes (`SendInput` + `KEYEVENTF_SCANCODE`), the camera and the Action Menu radial read
  relative mouse motion. Make the driver process DPI-aware or rects and screenshots disagree.
- Desktop menus: Esc = Quick Menu (Launch Pad, Here, Camera, Audio, Settings tabs); R = Action Menu.
  Personal Mirror and Face Mirror are in Action Menu > Tools (right / down-right). The Action Menu
  reopens on the last submenu it showed: detect the page before moving (`action_menu_page()`).
- The personal mirror spawns about 1 m in front of the player and stays where it was spawned.
- Udon can't enumerate cameras (`Camera.allCameras` is not exposed). `VRCCameraSettings.ScreenCamera`
  and `.PhotoCamera` are the only camera handles (near/far, culling mask, layer cull distances,
  occlusion); the personal mirror has none.
- **The personal mirror (desktop, incl. players-only "Show World" off) follows the screen camera's
  far clip** and ignores its layer cull distances: far 4 m hid a player at 6 m and kept one at 3 m;
  a 4 m Player-layer cull distance changed nothing.
- **Players-only mirrors still draw world objects on the Player layer** (a black quad on layer 9
  showed up in a players-only personal mirror). That is how a world can hide areas from them.
- Mirror settings live only in the Main Menu: Esc -> expand (top right of the Quick Menu) ->
  Settings -> Mirrors, then scroll. Rows: Personal Mirror, Grabbable, Tracking, Opacity, Immersive
  Move, Mirror Snap, Calibration Mirror, Border, Show other users, Show World, Show UI. Re-focusing
  the client (a new driver process calls `focus()`) closes an open menu: do a whole menu path in
  one process, and screenshot every step.
- Screenshots read the screen: a locked workstation (LogonUI running) or a covered window breaks
  them (`BitBlt failed` or black frames); the user's own input moves the real cursor into the
  client. Runs need the PC to themselves.
- VR mode: menus need the controllers (the Action Menu wheel is opened and steered with the
  controller buttons and stick), so the owner opens the mirror once with the headset on; teleports,
  turns, OSC and screenshots of the desktop view work without him.

## Writing a scenario
Copy `scenarios/mirror_presence.py` or `personal_mirror.py`: load clients and manifest, teleport,
act, wait for sync (2-3 s for remote positions), assert on `[E2E] state` lines and screenshots,
write `E2E/runs/<name>_<timestamp>/` with crops and a summary. Screenshots are evidence for the
agent; judge them visually, and keep a positive control (a state where the effect must show).

Detecting a player a few pixels tall (mirror_presence.py):
- Diff the *median* of ~10 frames taken over 4 s with the subject present against the same with
  the subject absent, and mask out every pixel whose range across either set is above the noise
  threshold. A two-frame noise map misses the observer's own idle sway, fires and video screens;
  those then read as detections (it happened: three "positive controls" were the observer's sleeve).
- Park the absent subject somewhere it is visible neither directly nor in the mirror (a players-only
  mirror is see-through, so whatever is in front of the observer shows too), and never on the
  observer (collision pushes the observer and the whole frame changes).
- Turn screens off (`interact` their toggle) and keep the far subject off the observer's
  reflection: aim so the target is 15-20 deg off the mirror axis, and check that the detected spot
  matches the predicted one (x = 0.5 + 0.5 * tan(angle) / tan(hfov/2)) before trusting a count.
- Zoom crops (present | absent, same box) are what the user can judge; save them every run.

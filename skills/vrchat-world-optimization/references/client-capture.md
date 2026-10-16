# Autonomous in-client capture (Build & Test + PresentMon)

Editor play mode is one flat view with editor overhead; the VRChat client is the truth. This runs a
local Build & Test in the user's VRChat client with no human input: a test-only Udon helper
teleports the local player through fixed viewpoints, PresentMon records the client's frames, and a
parser joins the two by wall-clock time. No upload.

Files: `scripts/perf-capture/` — `PerfCaptureTour.cs` (UdonSharp, test builds only),
`Editor/PerfCaptureGuard.cs` (blocks any build containing the helper unless the runner opted in),
`Editor/PerfCaptureRunner.cs` (Install / Place / StartBuildAndTest / Status / Remove, for
`execute_code`), `capture_client.py` (waits for the client, records PresentMon, waits for the tour's
done marker, closes the client, keeps the log), `parse_capture.py` (log markers + PresentMon CSV →
per-viewpoint table and A/B delta).

## What it measures, and what not

- Client frame time per viewpoint (median, p95, p99), PresentMon `MsCPUBusy` / `MsGPUBusy`. Rank and
  A/B deltas transfer to headsets; absolute FPS does not (desktop renders ~1/2–1/3 the pixels).
- **Not** draw calls (the client shows none; keep the editor Frame Debugger numbers for those).
- Teleport sets position and yaw; the desktop view stays level. Poses are close to, not identical
  with, the editor poses; compare client runs only with client runs.

## Prerequisites (check, don't assume)

- VRChat installed, the user logged in (a login or 2FA prompt is the one step that needs the user;
  report it and stop).
- PresentMon console exe (`GameTechDev/PresentMon` release, MIT) in `%LOCALAPPDATA%\PresentMon\`.
  Unelevated capture works when the user is in **Performance Log Users**
  (`whoami /groups`); otherwise it needs elevation, which is a user step. Always pass
  `--terminate_after_timed` with `--timed`, or the process never exits. CSVs are UTF-8 with BOM.
  PresentMon 2.6 date-times were observed **2 h ahead** of local time on a UTC+2 host; the parser
  auto-corrects from the CSV's modification time (`--pm-offset-hours` to force).
- The editor is idle: no other agent mutating, no bake, no play mode. The PC is not under other
  heavy load during the runs (it skews frame times); say so in the report if it was.

## Procedure (one Build & Test per state)

1. **Install** (once per project): copy `PerfCaptureTour.cs` to `Assets/AWDK_PerfCapture/` and
   both `Editor/*.cs` to `Assets/AWDK_PerfCapture/Editor/`; refresh, wait for compile, check the
   console for `error CS`; then `return PerfCaptureRunner.Install();` (creates the U# program
   asset).
2. **Place**: `return PerfCaptureRunner.Place(json, "<state>", 30f, 6f, 20f, 1);` with
   `{"viewpoints":[{"name":"garden_west","pos":[x,y,z],"yaw":deg}, ...]}` — pos = the player's
   feet, yaw = look direction. Reuse the editor baseline viewpoints; verify each has floor under
   it. `startDelaySeconds` must cover world load and image downloads (25–40 s). Save the scene.
3. **Set the state** to measure (e.g. "originals" via the project's swap menu). Save the scene.
4. **Build & Test**: `return PerfCaptureRunner.StartBuildAndTest();` (sets 1 client, desktop,
   opens the SDK panel, allows this one build, starts it asynchronously). If it reports the
   builder is not ready, wait a few seconds and retry. Immediately start, in a shell:
   `python capture_client.py --label <state> --out-dir <evidence dir>` — it waits for
   `VRChat.exe`, records PresentMon, waits for `[AWDK_PERF] done label=<state>` in the client log,
   closes the client and copies the log. Exit 0 = complete.
5. `PerfCaptureRunner.Status()` should read `STATE=launched`; `failed` carries the SDK error.
6. Repeat 2–5 for the other state(s) (Place again with the new label).
7. **Tear down — always, also after a failure**: `return PerfCaptureRunner.Remove();`, restore
   the state the user wants to keep, save the scene, check `Status()` says
   `harnessInScene=False`. The scripts and program asset may stay; they do nothing without the
   harness. Sweep `__*__` objects as usual.
8. **Parse**: `python parse_capture.py --run originals originals_output_log.txt originals.csv
   --run merged merged_output_log.txt merged.csv --json client_ab.json`. Quote both runs'
   medians/p95 and the delta; treat deltas within ~5 % as noise unless repeated runs agree (run
   each state twice when the result matters).

## Optional: in-client draw calls with RenderDoc (owner approval required)

PresentMon gives frame times only. For exact draw calls inside the client, `renderdoc_tour.py`
injects RenderDoc into the **local Build & Test client**: it reads the SDK's launch command, closes
that client, relaunches the same command under `renderdoccmd capture`, presses F12 at each
`begin` marker, renames each capture to its viewpoint and counts `ID3D11DeviceContext::Draw*`
calls from the XML export (`--count-only DIR` re-counts). This modifies the client: run it only
when the world owner has explicitly approved it, record their words in the project's task log,
and never on a normal VRChat session. RenderDoc portable zip: renderdoc.org/builds (MIT); keep it
in `%LOCALAPPDATA%\RenderDoc\`. `qrenderdoc --python` did not exit headless in a probe; the
script uses only `renderdoccmd` and a keypress. Captured frames carry no Unity names: report draw
totals per viewpoint, and keep the editor/standalone category table for attribution.

## Upload safety

`PerfCaptureGuard` implements `IVRCSDKBuildRequestedCallback`: any world build while the harness
is in a loaded scene fails with `[AWDK_PERF] Build blocked …` unless `AllowTestBuild()` was called
for that one build. Every upload starts with a build, so a forgotten harness cannot ship. Teardown
(step 8) is still mandatory; the guard is the backstop.

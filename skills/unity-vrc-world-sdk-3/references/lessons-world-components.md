# World components lessons

Lessons on colliders and physics, audio, video and world-space UI, and SDK upload and component behaviour in VRChat worlds.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Colliders and physics

Which objects get colliders (small props none, big furniture `SolidCollider`, lie-down colliders, ramps, no MeshColliders underfoot) is policy in `.omp/AGENTS.md` "Collision, seats and pickups"; layers in `references/layers.md`. These items are how to build and prove it.

### Transforms and reading colliders correctly

- **Before debugging any collider placement, print `lossyScale` of the collider and every ancestor. Keep collider roots at position 0, identity rotation, scale 1, child `localScale = 1`, with real dimensions in `BoxCollider.size`** — PhysX can't represent a sheared box, so non-uniform parent scale plus rotation collides with a different box than the gizmo draws, with no warning. Exact 90° rotations are exempt.
- **Call `Physics.SyncTransforms()` after scripted moves before reading `Collider.bounds` or raycasting in the same call; after rebuilding a mesh, reassign `mc.sharedMesh = null; mc.sharedMesh = m;`; on inactive objects read `BoxCollider.size`** — physics only sees the move at the next step, so a correct write looks failed; edit-mode MeshColliders keep stale zero-size bounds, and inactive colliders report bounds `(0,0,0)`.
- **In a collider census check `Collider.enabled` as well as `activeInHierarchy`, and sweep for collider bounds far outside their parent's renderer bounds** — disabled blockout boxes read as live (re-enabling them puts invisible walls ~10 cm inside every room), and boxes authored in world coordinates under a scaled parent land hundreds of metres away. Close sliver gaps in mesh bars with one box or thin inner walls.

### Fitting boxes to geometry

- **Fit one `BoxCollider` per building with each side on the area-weighted 90th percentile of outward wall triangles (y 0.3–2.2 m band, +2 cm, shrink-only, cap 1 m)** — raw extents include eaves (invisible walls) and vertex percentiles land on window trim, because vertex density isn't surface area. Never one solid box on archways or gatehouses.
- **Fit a stair ramp through the tread noses: slope first→last nose, intercept `max(y − slope·z)`, end where the plane meets each landing height** — anchoring at landing edges leaves a ~0.2 m lip; the ramp floating up to one riser above treads is expected. Policy: AGENTS.md "Movement collision".
- **Measure slanted walls at fixed absolute heights and fit the plane, then build a rotated box (one per facet on pointed ends)** — probing at floor + 1 m on a stepped floor fakes a taper on a flared wall.
- **When a slab is cut for a void (stairwell, mezzanine, shaft, hatch), cut its collider the same way and prove it with a headroom raycast walk (> 2.2 m everywhere on the route)** — renderers cut around the void while one big slab box still seals it, and every screenshot looks perfect.

### Layers for player-space colliders

- **Put interactables and world-space menus on the `Walkthrough` layer (17) with their collider kept; never delete it or use `Interactive`/`Environment`** — `Interact()` and UI laser raycasts need a collider, and layers 8 and 11 block players.
- **Keep custom-layer (22–31) colliders out of player space or make them triggers; never "fix" it in the project collision matrix** — custom layers collide with players, the client ignores the project matrix, and a particle-only proxy box became an invisible ceiling that only taller avatars hit.

### Proving walkability

- **Never accept a minimal-collider pass without a downward raycast grid over every floor, counting misses and "landed on a prop" hits separately, plus outward rays at 1.2 m on all sides** — a missing floor collider is invisible in the editor and spot checks lie by hitting furniture or the storey below.
- **After any collider rework, run a `CheckCapsule` flood fill from spawn on a 0.5 m grid (3D with a 0.5 m step-up for multi-level) and diff reachable cells before/after, naming each lost cell with `OverlapCapsule`** — colliders render nothing; classify losses against new box footprints inflated by the capsule radius, and filter ground hits by name so the ceiling doesn't hide the floor.
- **Triage "invisible wall" reports by checking jump impulse first (add `PlayerModSetter`), then a grid capsule sweep that flags hits with no visible prop within ~3.5 m; read true extents as `Vector3.Scale(col.size, lossyScale)`** — VRChat's default jump is 0, so every kerb and low prop blocks on foot, and `Collider.bounds` is a world AABB that makes a thin diagonal barrier look like a huge slab.
- **Script walk routes: capsule-march polylines in edit mode (flag rises > 0.31 m, keep steps ~0.25 m), then a ClientSim `TeleportTo` tour reading `IsPlayerGrounded()` in the next call** — ClientSim won't start unless the active scene holds the scene descriptor, and same-call reads are same-frame.

## Audio, video and UI

### Video screens

- **Blit a dim idle card into the shared video RenderTexture with `VRCGraphics.Blit` on Start, stop and error, and run it by script before screenshots or reviews** — the RT is black until a stream loads (what every joiner sees), the editor never runs Start, and a bright card lights the room through emission.
- **On a freshly placed ProTV, run `ProTVBuildChecks().RunChecks(false)` in edit mode, then `CopyProxyToUdon`, mark dirty and save** — `isAVPro` ships false and play-mode checks write only the proxy, so AVPro decodes behind a standby splash; editor streaming also needs the VideoPlayerShim package, whose modal dialog blocks a headless bridge.
- **Treat `VRCUrlInputField` as a `Selectable` and set its own re-declared properties (`textComponent`, `placeholder`, …), in a World Space canvas with `GraphicRaycaster`** — casting it to `InputField` throws.

### World-space canvases

- **Convert sRGB hex palettes with `.linear` where the palette is declared, for every `Graphic` colour including runtime tints** — projects render in Linear space, so unconverted UI comes out lighter and washed out and one missed element pops.
- **Build large menus with a re-runnable edit-mode builder script that destroys, rebuilds and rewires the canvas (then `CopyProxyToUdon`), and test by `SendCustomEvent`/`SetProgramVariable` on the UdonBehaviour** — hand-nudged RectTransforms drift and are wiped next rebuild; the C# proxy does nothing in play mode.
- **Size a readout canvas to the visible screen face, align columns as two labels in one rect with equal line counts, and back every Cull Off canvas with an opaque box** — prop bounds include posts and base, space-padding doesn't align proportional fonts, and Cull Off canvases show mirrored text from behind.
- **Place capture cameras at `panel.position − panel.forward·d` looking along `forward`, or shoot both sides** — a canvas is read from its −forward side, so a +forward camera photographs the back and you debug a non-existent render bug.
- **Keep wall-mounted canvases ≥ 20 cm off the wall and non-static** — a canvas ~3 cm proud of a wall drew nothing, background included; isolate by moving it into open space.

### Audio files

- **Make ambient loops with an ffmpeg equal-power (`qsin`) tail-into-head crossfade, then one fixed gain to −1 dBFS; never limit before the crossfade** — the crossfade sums signals and can clip, and `alimiter` renormalizes unless `level=false`. Swap a wired clip by overwriting in place and keeping its `.meta`.
- **Normalize prop SFX from WAV masters into new files, fix mono-in-stereo with `pan=mono|c0=c0`, and judge channels from the file or Build & Test, not ClientSim** — MP3 downmixes are ~6 dB quieter, `-ac 1` averages in silence, ClientSim drops the right channel under `VRCSpatialAudioSource`, `AudioImporter.normalize` doesn't change loudness, and transient props above ~−26 LUFS only buy limiting.

### Particles

- **Configure the effect hierarchy first and set the root `main.playOnAwake = true` last; verify through the real toggle path without calling `Play()`/`Simulate()`** — playOnAwake acts as shared, so turning it off on a sub-emitter killed the parent.
- **Verify particle collision in play mode by counting particles in a volume they must not reach against the no-collision expectation** — edit-mode `Simulate` skips world collision and collision sub-emitters entirely.

## SDK, upload and third-party components

- **Restore the shipped state the moment a preview pass ends, make "apply shipped state" the first step of any scripted save, and check with a `git diff` grep of lightmap/probe/enabled fields** — the SDK saves the open scene on Build & Publish, so any preview that wrote serialized fields ships; check reflection-probe enabled state before lightmaps when a glossy surface looks lit by the wrong state.
- **Check a null array entry's target for the `EditorOnly` tag before re-wiring, skip `EditorOnly` objects when building arrays, and mirror the stripping in previews** — ClientSim and the build strip them, so inspector-wired arrays read null at runtime. Mechanism: `references/components.md` editor-only exclusion.
- **Install SaccFlightAndVehicles by whole-folder copy, find ground vehicles by the `SaccGroundVehicle` GUID, seat them from the four `SaccWheel` anchors, and reuse the built-in `VehicleRespawner`** — the root pivot is metres off the wheelbase and the body is skinned with inflated bounds; its seats are real `VRCStation`s, so they need an explicit user request (AGENTS.md "No seats").
- **Set clip planes from Udon (far first, then near, clamped 0.001–0.05) and size ExpSq fog to ρ ≥ 2.63 / f_eff, with the horizon and below-horizon sky equal to the fog colour** — PC depth is reversed-Z float, so a small near costs no precision, but the skybox overpaints geometry beyond f_eff ≈ n·f/(n + 5.3e-7·(f−n)). Full procedure: `.omp/skills/clip-planes/SKILL.md`.

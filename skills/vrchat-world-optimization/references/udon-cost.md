# Udon scripting cost

Some costs are not rendering at all. In a measured world, a poker table's eight per-seat player
programs cost about 1.66 ms of `BehaviourUpdate` per frame (all Udon ~3.2 ms), while the table drew
only ~17 draws. Hiding renderers does nothing for that cost.

## Measure

- Attribute with `BehaviourUpdate` ms in the sweep: disable one system's `UdonBehaviour`s in play
  mode (diagnostic only, reverts on exit), re-sample, then drill down to the program type.
- Read the program's `Update` / `LateUpdate` / `PostLateUpdate` / `FixedUpdate` bodies: what runs
  every frame when nobody is using it.

## Fix without breaking networking

- **Never deactivate a synced object to save cost.** Inactive objects stop receiving and sending
  sync; far players miss state, late joiners break.
- **Gate the per-frame work, keep the object alive**: early-return from the update loop when the
  local player is beyond a distance (check it a few times per second, not every frame) or when
  the system is idle (no seated players, no game running). The project-local pattern is a small
  proximity gate component that toggles a flag, like a ripple-camera gate that runs a camera only
  within 15–20 m.
- Third-party packages: the edit is a local modification. Record it in the project's `AGENTS.md`,
  because a package update overwrites it.
- Prove it: play-mode test of the whole feature (join, play, leave, late join, ownership transfer),
  then the `BehaviourUpdate` delta near and far.

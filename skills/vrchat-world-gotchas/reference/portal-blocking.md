# Historical portal-blocking workarounds

Archived implementation evidence from a December 2021 guide, not a
current supported API contract or a runtime-verified recipe.

**Start with the supported option:** current VRC Scene Descriptor documentation
documents **Forbid User Portals** for portals opened from the world menu. Do not infer
broader coverage. See [the refresh](hai-guides-refresh.md) before considering the
historical alternatives below; changing respawn transforms can also affect real spawning.

## Approach 1 — move a Respawn point (no portal handling)

Haï reports using Udon to move a Respawn point in front of the player, causing VRChat to
refuse portal drops with **"Portal too close to spawn"**. The source attributes this
technique to *JSR Festival*. No portal detection or per-frame overlap query is required
by this approach, but present-client behavior and spawning side effects must be checked.

## Approach 2 — detect and relocate the portal

Handles observed by the 2021 implementation, not guaranteed public interfaces:

- Portals on the **Water layer — layer 4** (`1 << 4` as a mask).
- A GameObject name containing **`PortalInternalDynamic`**.

Source-reported caveats, not independently reproduced here:

- **Move the portal, don't destroy it.** Destroying it may leave the system menu unable to
  close after the player opens the portal menu.
- The author reports an unexplained next-update `Physics.OverlapBoxNonAlloc` crash after
  moving a portal, mitigated by reallocating the collider buffer. This does not establish
  a universal requirement to reallocate in current clients.
- The sample handles only the first portal each tick, assuming others can wait. That
  assumption is not a guarantee that simultaneous portal spawns cannot occur.

The source attributes this implementation to *VRWare*.

### Historical source script (not compiled or tested against current SDK)

```csharp
using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class RemoveSpawnedPortals : UdonSharpBehaviour
{
    private Vector3 _halfExtents;
    private Collider[] _buffer;
    private int _waterLayerMask;

    private void Start()
    {
        _halfExtents = Vector3.one * 15;
        _buffer = new Collider[32];
        _waterLayerMask = 1 << 4; // 4 is the Water layer, where portals are spawned
    }

    private void Update()
    {
        // This technique was documented several times on Prefabs Discord:
        // Detect objects called "PortalInternalDynamic" in the Water layer using the Physics.OverlapBox function.
        var size = Physics.OverlapBoxNonAlloc(transform.position, _halfExtents, _buffer, Quaternion.identity, _waterLayerMask);
        for (var i = 0; i < size; i++)
        {
            var that = _buffer[i];
            var itIsValid = Utilities.IsValid(that)
                          && Utilities.IsValid(that.gameObject);
            if (itIsValid)
            {
                var thatIsAPortal = that.gameObject.name.Contains("PortalInternalDynamic");
                if (thatIsAPortal)
                {
                    // Don't destroy the portal, move it somewhere else
                    that.gameObject.transform.position = that.gameObject.transform.position + Vector3.up * 20;

                    // For some unknown reason I have not investigated, the behaviour crashes in OverlapBoxNonAlloc on next update, so recreate the buffer.
                    _buffer = new Collider[32];

                    // Only stop at the first portal detected on this tick, which should be reasonable
                    // Spawning 2 portals on the same tick might never occur, and even if it did, it would be handled next tick
                    return;
                }
            }
        }
    }
}
```

### Notes if adapting this

- `_halfExtents = Vector3.one * 15` gives a 30 m cube centred on the behaviour's transform.
  Place the object at the spawn area, or scale/duplicate to cover wherever portals must be
  blocked. It is not a whole-world sweep.
- It runs an `OverlapBoxNonAlloc` **every frame**. On a busy world consider throttling it,
  but keep in mind a portal only needs a frame or two to become usable.
- Buffer size 32 is a per-tick cap on colliders considered; a crowded Water layer could
  push the portal out of the results.
- Verify the layer name→index mapping in the project before hardcoding `1 << 4` — the
  Water layer is index 4 in a default Unity/VRChat layout, but check
  `LayerMask.NameToLayer("Water")`.

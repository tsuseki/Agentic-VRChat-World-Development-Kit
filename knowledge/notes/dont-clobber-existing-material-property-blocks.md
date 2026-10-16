---
title: Do not clear a MaterialPropertyBlock another system owns
topic: materials-textures-shaders
tags: [MaterialPropertyBlock, SetPropertyBlock, HasPropertyBlock, state toggle, QvPen, Udon]
summary: Restoring with SetPropertyBlock(null) clears the block rather than restoring it; check HasPropertyBlock() in the base state before adding a renderer to a toggle list.
---
**Symptom:** A state toggle (e.g. a lights-out dim mode) applies `MaterialPropertyBlock`s and restores with `r.SetPropertyBlock(null)`. After toggling back, unrelated objects lose their state: for example QvPen pen/eraser meshes, which store each pen's colour in a property block, would lose their colours.

**Cause:** `SetPropertyBlock(null)` does not restore, it **clears**. If another (vendored) system already owned a block on that renderer, the "restore" destroys its state. The damage lands in the state you are not testing.

**Fix / rule:** Guard the wiring:

```csharp
if (r.HasPropertyBlock()) { /* skip: someone else owns this renderer */ }
```

Run the check in the **base state**, before your own pass has applied anything; afterwards every renderer in your list reports `true`. If you really need a renderer that already has a block, read the existing block, add your properties, and restore by re-applying the *captured* block rather than `null`. For a small prop, leaving it out is usually the better trade.

Related: [setpropertyblock-replaces-not-merges](setpropertyblock-replaces-not-merges.md), [removing-a-renderer-from-a-toggle-list-leaks-state](removing-a-renderer-from-a-toggle-list-leaks-state.md)

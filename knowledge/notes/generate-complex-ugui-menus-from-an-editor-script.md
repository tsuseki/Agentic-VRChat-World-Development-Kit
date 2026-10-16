---
title: Generate large UGUI menus from an editor builder script, and test them by SendCustomEvent
topic: audio-video-ui
tags: [UGUI, menu, editor script, builder, ClientSim, UdonSharp, testing]
summary: A 300-object menu hand-edited in the Inspector drifts from its mockup; a re-runnable builder that destroys and rebuilds the canvas and rewires references keeps it exact.
---
**When:** a menu with many tabs/rows (e.g. 11 tabs, ~300 objects).

**How:**
- An editor script (menu item "Rebuild Menu") destroys the canvas, rebuilds it, rewires every reference on the controlling UdonSharpBehaviour, and calls `CopyProxyToUdon`. Change layout in the script, never by nudging RectTransforms (they are wiped next rebuild). Rebuild in **edit mode** and save the scene after. Invokable headlessly via `Type.GetType("<Builder>, Assembly-CSharp-Editor")`.
- Keep parallel arrays (tab constants, buttons, labels, panels, `ShowTabN` targets) together; adding a tab touches all of them.
- Reserve one accent colour pair for the single call-to-action; reusing it for ordinary rows makes a whole tab look like a commit button.
- In linear colour space, linearise the UI palette.

**Testing in ClientSim:**
- Drive the menu with `SendCustomEvent` on the UdonBehaviour (find via `GetComponents<UdonBehaviour>()` and match `programSource.name`).
- Set U# state with `SetProgramVariable("money", 700f)` on the UdonBehaviour; the C# proxy field does nothing in play mode.
- ClientSim's own pause menu overlays captures — invoke its close button by exact label/path, or a fuzzy search also fires your own menu's buttons.
Related: [ugui-colors-need-linear-conversion](ugui-colors-need-linear-conversion.md), [drive-udonsharp-in-play-mode-through-the-udonbehaviour](drive-udonsharp-in-play-mode-through-the-udonbehaviour.md).

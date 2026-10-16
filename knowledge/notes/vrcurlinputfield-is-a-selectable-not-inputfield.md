---
title: VRCUrlInputField derives from Selectable, not InputField
topic: audio-video-ui
tags: [VRCUrlInputField, ugui, url-input, video-player, world-space-canvas, reflection]
summary: VRC.SDK3.Components.VRCUrlInputField inherits UnityEngine.UI.Selectable, so casting it to InputField throws; set its own re-declared properties instead.
---
**Symptom:** `(InputField)go.AddComponent(urlFieldType)` throws `InvalidCastException`.

**Cause:** `VRC.SDK3.Components.VRCUrlInputField` (assembly VRCSDK3) inherits `UnityEngine.UI.Selectable`, not `InputField`. It re-declares its own `textComponent` (`Text`), `placeholder` (`Graphic`), `lineType`, `contentType`, `characterLimit`, plus `GetUrl()` / `SetUrl()` returning `VRCUrl`. `targetGraphic` comes from `Selectable`.

**Fix / rule:** set those properties directly (reflection works from an editor script). A world-space URL field needs: a WorldSpace `Canvas` + `CanvasScaler` + `GraphicRaycaster`, an `Image` background, and child `Text` objects for the value and the placeholder.

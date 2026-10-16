---
title: Blit an idle card into the video RenderTexture or every screen is a black hole
topic: audio-video-ui
tags: [video player, rendertexture, VRCGraphics.Blit, udonsharp, screens, npot]
summary: A shared video RenderTexture is black until a stream loads — the state every joining player sees; blit a dim idle image on Start, stop and error.
---
**Symptom:** All video screens are pure black rectangles until someone loads a URL. No error; in a night scene it looks plausible and survives screenshots.
**Fix / rule:**
```csharp
public void ShowIdle()
{
    if (idleImage == null || feedTexture == null) return;
    VRCGraphics.Blit(idleImage, feedTexture);   // VRC.SDKBase.VRCGraphics; Graphics.Blit is not Udon-exposed
}
```
Call on `Start`, on stop and on video error.
**Pitfalls:**
- The editor never runs `Start`; run the same blit by script before screenshots or reviews, or reviewers report black screens.
- Keep the card dim: if the screen maps the RT to emission, the card's brightness lights the room.
- A 1280×720 card ships uncompressed; `npotScale = ToNearest` (→ 1024×512, DXT1 + mips) — Blit rescales to the RT anyway.

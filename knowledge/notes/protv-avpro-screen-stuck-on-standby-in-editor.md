---
title: ProTV screen stuck on standby in editor play mode until build checks run in edit mode
topic: audio-video-ui
tags: [protv, avpro, video-player, udonsharp, CopyProxyToUdon, clientsim]
summary: A freshly placed ProTV prefab ships isAVPro false, and the build checks that set it run too late in play mode, so AVPro streams decode but the screen shows the standby image until the checks are run in edit mode and copied to Udon.
---
**Symptom (ProTV 3.0 beta):** In editor play mode the stream decodes (AVPro playing, TV state PLAYING) but the screen stays on the standby splash. Every runtime metric looks healthy except the blit source.

**Cause:** `VPManager.isAVPro` is a private serialized field shipped as false in ProTV prefabs. ProTV's build checks set it via `manager.IsAVPro = true`, but in play mode they fire from `[RuntimeInitializeOnLoadMethod(AfterSceneLoad)]` - after UdonSharp already copied proxies to the Udon heap. The write lands on the proxy only, the heap keeps false, and `GetVideoTexture` reads the empty property-block path. The play-mode write is discarded on exit, so it never self-heals. Normally it persists on the first VRC SDK Build (`OnBuildRequested` runs the checks in edit mode).

**Fix / rule:** In **edit** mode run `new ArchiTech.ProTV.Editor.ProTVBuildChecks().RunChecks(false)` (public; also populates speakers/materials), then `UdonSharpEditorUtility.CopyProxyToUdon` on the ProTV UdonSharp behaviours, mark the scene dirty and save.

**Verify:** `ub.publicVariables.TryGetVariableValue("isAVPro", ...)` is true on the AVPro (Best/Compat) managers and false on the Unity video manager.

**Pitfalls:** Editor stream testing also requires the VideoPlayerShim VPM package (`dev.architech.videoplayershim`, repo vpm.techanon.dev). Its import handler pops a modal "AVPro Trial Importer" dialog that blocks a headless MCP bridge until clicked, then imports the AVPro Trial into `Assets/AVProVideo/` (trial watermark on video is expected).

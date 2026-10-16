---
title: Read image aspect from the file on disk, not from the imported Texture2D
topic: materials-textures-shaders
tags: [texture import, NPOT, aspect ratio, picture frames, artwork]
summary: Texture2D width/height are post-import (NPOT scaling, max-size clamp), so sizing frames from them stretches non-power-of-two images.
---
**Symptom:** Hung pictures look squashed/stretched.
**Cause:** The default importer scales NPOT to nearest power of two and clamps max size: 957×364 (AR 2.63) imports as 1024×512 (AR 2.00); 990×1107 as 1024×1024.
**Fix / rule:** Read true dimensions from the source file (e.g. PIL `Image.open(p).size`) and scale the frame from that aspect. If the frame mesh has a fixed picture area (e.g. exactly 16:9), apply the aspect via non-uniform scale on the instance.
**Verify:** Compare each placed picture's world aspect against the source pixel aspect; assert 0.00% error.

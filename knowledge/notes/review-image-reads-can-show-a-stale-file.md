---
title: Re-read a regenerated image under a new file name
topic: agent-workflow-verification
tags: [image viewer, cache, verification, renders, read tool]
summary: Reading an image that was regenerated at the same path can show the old picture, so copy it to a new file name before viewing, and retry once if the first read of the copy fails.
---

**Symptom.** After re-rendering a thumbnail or a prop render to the same path, reading it showed the previous version; the change seemed not to have happened.

**Cause.** Not confirmed. The behaviour matches a cache keyed by file path in the agent's image reader.

**Fix / rule.** Copy every regenerated image to a new file name (a round or time suffix) before viewing it. The first read right after the copy sometimes fails; retry once.

**Verify.** Compare the file's hash or modification time with what you just wrote, and view the copy.

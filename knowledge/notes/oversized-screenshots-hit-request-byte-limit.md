---
title: Large PNG screenshots break agent requests with HTTP 413
topic: agent-workflow-verification
tags: [screenshots, png, jpeg, 413, payload, review]
summary: 413 request_too_large is a byte limit, not a token limit; re-encode screenshots as JPEG instead of compacting context.
---
**Symptom:** An agent that takes Editor screenshots fails with `HTTP 413 request_too_large`, even
though token usage looks low.

**Cause:** The limit is on request **bytes**. A 1600×900 PNG can be ~3.5 MB once base64-encoded
while counting as few tokens. Context compaction does not help.

**Fix / rule:** Capture or re-encode screenshots as progressive JPEG (measured 3.5 MB → 0.37 MB at
full resolution with Pillow, quality ~85), or cap the long edge (~1600 px). Keep review
screenshots on disk and attach only the ones being discussed.

**Verify:** Check the encoded size of each attached image before sending.

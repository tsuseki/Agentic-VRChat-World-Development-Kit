---
title: When current state and a before-shot disagree, prove which one is right before "fixing"
topic: agent-workflow-verification
tags: [regression, baseline, screenshot diff, git, md5, reflection probe]
summary: An in-session before-shot can be the contaminated one; prove the current state against version control and asset hashes, then reproduce the baseline by re-introducing the suspected contaminant.
---
**Symptom:** A fresh capture differs from your own earlier before-shot on ~45% of pixels. A control (two captures of the same state) differs by 0 px, so the delta is real and persistent — it looks like a regression.

**Cause:** The **baseline** was captured mid-restore with a night reflection probe still enabled. The current state was correct. Because you took the before-shot yourself it feels authoritative, and the instinct is to re-break the correct scene until it matches.

**Fix / rule:**
1. Prove every *input* against version control: `git checkout` drifted materials, `git diff` the scene for `m_LightmapIndex` / `m_LightProbeUsage` / RenderSettings drift, and md5 every lightmap `.hdr` and probe asset against a backup. Lightmap output folders are often gitignored, so git alone cannot tell you — hash against a backup.
2. Confirm the diagnosis positively: re-enable the suspected contaminant and watch the metric move toward the baseline (here: diff 45.2% → 21.6%, blue channel back toward the baseline value). A suspect that moves nothing is cleared.

Version control and byte-identical hashes beat any screenshot.

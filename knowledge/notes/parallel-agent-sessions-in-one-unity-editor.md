---
title: Another agent session may be editing the same open Unity project
topic: agent-workflow-verification
tags: [multi-agent, concurrency, unity-editor, bake, git, ownership]
summary: When several AI sessions drive the same open Unity editor, objects can change or vanish mid-session, and a long bake snapshots a scene another session is rebuilding; re-verify ownership and state before acting.
---
**Symptom:** Objects you created vanish or change; unfamiliar objects and imports appear; a finished long bake describes geometry that no longer matches the live scene; your fixes on renderers are reverted and your materials orphaned.

**Cause:** A parallel agent session worked in the same editor. A lightmapper snapshots the scene at bake start, so a 25-minute bake finished stale on arrival after the other session rebuilt the objects it was meant to verify.

**Fix / rule:**
- Before modifying or deleting scene objects, re-query the hierarchy and verify the object is yours (e.g. check its mesh asset path). Don't delete or "fix" unfamiliar objects - they may be someone else's live work. Surface conflicts to the user.
- Before acting on the result of any long Unity operation (bake, import, batch edit), re-verify the objects it covered still match what you built - don't go straight from "bake finished" to "measure and review".
- If another session has taken over an object: stop editing it, don't re-impose your version, don't start another bake or a review of a world mid-build. Their version may be better.

**Detection that worked, in order:** query the object's child names and materials; `git log` for commits you didn't make; compare mtimes of `Assets/**/*.mat` against the scene file; list files modified in the last few minutes to see what the other session is writing right now.

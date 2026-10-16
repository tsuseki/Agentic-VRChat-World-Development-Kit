---
title: In-world number readouts follow each player's locale; format floats manually in Udon
topic: udonsharp-networking
tags: [Udon, string.Format, locale, decimal separator, scoreboard, timer]
summary: Udon runs on each client under that player's culture, so formatted floats show '3:02,412' for some players; convert to integers and join with a literal '.'.
---
**Symptom:** A lap-time board formatted with `string.Format("{0}:{1:00.000}", m, r)` renders `3:02,412` for some players and `3:02.412` for others, from the same synced float.

**Cause:** .NET culture-sensitive formatting follows the OS locale, and Udon runs on each player's client under their culture. Udon exposes no `CultureInfo.InvariantCulture` to pass.

**Fix / rule:** Never hand a float to a formatter for display. Convert to whole units as an `int` (e.g. milliseconds), split with `/` and `%`, and concatenate the parts with a literal `"."`. Applies to any in-world readout of a time, distance, price or score.

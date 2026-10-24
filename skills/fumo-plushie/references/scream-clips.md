# Scream clips

CC0 candidates that were trimmed and tried. Download, prepare, put them in one folder of the world
(e.g. `Assets/<World>/Audio/FumoScreams/`) with a `CREDITS.txt` (source, author, licence per file),
and let the user pick. Swapping later is one field on `FumoScreamSettings`.

| Clip | Length | Source (all CC0) |
|---|---|---|
| Wilhelm scream | 1.35 s | <https://commons.wikimedia.org/wiki/File:Wilhelm_Scream.ogg> |
| High shrill scream | 2.5 s | <https://freesound.org/people/DigitalDominic/sounds/175385/> |
| Horror jumpscare scream | 2.4 s | <https://freesound.org/people/Breviceps/sounds/587354/> |
| Clean female scream | 1.1 s | <https://opengameart.org/content/female-scream-1> |
| Short girly shriek | 0.7 s | <https://opengameart.org/content/girly-scream> (CC0 among other licences) |
| Wobbling "aaee" scream | 2.95 s | <https://freesound.org/people/RutgerMuller/sounds/104036/> |
| Plush squeak + high scream | 1.8 s | squeak <https://freesound.org/people/Breviceps/sounds/444494/> + scream <https://opengameart.org/content/female-high-pitched-scream-sfx> |

Re-check each page's licence before downloading; Freesound "hq" previews need no login.

## Preparation (any audio tool, e.g. ffmpeg)

- Trim to the scream, fade in 8 ms / out 80 ms, high-pass 60 Hz.
- Loudness-normalise to −18 LUFS, true peak −2 dB; mono; Ogg Vorbis.
- Unity import (`FumoScreamBuilder.ImportClips`): force mono, Vorbis quality 0.7, Compressed In
  Memory, preload.

```
ffmpeg -i raw.ogg -ss <start> -t <len> -af "highpass=f=60,afade=t=in:d=0.008,areverse,afade=t=in:d=0.08,areverse,loudnorm=I=-18:TP=-2" -ac 1 -c:a libvorbis -q:a 5 FumoScream_01.ogg
```

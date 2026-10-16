---
title: Make seamless ambient audio loops with ffmpeg only
topic: audio-video-ui
tags: [audio, loop, ffmpeg, crossfade, ambience, freesound, cc0]
summary: Fold the tail into the head with an equal-power (qsin) crossfade, then apply one fixed gain to −1 dBFS; never limit before the crossfade.
sources: [https://freesound.org/]
---
**How** (TRIM = BODY + XF, e.g. BODY=210, XF=6, TRIM=216):
```
ffmpeg -y -i src -filter_complex \
"[0:a]atrim=0:TRIM,asetpts=N,aformat=channel_layouts=mono,asplit=2[a][b];\
[a]atrim=start=BODY,asetpts=N[tail];\
[b]atrim=end=BODY,asetpts=N[body];\
[tail][body]acrossfade=d=XF:c1=qsin:c2=qsin[out]" \
 -map "[out]" -ar 44100 -ac 1 -c:a pcm_s16le loop_raw.wav
maxdb=$(ffmpeg -i loop_raw.wav -af volumedetect -f null - 2>&1 | grep -oE 'max_volume: [-0-9.]+' | grep -oE '[-0-9.]+$')
gain=$(awk -v m="$maxdb" 'BEGIN{printf "%.2f", -1.0 - m}')
ffmpeg -y -i loop_raw.wav -af "volume=${gain}dB" out.wav
```
Seamless because output start = s[BODY] and output end ≈ s[BODY⁻] (contiguous in source). `qsin` is constant-power — right for noise-like ambience; linear `tri` dips on uncorrelated signal.
**Pitfalls:**
- `alimiter` has `level=true` by default and renormalizes to 0 dBFS; set `level=false` if used.
- Never limit before `acrossfade`: the crossfade sums two signals and can clip. Normalize after.
- To swap a clip already wired into the world, overwrite the audio file in place with the same format (e.g. mono 44.1 kHz) and keep its `.meta` so the GUID and references survive; then refresh assets.
**Sourcing:** Freesound HQ preview MP3s are public (`https://cdn.freesound.org/previews/<first3>/<id>_<user>-hq.mp3`; get the exact URL from the sound page); filter `license:"Creative Commons 0"`. Pixabay audio is gated behind a JS session.

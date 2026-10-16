---
title: Normalize prop SFX loudness from the WAV masters; fix mono-in-stereo files with pan, not downmix
topic: audio-video-ui
tags: [audio, LUFS, loudness, ffmpeg, stereo, AudioImporter, normalize, ClientSim]
summary: Source the louder WAV masters (MP3 downmixes were ~6 dB quieter), fix silent right channels with pan=mono|c0=c0, judge channels from the file not ClientSim, and expect pure limiting above about −26 LUFS on transient props.
sources: [https://feedback.vrchat.com/sdk-bug-reports/p/stereo-audio-missing-a-channel-in-clientsim]
---
**Symptom:** prop sounds in a scene span a 23 dB range (−20 to −43 LUFS, scene average −30.8 LUFS) at identical AudioSource volume; one clip sounds half-dead in stereo.

**Rules:**
- **Dead channel:** a mono recording in a stereo container (ch1 peak −7.9 dB, ch2 −113.9 dB) imports as `ch=2` and stays one-sided. Fix with ffmpeg `pan=mono|c0=c0` (take the live channel). Never `-ac 1` — it averages in the silence and costs ~6 dB.
- **ClientSim drops the right channel** of a stereo clip whose AudioSource has a `VRCSpatialAudioSource` (Canny report, 2026-10-12); the VRChat client plays both. Diagnose dead channels from the file (ffmpeg per-channel peaks) or in Build & Test, never by ear in ClientSim — it makes every stereo clip sound one-sided.
- **Masters vs downmixes:** asset packs may ship 96 kHz stereo `.wav` masters alongside `.mp3` versions that are uncompensated `(L+R)/2` downmixes ~6 dB quieter. Process from the `.wav`.
- **Transient props have no headroom** (peak ≈ −1 dBTP at −30 LUFS): any loudness gain is pure limiting. −22 LUFS cost LRA 4.7 → 2.4; −26 LUFS kept LRA 3.5. A compressor stage before the limiter bought nothing.
- Noise floors on good recordings allow big gains (+21 to +26 dB still floored at −62 to −81 dB).
- **AudioImporter `normalize` is inert for loudness**: in-engine `AudioClip.GetData()` peak matched the file's true peak. File loudness maps directly to playback loudness — process the file.
- Write processed clips as new files (e.g. `_loud.wav`, mono, Vorbis q1.0), copy the original import settings, repoint the AudioSources, keep originals untouched.

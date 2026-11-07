#!/bin/bash
# Convert soundtrack files (mp3, wav, flac, m4a...) into what src/CrawlFurther.Core/UI/ModMusic.cs loads: Ogg Vorbis, 44.1 kHz stereo,
# leading silence trimmed, loudness normalised (two-pass EBU R128 loudnorm) so the tracks sit next to the game's music.
#
#   tools/music_convert.sh further_down.mp3 tallow_hymn.mp3 gilded_rot.mp3     # -> music/further_down.ogg ...
#   tools/music_convert.sh ~/Downloads/*.mp3
#   LUFS=-16 tools/music_convert.sh track.mp3                                   # another loudness target
#
# Target: -14 LUFS integrated, -1.5 dBTP peak ceiling. The vanilla tracks could not be measured here (they are FMOD
# FSB5 banks inside the asset files and no FSB decoder is available), so -14 is the common game/streaming level; if the
# new tracks feel loud next to Crawl's own, lower LUFS or set CustomMusicVolume in BepInEx/config/CrawlFurther.UI.cfg.
# Output names: the input's base name, lower-cased, spaces -> underscores. Re-run validate.py afterwards (music check).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${OUT:-$ROOT/music}
LUFS=${LUFS:--14}
TP=${TP:--1.5}
LRA=${LRA:-11}
command -v ffmpeg >/dev/null || { echo "ffmpeg not found: install ffmpeg first"; exit 1; }
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libvorbis || { echo "this ffmpeg has no libvorbis encoder"; exit 1; }
[ $# -gt 0 ] || { echo "usage: $0 track.mp3 [more...]"; exit 1; }
mkdir -p "$OUT"
# leading silence: drop everything quieter than -50 dB before the music starts (keeps the first 0.05 s of attack)
TRIM="silenceremove=start_periods=1:start_duration=0.05:start_threshold=-50dB:detection=peak"
for IN in "$@"; do
  [ -f "$IN" ] || { echo "skip: $IN (not a file)"; continue; }
  base=$(basename "$IN"); base=${base%.*}; base=$(echo "$base" | tr '[:upper:] ' '[:lower:]_')
  DST="$OUT/$base.ogg"
  # pass 1: measure (after the trim, so the silence doesn't count)
  JSON=$(ffmpeg -hide_banner -nostats -i "$IN" -af "$TRIM,loudnorm=I=$LUFS:TP=$TP:LRA=$LRA:print_format=json" -f null - 2>&1 \
         | sed -n '/^{/,/^}/p')
  read -r MI MTP MLRA MTH OFF < <(python3 -c "import json,sys;d=json.loads(sys.stdin.read());print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])" <<< "$JSON")
  # pass 2: apply with the measured values (linear normalisation where possible: no pumping)
  ffmpeg -hide_banner -loglevel error -y -i "$IN" \
    -af "$TRIM,loudnorm=I=$LUFS:TP=$TP:LRA=$LRA:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$OFF:linear=true,aresample=44100" \
    -ar 44100 -ac 2 -c:a libvorbis -q:a 6 -map_metadata -1 "$DST"
  # report what came out
  R=$(ffmpeg -hide_banner -nostats -i "$DST" -af "loudnorm=I=$LUFS:TP=$TP:LRA=$LRA:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p' \
      | python3 -c "import json,sys;d=json.loads(sys.stdin.read());print('%s LUFS, peak %s dBTP' % (d['input_i'], d['input_tp']))")
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$DST")
  printf '%s -> %s  (%.0f s, was %s LUFS; now %s)\n' "$(basename "$IN")" "$DST" "$DUR" "$MI" "$R"
done

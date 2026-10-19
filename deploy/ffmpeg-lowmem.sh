#!/usr/bin/env bash
# ffmpeg wrapper (set as IMAGEIO_FFMPEG_EXE) that makes libx264 encodes use a lighter preset.
# mpt always encodes with x264's default "medium"; on one CPU a 30s 1080x1920 video takes
# ~160s and ~940MB, "veryfast" ~100s and ~740MB, "ultrafast" ~60s and ~540MB.
real="${FFMPEG_REAL:?FFMPEG_REAL must point to the real ffmpeg binary}"
preset="${X264_PRESET:-veryfast}"

args=("$@")
encodes_x264=0
has_preset=0
for i in "${!args[@]}"; do
  case "${args[i]}" in
    libx264) encodes_x264=1 ;;
    -preset) has_preset=1; args[i + 1]="$preset" ;;
  esac
done

if [ "$encodes_x264" = 1 ] && [ "$has_preset" = 0 ] && [ "${#args[@]}" -gt 0 ]; then
  # The output file is the last argument; options must come before it
  last=$((${#args[@]} - 1))
  args=("${args[@]:0:last}" -preset "$preset" "${args[last]}")
fi

exec "$real" "${args[@]}"

#!/usr/bin/env bash
# Low-frequency progress logger for a chunked download.
#
# Usage:
#   setsid nohup bash scripts/download_watch.sh \
#     CHUNK_DIR TOTAL_MB [INTERVAL_SECONDS] [LOG_FILE] \
#     >/tmp/download-watch.log 2>&1 &

set -u

CHUNKS=${1:?usage: download_watch.sh CHUNK_DIR TOTAL_MB [INTERVAL] [LOG]}
TOTAL_MB=${2:?usage: download_watch.sh CHUNK_DIR TOTAL_MB [INTERVAL] [LOG]}
INTERVAL=${3:-900}
LOG=${4:-"${CHUNKS%/}/download_watch.log"}

mkdir -p "$(dirname "$LOG")"
prev=$(du -sm "$CHUNKS" 2>/dev/null | cut -f1)
prev=${prev:-0}
t0=$(date +%s)
printf '# watch start %s total=%sMB interval=%ss\n' \
  "$(date '+%F %T')" "$TOTAL_MB" "$INTERVAL" >> "$LOG"

while true; do
  sleep "$INTERVAL"
  now=$(du -sm "$CHUNKS" 2>/dev/null | cut -f1)
  now=${now:-0}
  ts=$(date +%s)
  dt=$((ts - t0))
  [ "$dt" -lt 1 ] && dt=1
  rate=$(awk -v d="$((now - prev))" -v t="$dt" \
    'BEGIN { printf "%.2f", d/t }')
  done_mb=$(du -sm "${CHUNKS%/}_assembled" 2>/dev/null | cut -f1)
  done_mb=${done_mb:-0}
  eta=$(awk -v r="$rate" -v left="$((TOTAL_MB - now))" \
    'BEGIN { if (r > 0.01) printf "%.1fh", left/r/3600; else print "n/a" }')
  curls=$(pgrep -c -x curl 2>/dev/null || true)
  printf '%s  chunks=%sMB  rate=%sMB/s  assembled=%sMB  curls=%s  ETA~%s\n' \
    "$(date '+%F %T')" "$now" "$rate" "$done_mb" "$curls" "$eta" >> "$LOG"
  prev=$now
  t0=$ts
done

#!/usr/bin/env bash
# Parallel byte-range downloader for one big file behind a flaky/slow link.
#
# Why: aria2 caps --max-connection-per-server at 16, and this network scales with
# parallelism (measured 2026-10-05: 1 conn 0.2 MB/s, 16 conn 2.5 MB/s, 32 conn
# 4.2 MB/s, 64 conn 5.8 MB/s through the AutoDL academic proxy). So: split the
# object into N ranges and drive them with M concurrent curl writers.
#
# Resumable: each part keeps its bytes in a file; a re-run continues where it
# stopped. Safe to interrupt at any time.
#
# Usage:
#   bash tools/parallel_range_download.sh <url> <out_dir> <total_bytes> [parts] [concurrency]
set -u

URL="$1"; OUT_DIR="$2"; SIZE="$3"; PARTS="${4:-64}"; CONC="${5:-48}"
mkdir -p "$OUT_DIR"

fetch_one() {
  local i="$1" s="$2" e="$3"
  local f="$OUT_DIR/part_$(printf '%03d' "$i").bin"
  local want=$(( e - s + 1 ))
  local have=0
  [ -f "$f" ] && have=$(stat -c%s "$f")
  if [ "$have" -gt "$want" ]; then
    echo "part $i overrun: $have > $want (server may ignore Range)" >&2
    return 1
  fi
  # 单次请求的墙钟上限：太长会让"卡住的连接"把整个分块拖到一小时（2026-10-13 实测：
  # 192 分块里 2 块挂死 → 整份停摆）。默认 180s，可用 CURL_MAX_TIME 覆盖。
  local _maxt="${CURL_MAX_TIME:-180}"
  while [ "$have" -lt "$want" ]; do
    curl -s --max-time "$_maxt" --connect-timeout 20 \
         -r "$(( s + have ))-$e" -o - "$URL" >> "$f" || true
    local new; new=$(stat -c%s "$f" 2>/dev/null || echo "$have")
    if [ "$new" -gt "$want" ]; then
      echo "part $i overrun: $new > $want (server may ignore Range)" >&2
      return 1
    fi
    if [ "$new" -le "$have" ]; then sleep 10; else have="$new"; fi
  done
  echo "part $i done ($have bytes)"
}
export -f fetch_one
export URL OUT_DIR

: > "$OUT_DIR/todo.txt"
for i in $(seq 0 $(( PARTS - 1 ))); do
  s=$(( i * SIZE / PARTS )); e=$(( (i + 1) * SIZE / PARTS - 1 ))
  f="$OUT_DIR/part_$(printf '%03d' "$i").bin"
  have=0; [ -f "$f" ] && have=$(stat -c%s "$f")
  [ "$have" -ge $(( e - s + 1 )) ] && continue
  echo "$i $s $e" >> "$OUT_DIR/todo.txt"
done

echo "[dl] $(wc -l < "$OUT_DIR/todo.txt") parts to fetch (of $PARTS), concurrency=$CONC"
xargs -a "$OUT_DIR/todo.txt" -n3 -P "$CONC" bash -c 'fetch_one "$@"' _ || {
  echo "[dl] one or more ranges failed; inspect todo.txt and part sizes" >&2
  exit 1
}
echo "[dl] all parts complete"

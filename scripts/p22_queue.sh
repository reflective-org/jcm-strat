#!/usr/bin/env bash
# Phase 22 job queue for one GPU: runs the lines of runs/p22_queue_gpu<N>.txt in order ("track T KEY=VALUE ..." -> p22_track.sh,
# "final T" -> p22_final.sh); a line is done once it appears in runs/p22_queue_gpu<N>.done. Lines may be appended while it runs;
# it exits when no line is left. Log runs/p22_queue_gpu<N>.log.   tmux new-session -d -s strat_p22_g0 'bash scripts/p22_queue.sh 0'
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
G="${1:?gpu}"; Q="runs/p22_queue_gpu$G.txt"; D="runs/p22_queue_gpu$G.done"; LOG="runs/p22_queue_gpu$G.log"; touch "$D"
say() { echo "[p22 queue $G] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
while :; do
  line=$(grep -v '^\s*#' "$Q" | grep . | while read -r l; do grep -qxF "$l" "$D" || { echo "$l"; break; }; done)
  [ -n "$line" ] || { say "queue empty - exiting"; exit 0; }
  [ "$(cat runs/p22_deadline)" -gt "$(date +%s)" ] || { say "deadline passed - exiting"; exit 0; }
  say "start: $line"
  read -r kind name rest <<< "$line"
  case "$kind" in
    track) eval "bash scripts/p22_track.sh $name $G $rest" ;;
    final) bash scripts/p22_final.sh "$name" "$G" ;;
    *) say "unknown job: $line" ;;
  esac
  say "done (exit $?): $line"; echo "$line" >> "$D"
done

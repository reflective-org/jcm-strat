#!/usr/bin/env bash
# Phase 16 watchdog: two queues can pick the same momentarily idle GPU (5-min polls vs a 20-s start window); the loser sees
# CUDA_ERROR_NO_DEVICE and JAX silently runs it on the CPU (weeks instead of hours). Every 2 min: any p16 segment whose log
# says 1xcpu is killed (its chain then fails and the queue moves on; the segment is re-run by hand or by a later queue).
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
while :; do
  for log in runs/p16_*_199?0101/log.txt; do
    [ -L "$(dirname "$log")" ] && continue
    if grep -q '1xcpu' "$log" 2>/dev/null && ! grep -q '\[launch\].*exit=' "$log"; then
      d=$(dirname "$log"); pid=$(pgrep -f "^python -m jcm_strat.main .*hydra.run.dir=$PWD/$d" | head -1)
      if [ -n "$pid" ]; then
        kill "$pid"; echo "[watchdog] $(date -Is) killed CPU-fallback run $d (pid $pid)" | tee -a runs/p16_watchdog.log
      fi
    fi
  done
  sleep 120
done

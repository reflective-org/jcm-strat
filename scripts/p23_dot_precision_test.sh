#!/usr/bin/env bash
# Phase 23 side test: 30 days of P20b (p22_teq) from P20b's end-of-2004 state, HIGHEST (jcm default) vs bf16x6
# (dinosaur default, miscompiled on our jaxlib - timing only), one after the other on GPU 0 once strat_p23_run is done.
# Then the ps gate on both (the x6 arm is expected to FAIL it) and per-chunk timings -> runs/p23_dot_test.log.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
LOG="$REPO/runs/p23_dot_test.log"; OUT="$REPO/docs/outputs/23_lat_nudging/dot_precision"; mkdir -p "$OUT"
step() { echo "[p23 dot] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
while tmux has-session -t =strat_p23_run 2>/dev/null; do sleep 120; done
while nvidia-smi -i 0 --query-compute-apps=pid --format=csv,noheader | grep -q .; do step "GPU 0 busy"; sleep 300; done
for arm in hi x6; do
  rundir="$REPO/runs/p23s_dot_$arm"; [ -s "$rundir/checkpoint.ckpt" ] && { step "$arm done already"; continue; }
  mkdir -p "$rundir"; entry=(-m jcm_strat.main); [ $arm = x6 ] && entry=("$REPO/scripts/p23_dot_precision_test.py")
  step "run $arm"
  ( cd "$rundir" && python "${entry[@]}" --config-dir "$REPO/jcm_strat/config" +experiment=p22_teq ++run.checkpoint_path=checkpoint.ckpt \
      run.start_time=2005-01-01 run.total_time=30 physics.terms.held_suarez.qbo.year=2005 \
      init=from_state "init.file=$REPO/runs/p20bt_20040101/checkpoint.ckpt" hydra.run.dir="$rundir" ) >> "$rundir/log.txt" 2>&1
  step "$arm exit=$? $(grep -m1 'dot precision\|p23 dot test' "$rundir/log.txt" | cut -c1-200)"
done
JAX_PLATFORMS=cpu "$REPO/.venv/bin/python" - "$REPO/runs" >> "$LOG" 2>&1 <<'PY'
import re, sys, datetime as d
for arm in ("hi", "x6"):
    ts, ev = [], []
    for l in open(f"{sys.argv[1]}/p23s_dot_{arm}/log.txt"):
        m = re.match(r"\[(\S+ \S+),(\d+)\]\[jcm.model\]\[INFO\] - (Model starting|Run completed)", l)
        if m: ts.append(d.datetime.fromisoformat(m.group(1)) + d.timedelta(milliseconds=int(m.group(2)))); ev.append(m.group(3))
    st = sorted((ts[i + 1] - ts[i]).total_seconds() for i in range(len(ts) - 1) if ev[i] == "Model starting")
    print(f"[p23 dot] {arm}: {len(st)} chunks, s per 10-day chunk: first {st[-1]:.1f} (compile), others {st[:-1]}")
PY
for arm in hi x6; do
  JAX_PLATFORMS=cpu "$REPO/.venv/bin/python" scripts/p19_ps_gate.py "runs/p23s_dot_$arm" --days 30 --out "$OUT" --tag "dot_$arm" >> "$LOG" 2>&1
  step "ps gate $arm exit=$? (0 PASS, 1 FAIL)"
done
step "finished"

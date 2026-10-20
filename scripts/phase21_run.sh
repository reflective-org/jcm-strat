#!/usr/bin/env bash
# Phase 21 pipeline (tmux strat_p21_run, log runs/p21_run.log): the full-physics references redone on the new jcm with
# the fixed Lott-Miller SSO, ECHAM sponge levels=1 (no target_T_K), cubic SL, one-month spin-up from 1989-12-01:
#   21a p21_echam_n400 (GPU_A, default 2): Phase 12 run 4 with ERA5 nudging < 400 hPa, QBO term, 1990-1994
#   21b p21_free       (GPU_B, default 3): Phase 14, free-running, no QBO, 1990-1999 (+ 5-yr aggregate)
# Runs from the phase19 worktree; record in the phase21 worktree (branch phase21-fullphys-rerun) docs/outputs/21_fullphys_rerun/.
# Steps: pytest -> smokes (skipped if passed) -> both spin-ups -> wait for the Phase 19b gate -> both chains in parallel, each
# followed by its own diagnostics vs the old run -> (after Phase 20's chain) the comparisons with Phase 20 alongside ->
# commit -> write-up agent. Failures -> failure agent. Restartable.
#   tmux new-session -d -s strat_p21_run 'GPU_A=2 GPU_B=3 bash /data/JCM_stripped/jcm-strat-phase19/scripts/phase21_run.sh'
set -uo pipefail
REPO=/data/JCM_stripped/jcm-strat-phase19
# shellcheck disable=SC1091
source "$REPO/scripts/p19_lib.sh"; cd "$REPO"
GPU_A="${GPU_A:-2}"; GPU_B="${GPU_B:-3}"; LOG="$REPO/runs/p21_run.log"
WT=/data/JCM_stripped/jcm-strat-phase21; OUT="$WT/docs/outputs/21_fullphys_rerun"; mkdir -p "$OUT/scores"
P12=/data/JCM_stripped/jcm-strat-phase12/runs; P14=/data/JCM_stripped/jcm-strat-phase14/runs
SPIN="1989-12-01 31"
SELF="$REPO/scripts/phase21_run.sh"
RELAUNCH="tmux new-session -d -s strat_p21_run 'RELAUNCHED=1 GPU_A=$GPU_A GPU_B=$GPU_B bash $SELF'"
step() { echo "[p21] $(pdt) $*" | tee -a "$LOG"; }
fail() { step "FAIL: $*"; failure_agent 21 "$*" "$SELF" "$LOG" "$RELAUNCH"; exit 1; }
step "start, commit $(git rev-parse --short HEAD), GPUs $GPU_A (21a) / $GPU_B (21b), RELAUNCHED=${RELAUNCHED:-0}"

JAX_PLATFORMS=cpu python -m pytest tests -q -p no:cacheprovider > runs/p21_tests.log 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 runs/p21_tests.log))"; [ $rc -eq 0 ] || fail "pytest (runs/p21_tests.log)"
wait_gpu "$GPU_A"; wait_gpu "$GPU_B"
smoke p21_echam_n400 p21echam_smoke5 "$GPU_A" physics.terms.qbo_nudging.year=1990 >> "$LOG" 2>&1 & s1=$!
smoke p21_free p21free_smoke5 "$GPU_B" >> "$LOG" 2>&1 & s2=$!
wait $s1 || fail "smoke p21echam_smoke5"; wait $s2 || fail "smoke p21free_smoke5"
step "smokes passed"

chain_a() { SPINUP="$SPIN" EXPERIMENT=p21_echam_n400 PREFIX=p21echam SCHEME=calendar YEARS=1990-1994 AGG=p21echam_5yr SAVE_INTERVAL=0.25 GPU="$GPU_A" \
  EXTRA_PER_SEG='physics.terms.qbo_nudging.year={year}' "$@" bash scripts/chain_segments.sh >> runs/p21echam_chain_stdout.log 2>&1; }
chain_b() { SPINUP="$SPIN" EXPERIMENT=p21_free PREFIX=p21free SCHEME=calendar YEARS=1990-1999 AGG=p21free_10yr SAVE_INTERVAL=0.25 GPU="$GPU_B" \
  EXTRA_PER_SEG= "$@" bash scripts/chain_segments.sh >> runs/p21free_chain_stdout.log 2>&1; }

wait_gpu "$GPU_A"; wait_gpu "$GPU_B"
SPINUP_ONLY=1 chain_a & c1=$!; SPINUP_ONLY=1 chain_b & c2=$!
wait $c1 || fail "21a spin-up (runs/p21echam_chain.log)"; wait $c2 || fail "21b spin-up (runs/p21free_chain.log)"
step "spin-ups done; waiting for the Phase 19b precision gate"
until [ -e runs/p19b_gate.PASS ] || [ -e runs/p19b_gate.FAIL ]; do sleep 120; done
if [ -e runs/p19b_gate.FAIL ]; then step "STOP: the Phase 19b precision gate failed - not continuing"; exit 1; fi
step "gate PASS"

cmp() { local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6
  JAX_PLATFORMS=cpu python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" --stride 1 \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" > "runs/p21_compare_$tag.log" 2>&1; local r=$?; step "compare $tag exit=$r"; return $r; }
clams() { local run=$1 v=$2 second=$3 sl=$4 l=$5
  JAX_PLATFORMS=cpu python scripts/aoa_vs_clams.py "$run" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" --second-run "$second" --second-label "$sl" \
    --label "$l [$v] vs CLaMS/WACCM" > "runs/p21_aoa_$(basename "$run")_$v.log" 2>&1; }

branch_a() {   # 21a chain, then its diagnostics
  wait_gpu "$GPU_A"; step "chain 21a p21echam 1990-1994 (GPU $GPU_A)"
  chain_a || { step "21a chain FAILED"; return 1; }
  step "21a chain finished"
  for y in $(seq 1990 1994); do JAX_PLATFORMS=cpu python scripts/throughput.py "runs/p21echam_${y}0101" --label "P21a echam n400 new jcm $y" --grid T63L95 --csv "$OUT/throughput_p21.csv" 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"; done
  local f=0
  cmp echam_rerun "$P12/p12echam_5yr" runs/p21echam_5yr "Full ECHAM, nudged, QBO term, 1990-1994: old jcm (broken LM, 10-level sponge, nudged < 150 hPa) -> new jcm (fixed LM, ECHAM sponge, < 400 hPa)" \
    "Phase 12 run 4 (old jcm)" "21a (new jcm)" || f=1
  for v in aoa_sfc aoa150 aoa500; do clams runs/p21echam_5yr "$v" "$P12/p12echam_5yr" "Phase 12 run 4 (old jcm)" "P21a full ECHAM nudged < 400 hPa, new jcm, 1990-1994" || f=1; done
  JAX_PLATFORMS=cpu python scripts/sweep_score.py runs/p21echam_5yr --name p21echam_5yr --out "$OUT/scores" --desc "21a" > runs/p21_score_a.log 2>&1 || f=1
  return $f
}
branch_b() {   # 21b chain, then its diagnostics
  wait_gpu "$GPU_B"; step "chain 21b p21free 1990-1999 (GPU $GPU_B)"
  chain_b || { step "21b chain FAILED"; return 1; }
  LINK_ONLY=1 COMPACT=0 AGG=p21free_5yr YEARS=1990-1994 chain_b_link || true
  step "21b chain finished"
  for y in $(seq 1990 1999); do JAX_PLATFORMS=cpu python scripts/throughput.py "runs/p21free_${y}0101" --label "P21b free new jcm $y" --grid T63L95 --csv "$OUT/throughput_p21.csv" 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"; done
  local f=0
  cmp free_rerun10 "$P14/p14free_10yr" runs/p21free_10yr "Full ECHAM free-running 1990-1999: old jcm (broken LM, 10-level sponge) -> new jcm (fixed LM, ECHAM sponge)" \
    "Phase 14 (old jcm)" "21b (new jcm)" || f=1
  cmp free_rerun5 "$P14/p14free_5yr" runs/p21free_5yr "Full ECHAM free-running, first 5 yr: old jcm -> new jcm" "Phase 14 first 5 yr" "21b first 5 yr" || f=1
  for v in aoa_sfc aoa150 aoa500; do clams runs/p21free_10yr "$v" "$P14/p14free_10yr" "Phase 14 (old jcm)" "P21b free-running, new jcm, 1990-1999" || f=1; done
  JAX_PLATFORMS=cpu python scripts/sweep_score.py runs/p21free_10yr --name p21free_10yr --out "$OUT/scores" --desc "21b, 1998-99 (ERA5 TEM)" > runs/p21_score_b.log 2>&1 || f=1
  JAX_PLATFORMS=cpu python scripts/sweep_score.py "$P14/p14free_10yr" --name p14free_10yr --out "$OUT/scores" --desc "Phase 14 old jcm, 1998-99" > runs/p21_score_p14.log 2>&1 || f=1
  return $f
}
chain_b_link() { SPINUP="$SPIN" EXPERIMENT=p21_free PREFIX=p21free SCHEME=calendar SAVE_INTERVAL=0.25 GPU="$GPU_B" EXTRA_PER_SEG= \
  bash scripts/chain_segments.sh >> runs/p21free_chain_stdout.log 2>&1; }

branch_a > runs/p21a_branch.log 2>&1 & b1=$!
branch_b > runs/p21b_branch.log 2>&1 & b2=$!
wait $b1; ra=$?; wait $b2; rb=$?
step "21a branch rc=$ra, 21b branch rc=$rb"
grep -q "21a chain finished" "$LOG" || fail "21a chain (runs/p21echam_chain.log)"
grep -q "21b chain finished" "$LOG" || fail "21b chain (runs/p21free_chain.log)"
dfail=0; [ $ra -eq 0 ] && [ $rb -eq 0 ] || dfail=1

# ---- Phase 20 alongside
step "waiting for the Phase 20 chain (runs/p20jhsso_10yr)"
if wait_chain p20jhsso 72 && [ -d runs/p20jhsso_5yr ]; then
  cmp echam_vs_p20 runs/p20jhsso_5yr runs/p21echam_5yr "1990-1994, new jcm, fixed LM, nudged < 400 hPa: dry 13d + LM (Phase 20) vs full ECHAM (21a)" \
    "20 dry + fixed LM" "21a full ECHAM" & q1=$!
  cmp free_vs_p20 runs/p20jhsso_10yr runs/p21free_10yr "1990-1999, new jcm, fixed LM: dry 13d + LM nudged < 400 hPa (Phase 20) vs free-running full ECHAM (21b)" \
    "20 dry + fixed LM" "21b free full ECHAM" & q2=$!
  wait $q1 || dfail=1; wait $q2 || dfail=1
  JAX_PLATFORMS=cpu python scripts/mesosphere_wstar.py "runs/p21echam_19940101:21a full ECHAM nudged 1994" "runs/p21free_19990101:21b free 1999" \
    "runs/p20jhsso_19990101:20 dry + fixed LM 1999" --reference "$P12/p12echam_19940101:Phase 12 run 4 (old jcm) 1994" --stride 1 --out "$OUT" --tag p21 \
    > runs/p21_mesosphere.log 2>&1 || dfail=1
else
  step "Phase 20 chain not available: comparisons with Phase 20 not made"; dfail=1
fi
grep -l Traceback runs/p21_*.log >> "$LOG" 2>/dev/null && dfail=1
git -C "$WT" add docs/outputs/21_fullphys_rerun && git -C "$WT" commit -q -m "Phase 21: full-physics rerun diagnostics (metrics and plots from the pipeline)" && step "committed in $WT $(git -C "$WT" rev-parse --short HEAD)"
[ $dfail -eq 0 ] || failure_agent 21 "a diagnostics step failed or was skipped (see runs/p21_run.log, runs/p21*_branch.log, runs/p21_*.log); both chains are complete" "$SELF" "$LOG" "(do not relaunch the pipeline; rerun only the failed diagnostic by hand, writing into $OUT, and commit in $WT)"
step "write-up agent"
writeup_agent 21
step "finished"

#!/usr/bin/env bash
# Phase 19 pipeline (tmux strat_p19_run, log runs/p19_run.log): jcm update -> precision gate -> 19d baseline.
# 19d = the 13d physics (Jucker + Hines, no Lott-Miller) on strat81 with ERA5 nudging < 400 hPa (experiment p19_jh_n400,
# = Phase 13c run 2 p13jhn400 on the OLD jcm) on the new jcm 35dc1997 / dinosaur 1.5.0. Purpose: the update's effect alone.
# Steps: pytest gate -> 5-day smoke + restart smoke (skipped if passed) -> the one-month spin-up 1989-12-01 (SPINUP_ONLY)
# -> 19b gate: 30-day NH-SH / global ps drift of that spin-up (scripts/p19_ps_gate.py; writes runs/p19b_gate.PASS|FAIL,
# which the Phase 20/21 pipelines wait for) -> chain 1990-1994 -> diagnostics at STRIDE 1 vs the old p13jhn400 (first 5 yr)
# and p13jh (13d) -> commit metrics/plots -> headless write-up agent. Any failure -> headless failure agent.
# Restartable: finished smokes/segments are skipped.  GPU: $GPU (default 4: GPU 0 was taken by another job on 2026-10-07).
#   tmux new-session -d -s strat_p19_run 'GPU=4 bash /data/JCM_stripped/jcm-strat-phase19/scripts/phase19_run.sh'
set -uo pipefail
REPO=/data/JCM_stripped/jcm-strat-phase19
# shellcheck disable=SC1091
source "$REPO/scripts/p19_lib.sh"; cd "$REPO"
GPU="${GPU:-4}"; LOG="$REPO/runs/p19_run.log"; OUT="$REPO/docs/outputs/19_jcm_update"; mkdir -p "$OUT/scores"
P13=/data/JCM_stripped/jcm-strat-phase13/runs; P12=/data/JCM_stripped/jcm-strat-phase12/runs
PREFIX=p19jhn400; AGG=${PREFIX}_5yr; YEARS=1990-1994; SPIN="1989-12-01 31"
SELF="$REPO/scripts/phase19_run.sh"
RELAUNCH="tmux new-session -d -s strat_p19_run 'RELAUNCHED=1 GPU=$GPU bash $SELF'"
step() { echo "[p19] $(pdt) $*" | tee -a "$LOG"; }
fail() { step "FAIL: $*"; failure_agent 19 "$*" "$SELF" "$LOG" "$RELAUNCH"; exit 1; }
step "start, commit $(git rev-parse --short HEAD), GPU $GPU, RELAUNCHED=${RELAUNCHED:-0}"

# ---- tests (CPU)
JAX_PLATFORMS=cpu python -m pytest tests -q -p no:cacheprovider > runs/p19_tests.log 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 runs/p19_tests.log))"; [ $rc -eq 0 ] || fail "pytest (runs/p19_tests.log)"

# ---- smokes
wait_gpu "$GPU"
smoke p19_jh_n400 p19_smoke5 "$GPU" physics.terms.held_suarez.qbo.year=1990 >> "$LOG" 2>&1 || fail "smoke p19_smoke5"
if ! grep -q "^RESULT PASS" runs/p19_smoke5r/smoke_check_restart.txt 2>/dev/null; then
  smoke p19_jh_n400 p19_smoke5r "$GPU" physics.terms.held_suarez.qbo.year=1990 init=from_state "init.file=$REPO/runs/p19_smoke5/checkpoint.ckpt" >> "$LOG" 2>&1 || fail "restart smoke"
  JAX_PLATFORMS=cpu python scripts/p19_smoke_check.py runs/p19_smoke5r --restart > runs/p19_smoke5r/smoke_check_restart.txt 2>&1 || fail "restart smoke check"
fi
step "smokes passed (5-day + restart re-initialisation)"

# ---- spin-up month, then the 19b precision gate on it
wait_gpu "$GPU"
SPINUP="$SPIN" SPINUP_ONLY=1 EXPERIMENT=p19_jh_n400 PREFIX=$PREFIX SCHEME=calendar YEARS=$YEARS AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash scripts/chain_segments.sh > runs/${PREFIX}_chain_stdout.log 2>&1 || fail "spin-up (runs/${PREFIX}_chain.log)"
step "spin-up done: runs/${PREFIX}_spinup_19891201"
JAX_PLATFORMS=cpu python scripts/p19_ps_gate.py runs/${PREFIX}_spinup_19891201 --ref "$P13/p13jhn400_19900101" --days 31 \
  --out "$OUT" --tag p19 > runs/p19b_gate.log 2>&1; rc=$?
cp runs/p19b_grep_dot_algorithm.txt runs/p19b_dot_precision_test.log "$OUT/" 2>/dev/null
if [ $rc -eq 0 ]; then touch runs/p19b_gate.PASS; rm -f runs/p19b_gate.FAIL; step "19b gate PASS ($(grep 'Result' runs/p19b_gate.log))"
else touch runs/p19b_gate.FAIL; fail "19b precision gate FAILED or errored (runs/p19b_gate.log; $OUT/p19_ps_gate.md) - do NOT relaunch, this is a science stop"; fi

# ---- the 5-year chain
wait_gpu "$GPU"
step "chain $PREFIX $YEARS (GPU $GPU)"
SPINUP="$SPIN" EXPERIMENT=p19_jh_n400 PREFIX=$PREFIX SCHEME=calendar YEARS=$YEARS AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash scripts/chain_segments.sh >> runs/${PREFIX}_chain_stdout.log 2>&1 || fail "chain (runs/${PREFIX}_chain.log)"
step "chain finished -> runs/$AGG"

# ---- diagnostics (CPU), stride 1
export JAX_PLATFORMS=cpu
dfail=0
link_first_days "$P13/p13jhn400_10yr" runs/old_p13jhn400_5yr 1826 >> "$LOG" 2>&1
for y in 1990 1991 1992 1993 1994; do
  python scripts/throughput.py "runs/${PREFIX}_${y}0101" --label "P19d jh n400 new jcm $y" --grid T63L95 --csv "$OUT/throughput_p19.csv" 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done
cmp() { local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6
  python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" --stride 1 \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" > "runs/p19_compare_$tag.log" 2>&1; local r=$?; step "compare $tag exit=$r"; return $r; }
cmp update runs/old_p13jhn400_5yr "runs/$AGG" "Jucker + Hines, nudged < 400 hPa, 1990-1994: OLD jcm 849893be strat81 -> NEW jcm 35dc1997 L95 cubic (stride 1)" \
  "old jcm (p13jhn400, first 5 yr)" "new jcm (p19jhn400)" & p1=$!
cmp vs13d "$P13/p13jh_5yr" "runs/$AGG" "13d (Jucker + Hines, nudged < 150 hPa, old jcm) vs 19d (nudged < 400 hPa, new jcm), 1990-1994 (stride 1)" \
  "13d p13jh (old jcm, < 150 hPa)" "19d p19jhn400 (new jcm, < 400 hPa)" & p2=$!
wait $p1 || dfail=1; wait $p2 || dfail=1
for v in aoa150 aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py "runs/$AGG" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" --second-run runs/old_p13jhn400_5yr --second-label "old jcm" \
    --label "P19d new jcm 1990-1994 [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM; old jcm alongside" > "runs/p19_aoa_$v.log" 2>&1 || dfail=1 &
done; wait
grep -l Traceback runs/p19_aoa_*.log >> "$LOG" 2>/dev/null && dfail=1
python scripts/mesosphere_wstar.py "runs/${PREFIX}_19940101:19d new jcm 1994" "$P13/p13jhn400_19940101:13c run 2 old jcm 1994" \
  --reference "$P12/p12echam_19940101:full ECHAM (old jcm) 1994" --stride 1 --out "$OUT" --tag p19 > runs/p19_mesosphere.log 2>&1
rc=$?; step "mesosphere exit=$rc"; [ $rc -eq 0 ] || dfail=1
python scripts/sweep_score.py "runs/$AGG" --name p19jhn400_5yr --out "$OUT/scores" --desc "19d new jcm" > runs/p19_score_new.log 2>&1 || dfail=1 &
python scripts/sweep_score.py runs/old_p13jhn400_5yr --name p13jhn400_first5yr --out "$OUT/scores" --desc "13c run 2 old jcm, first 5 yr" > runs/p19_score_old.log 2>&1 || dfail=1 &
wait; grep -l Traceback runs/p19_score_*.log >> "$LOG" 2>/dev/null && dfail=1; step "scores done"
unset JAX_PLATFORMS

# ---- commit the metrics and plots
git add "$OUT" && git commit -q -m "Phase 19: precision gate and 19d diagnostics (metrics and plots from the pipeline)" && step "committed $(git rev-parse --short HEAD)"
[ $dfail -eq 0 ] || failure_agent 19 "a diagnostics step failed (see runs/p19_*.log); the chain itself is complete" "$SELF" "$LOG" "(do not relaunch the pipeline; rerun only the failed diagnostic by hand and commit)"
step "write-up agent"
writeup_agent 19
step "finished"

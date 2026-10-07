#!/usr/bin/env bash
# Phase 20 pipeline (tmux strat_p20_run, log runs/p20_run.log): dry 13d physics + the FIXED Lott-Miller SSO (experiment
# p20_jh_sso_n400 = p19_jh_n400 + lott_miller_sso), strat81, nudging < 400 hPa, new jcm, one-month spin-up, 1990-1999.
# Runs from the phase19 worktree (its venv, runs/); the record goes to the phase20 worktree (branch phase20-sso-fixed):
# docs/outputs/20_sso_fixed/. Steps: pytest -> smoke (skipped if passed) -> spin-up -> wait for the Phase 19b gate ->
# chain 1990-1999 (+ 5-yr aggregate) -> diagnostics at stride 1 (vs 19d = THE comparison, needs runs/p19jhn400_5yr; vs the
# old-jcm 13c runs 1/2 and 13d; ERA5 1998-99 w*/mass flux via sweep_score; spin-up angular momentum) -> commit -> write-up
# agent. Any failure -> failure agent. Restartable.
#   tmux new-session -d -s strat_p20_run 'GPU=1 bash /data/JCM_stripped/jcm-strat-phase19/scripts/phase20_run.sh'
set -uo pipefail
REPO=/data/JCM_stripped/jcm-strat-phase19
# shellcheck disable=SC1091
source "$REPO/scripts/p19_lib.sh"; cd "$REPO"
GPU="${GPU:-1}"; LOG="$REPO/runs/p20_run.log"
WT=/data/JCM_stripped/jcm-strat-phase20; OUT="$WT/docs/outputs/20_sso_fixed"; mkdir -p "$OUT/scores"
P13=/data/JCM_stripped/jcm-strat-phase13/runs; P12=/data/JCM_stripped/jcm-strat-phase12/runs
PREFIX=p20jhsso; AGG=${PREFIX}_10yr; AGG5=${PREFIX}_5yr; YEARS=1990-1999; SPIN="1989-12-01 31"
SELF="$REPO/scripts/phase20_run.sh"
RELAUNCH="tmux new-session -d -s strat_p20_run 'RELAUNCHED=1 GPU=$GPU bash $SELF'"
step() { echo "[p20] $(pdt) $*" | tee -a "$LOG"; }
fail() { step "FAIL: $*"; failure_agent 20 "$*" "$SELF" "$LOG" "$RELAUNCH"; exit 1; }
step "start, commit $(git rev-parse --short HEAD), GPU $GPU, RELAUNCHED=${RELAUNCHED:-0}"

JAX_PLATFORMS=cpu python -m pytest tests -q -p no:cacheprovider > runs/p20_tests.log 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 runs/p20_tests.log))"; [ $rc -eq 0 ] || fail "pytest (runs/p20_tests.log)"
wait_gpu "$GPU"
smoke p20_jh_sso_n400 p20_smoke5 "$GPU" physics.terms.held_suarez.qbo.year=1990 >> "$LOG" 2>&1 || fail "smoke p20_smoke5"
step "smoke passed"

wait_gpu "$GPU"
SPINUP="$SPIN" SPINUP_ONLY=1 EXPERIMENT=p20_jh_sso_n400 PREFIX=$PREFIX SCHEME=calendar YEARS=$YEARS AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash scripts/chain_segments.sh > runs/${PREFIX}_chain_stdout.log 2>&1 || fail "spin-up (runs/${PREFIX}_chain.log)"
step "spin-up done; waiting for the Phase 19b precision gate (runs/p19b_gate.PASS|FAIL)"
until [ -e runs/p19b_gate.PASS ] || [ -e runs/p19b_gate.FAIL ]; do sleep 120; done
if [ -e runs/p19b_gate.FAIL ]; then step "STOP: the Phase 19b precision gate failed - not continuing (see docs/outputs/19_jcm_update/p19_ps_gate.md)"; exit 1; fi
step "gate PASS"

wait_gpu "$GPU"
step "chain $PREFIX $YEARS (GPU $GPU)"
SPINUP="$SPIN" EXPERIMENT=p20_jh_sso_n400 PREFIX=$PREFIX SCHEME=calendar YEARS=$YEARS AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash scripts/chain_segments.sh >> runs/${PREFIX}_chain_stdout.log 2>&1 || fail "chain (runs/${PREFIX}_chain.log)"
LINK_ONLY=1 COMPACT=0 SPINUP="$SPIN" EXPERIMENT=p20_jh_sso_n400 PREFIX=$PREFIX SCHEME=calendar YEARS=1990-1994 AGG=$AGG5 SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash scripts/chain_segments.sh >> runs/${PREFIX}_chain_stdout.log 2>&1 || fail "5-yr aggregate link"
step "chain finished -> runs/$AGG, runs/$AGG5"

# ---- diagnostics (CPU), stride 1
export JAX_PLATFORMS=cpu
dfail=0
for y in $(seq 1990 1999); do
  python scripts/throughput.py "runs/${PREFIX}_${y}0101" --label "P20 jh + fixed LM n400 $y" --grid T63L81 --csv "$OUT/throughput_p20.csv" 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done
cmp() { local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6
  python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" --stride 1 \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" > "runs/p20_compare_$tag.log" 2>&1; local r=$?; step "compare $tag exit=$r"; return $r; }
cmp sso10_vs_13c1 "$P13/p13jgn400_10yr" "runs/$AGG" "Jucker + Hines + Lott-Miller, n400, 1990-1999: BROKEN LM on the old jcm (13c run 1) -> FIXED LM on the new jcm" \
  "13c run 1 (old jcm, broken LM)" "20 (new jcm, fixed LM)" & a1=$!
cmp sso10_vs_13c2 "$P13/p13jhn400_10yr" "runs/$AGG" "Jucker + Hines n400, 1990-1999: no LM on the old jcm (13c run 2) -> fixed LM on the new jcm" \
  "13c run 2 (old jcm, no LM)" "20 (new jcm, fixed LM)" & a2=$!
cmp sso10_vs_13d "$P13/p13jh_10yr" "runs/$AGG" "13d (Jucker + Hines, nudged < 150 hPa, old jcm) vs 20 (+ fixed LM, < 400 hPa, new jcm), 1990-1999" \
  "13d p13jh (old jcm)" "20 p20jhsso (new jcm)" & a3=$!
wait $a1 || dfail=1; wait $a2 || dfail=1; wait $a3 || dfail=1
for v in aoa150 aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py "runs/$AGG" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" --second-run "runs/$AGG5" --second-label "after 5 yr" \
    --label "P20 fixed Lott-Miller 1990-1999 [$v]: age after 10 yr (last 60 d) vs CLaMS/WACCM" > "runs/p20_aoa_$v.log" 2>&1 &
done; wait
python scripts/p20_spinup_adjust.py "runs/p19jhn400_spinup_19891201,runs/p19jhn400_19900101:19d no SSO" \
  "runs/${PREFIX}_spinup_19891201,runs/${PREFIX}_19900101:20 fixed Lott-Miller" --out "$OUT" --tag p20 --days-after 31 > runs/p20_spinup_adjust.log 2>&1
rc=$?; step "spin-up adjustment exit=$rc"; [ $rc -eq 0 ] || dfail=1
python scripts/sweep_score.py "runs/$AGG" --name p20jhsso_10yr --out "$OUT/scores" --desc "20: 13d + fixed LM, n400, new jcm, last 2 yr 1998-99 (ERA5 TEM)" > runs/p20_score_10.log 2>&1 &
python scripts/sweep_score.py "$P13/p13jhn400_10yr" --name p13jhn400_10yr --out "$OUT/scores" --desc "13c run 2 old jcm, 1998-99" > runs/p20_score_13c2.log 2>&1 &
python scripts/sweep_score.py "$P13/p13jh_10yr" --name p13jh_10yr --out "$OUT/scores" --desc "13d old jcm, 1998-99" > runs/p20_score_13d.log 2>&1 &
wait
grep -l Traceback runs/p20_aoa_*.log runs/p20_score_*.log >> "$LOG" 2>/dev/null && dfail=1
# THE comparison needs 19d's 5-yr aggregate
step "waiting for the Phase 19d chain (runs/p19jhn400_5yr)"
wait_chain p19jhn400 72; rc=$?
if [ $rc -eq 0 ]; then
  cmp sso5_vs_19d runs/p19jhn400_5yr "runs/$AGG5" "13d physics, strat81, n400, new jcm, 1990-1994: without (19d) -> with the fixed Lott-Miller (20)" \
    "19d (no SSO)" "20 (fixed Lott-Miller)" || dfail=1
  for v in aoa150 aoa_sfc; do
    python scripts/aoa_vs_clams.py "runs/$AGG5" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" --second-run runs/p19jhn400_5yr --second-label "19d no SSO" \
      --label "P20 fixed Lott-Miller 1990-1994 [$v] vs 19d (no SSO) vs CLaMS/WACCM" > "runs/p20_aoa5_$v.log" 2>&1 || dfail=1
  done
  python scripts/sweep_score.py "runs/$AGG5" --name p20jhsso_5yr --out "$OUT/scores" --desc "20 first 5 yr (1993-94 window)" > runs/p20_score_5.log 2>&1 || dfail=1
  python scripts/mesosphere_wstar.py "runs/${PREFIX}_19940101:20 fixed LM 1994" "runs/${PREFIX}_19990101:20 fixed LM 1999" "runs/p19jhn400_19940101:19d no SSO 1994" \
    --reference "$P12/p12echam_19940101:full ECHAM (old jcm) 1994" --stride 1 --out "$OUT" --tag p20 > runs/p20_mesosphere.log 2>&1 || dfail=1
else
  step "19d chain not available (wait_chain rc=$rc): sso5_vs_19d not made"; dfail=1
  python scripts/mesosphere_wstar.py "runs/${PREFIX}_19940101:20 fixed LM 1994" "runs/${PREFIX}_19990101:20 fixed LM 1999" \
    --reference "$P12/p12echam_19940101:full ECHAM (old jcm) 1994" --stride 1 --out "$OUT" --tag p20 > runs/p20_mesosphere.log 2>&1
fi
unset JAX_PLATFORMS
git -C "$WT" add docs/outputs/20_sso_fixed && git -C "$WT" commit -q -m "Phase 20: fixed Lott-Miller diagnostics (metrics and plots from the pipeline)" && step "committed in $WT $(git -C "$WT" rev-parse --short HEAD)"
[ $dfail -eq 0 ] || failure_agent 20 "a diagnostics step failed or was skipped (see runs/p20_run.log, runs/p20_*.log); the chain itself is complete" "$SELF" "$LOG" "(do not relaunch the pipeline; rerun only the failed diagnostic by hand, writing into $OUT, and commit in $WT)"
step "write-up agent"
writeup_agent 20
step "finished"

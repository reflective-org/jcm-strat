#!/usr/bin/env bash
# Phase 14, 5-year milestone (tmux strat_p14_5yr, log runs/p14_5yr_diag.log): Susanne, 2026-09-23: "can we do a 5 year run
# then like we did in the earlier phases and then just extend the run to the planned 10 years?" The running ten-segment chain
# IS that run (segment 1995 starts from 1994's checkpoint exactly as an extension would), so this script only waits, on the
# CPU, for segment 1994 to finish, links the first five segments as runs/p14free_5yr (chain_segments.sh skips finished segments
# and only links; GPU=1 is passed so its busy check looks at an idle card - nothing runs on any GPU here) and produces the
# Phase 12 diagnostics for the 5-year run against the nudged full physics (p12echam_5yr) and the dry control (p12ctl_5yr).
# The GPU chain continues to 1999 untouched; scripts/phase14_run.sh repeats the 5-yr compare (identical) when it finishes.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
export JAX_PLATFORMS=cpu
OUT="$REPO/docs/outputs/14_free_physics"; LOG="$REPO/runs/p14_5yr_diag.log"; AGG5=p14free_5yr
step() { echo "[p14-5yr] $(date -Is) $*" | tee -a "$LOG"; }
step "start, commit $(git rev-parse --short HEAD); waiting for segment 1994"
n=0
until grep -q "done p14free_19940101 exit=0" "$REPO/runs/p14free_chain.log" 2>/dev/null; do
  grep -q "FAILED" "$REPO/runs/p14free_chain.log" 2>/dev/null && { step "FAIL: the chain reported a failed segment"; exit 1; }
  [ $((n % 30)) -eq 0 ] && step "waiting ($(tail -1 "$REPO/runs/p14free_chain.log" | cut -c1-90))"
  n=$((n + 1)); sleep 120
done
step "segment 1994 done - linking $AGG5"
EXTRA_PER_SEG="" FIRST_SEG_EXTRA="" COMPACT=0 EXPERIMENT=p14_free PREFIX=p14free SCHEME=calendar YEARS=1990-1994 AGG=$AGG5 SAVE_INTERVAL=0.25 GPU=1 \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p14free_5yr_link.log" 2>&1; rc=$?
step "link exit=$rc ($(ls "$REPO/runs/$AGG5"/longrun_day*.nc 2>/dev/null | wc -l) chunk files)"; [ $rc -eq 0 ] || exit 1
for y in 1990 1991 1992 1993 1994; do
  python scripts/throughput.py "runs/p14free_${y}0101" --label "P14 free $y" --grid T63L95 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done
CLOCKS="aoa_sfc aoa500 aoa150"
step "phase12_compare: free first 5 yr vs nudged full physics"
python scripts/phase12_compare.py --before runs/p12echam_5yr --after "runs/$AGG5" --tag free5 --clocks $CLOCKS \
  --label "free-running full physics, first 5 yr (1990-1994) vs the nudged full physics 1990-1994 (both T63L95)" \
  --before-label "nudged (p12echam, 5 yr)" --after-label "free (p14free, first 5 yr)" --out "$OUT" > "$REPO/runs/p14_compare_free5.log" 2>&1; step "compare free5 exit=$?"
step "phase12_compare: free first 5 yr vs the dry control"
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after "runs/$AGG5" --tag free5_vs_ctl --clocks $CLOCKS \
  --label "free-running full physics, first 5 yr (1990-1994, T63L95) vs the dry Polvani-Kushner control 1990-1994 (strat63)" \
  --before-label "ctl: dry PK, nudged" --after-label "free (p14free, first 5 yr)" --out "$OUT" > "$REPO/runs/p14_compare_free5_vs_ctl.log" 2>&1; step "compare free5_vs_ctl exit=$?"
for v in $CLOCKS; do
  python scripts/aoa_vs_clams.py "runs/$AGG5" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P14 free 1990-1994 [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p14_5yr_aoa_${v}.log" 2>&1; step "aoa_vs_clams $v exit=$?"
done
python scripts/aoa_vs_clams.py "runs/$AGG5" "$OUT" --years 2005-2009 --last-saves 240 --var aoa_sfc --mark-levels 500,55,30 --pmax 1000 \
  --label "P14 free 1990-1994 [aoa_sfc]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p14_5yr_aoa_aoa_sfc_levels.log" 2>&1; step "aoa_vs_clams aoa_sfc levels exit=$?"
step "finished"

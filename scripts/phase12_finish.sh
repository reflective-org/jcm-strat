#!/usr/bin/env bash
# Phase 12, second half (tmux strat_p12_finish, log runs/p12_run.log): the first pipeline run (scripts/phase12_run.sh,
# 2026-09-16 14:45 PDT) lost the noqbo chain to a bash quirk in chain_segments.sh (an empty EXTRA_PER_SEG became the
# hydra override '}', fixed in 1abb96b) and, by design, skips the diagnostics when a chain fails. This script runs the
# noqbo chain at once on GPU_A (GPU 3: Susanne, 2026-09-16 16:00 PDT, "if GPU3 is available you can use that"), waits
# for that pipeline to end (ctl on GPU 1 and l81 on GPU 2 finished), then runs the diagnostics.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1994}"; GPU_A="${GPU_A:-3}"
P11A="${P11A:-/data/JCM_stripped/jcm-strat-phase11/runs/p11a_5yr}"
OUT="$REPO/docs/outputs/12_circulation"; LOG="$REPO/runs/p12_run.log"
step() { echo "[p12-finish] $(date -Is) $*" | tee -a "$LOG"; }
y0="${YEARS%-*}"; y1="${YEARS#*-}"
step "start, commit $(git rev-parse --short HEAD); launching chain noqbo on GPU $GPU_A"
nvidia-smi -i "$GPU_A" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q . && { step "FAIL: GPU $GPU_A busy"; exit 1; }
EXTRA_PER_SEG="" EXPERIMENT=p12_noqbo PREFIX=p12noqbo SCHEME=calendar YEARS="$YEARS" AGG=p12noqbo_5yr SAVE_INTERVAL=0.25 GPU="$GPU_A" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p12noqbo_chain_stdout.log" 2>&1 & pn=$!
step "waiting for tmux strat_p12_run (ctl, l81) to end"
while tmux has-session -t strat_p12_run 2>/dev/null; do sleep 300; done
for pre in p12ctl p12l81; do
  grep -q "chain finished" "$REPO/runs/${pre}_chain.log" 2>/dev/null || { step "FAIL: chain $pre did not finish (runs/${pre}_chain.log)"; exit 1; }
done
step "ctl and l81 chains finished; waiting for noqbo"
wait $pn; ra=$?
step "chain noqbo exit=$ra"; [ $ra -eq 0 ] || { step "FAIL: chain noqbo (runs/p12noqbo_chain.log)"; exit 1; }

export JAX_PLATFORMS=cpu
step "throughput rows"
for pre in p12noqbo p12l81 p12ctl; do for y in $(seq "$y0" "$y1"); do
  python scripts/throughput.py "runs/${pre}_${y}0101" --label "P12 ${pre#p12} $y" --grid "$([ $pre = p12l81 ] && echo T63L81 || echo T63L63)" --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done; done
step "phase12_compare: noqbo vs ctl"
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12noqbo_5yr --tag noqbo --label "QBO nudging off (strat63, $YEARS)" \
  --before-label "ctl: QBO on" --after-label "QBO off" --out "$OUT" > "$REPO/runs/p12_compare_noqbo.log" 2>&1; step "compare noqbo exit=$?"
step "phase12_compare: l81 vs ctl"
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12l81_5yr --tag l81 --label "full L95 troposphere: strat63 -> strat81 (QBO on, $YEARS)" \
  --before-label "ctl: strat63" --after-label "strat81" --out "$OUT" > "$REPO/runs/p12_compare_l81.log" 2>&1; step "compare l81 exit=$?"
step "phase12_compare: ctl vs p11a (reproduction check: identical dynamics expected)"
python scripts/phase12_compare.py --before "$P11A" --after runs/p12ctl_5yr --tag ctl_vs_p11a --label "Phase 12 control vs Phase 11 A (same dynamics)" \
  --before-label "p11a_5yr" --after-label "p12ctl_5yr" --clocks aoa_sfc aoa --no-waccm --out "$OUT" > "$REPO/runs/p12_compare_ctl.log" 2>&1; step "compare ctl exit=$?"
for pre in p12ctl p12noqbo p12l81; do for v in aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py "runs/${pre}_5yr" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P12 ${pre#p12} $YEARS [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/${pre}_aoa_${v}.log" 2>&1; step "aoa_vs_clams $pre $v exit=$?"
done; done
step "finished"

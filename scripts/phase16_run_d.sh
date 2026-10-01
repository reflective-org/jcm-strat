#!/usr/bin/env bash
# Phase 16 queue D (2026-09-29): re-runs the two base continuations that hit a transient OOM at launch (GPUs still releasing the
# memory of killed runs) on the first idle GPU, and takes over the final diagnostics from A/B/C (waits for their done flags).
# Derived from phase16_run.sh, which must not be edited while A/B/C run it. Phase 16 (Susanne 2026-09-28 21:30 PDT): three queues of ten-year chains (scripts/phase16_queues.txt) on GPUs 0 / 1 / first idle,
# each queue in its own tmux session (strat_p16_A/B/C, log runs/p16_<queue>.log), hard budget BUDGET_H (23 h; "nothing longer
# than 24 h"). Every finished run is scored (scripts/sweep_score.py, last two years) into docs/outputs/16_mixing/scores, the
# leaderboard + record are rewritten and committed (under a lock shared by the queues). The LAST queue to finish runs the
# cross-run diagnostics (phase12_compare, stride 1, of every run against the ten-year base; aoa_vs_clams for the mixing runs).
#   bash scripts/phase16_run.sh A        # GPU 0
#   bash scripts/phase16_run.sh B        # GPU 1
#   bash scripts/phase16_run.sh C        # first idle of GPU 2, 0, 1 (a colleague's job held GPU 2 at launch)
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
Q="${1:-D}"; BUDGET_H="${BUDGET_H:-23}"; YEARS="${YEARS:-1990-1999}"; MPY="${MPY:-32}"
case "$Q" in D) GPUS=(0 2 1);; *) echo "this script runs queue D"; exit 1;; esac
OUT="$REPO/docs/outputs/16_mixing"; SCORES="$OUT/scores"; mkdir -p "$OUT" "$SCORES" "$REPO/runs"
LOG="$REPO/runs/p16_$Q.log"; LOCK="$REPO/runs/.p16_git.lock"; QUEUES="$REPO/scripts/phase16_queues.txt"
P13="${P13:-/data/JCM_stripped/jcm-strat-phase13/runs}"
T0=$(date +%s); DEADLINE=$((T0 + BUDGET_H * 3600))
step() { echo "[p16$Q] $(date -Is) $*" | tee -a "$LOG"; }
runlog() { flock "$LOCK" bash -c "echo '- $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M PDT') — queue $Q: $*' >> '$OUT/output.md'"; }
remaining_min() { echo $(( (DEADLINE - $(date +%s)) / 60 )); }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
gpu_visible() { CUDA_VISIBLE_DEVICES="$1" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1; }
record() {  # <message>: leaderboard + commit under the shared lock
  flock "$LOCK" bash -c "cd '$REPO' && JAX_PLATFORMS=cpu python scripts/sweep_leaderboard.py '$OUT' --scores '$SCORES' 2>&1 | tail -1; \
    git add -A '$OUT' PROGRESS.md >/dev/null 2>&1; git commit -q -m 'Phase 16: $1' >/dev/null 2>&1 && echo committed || echo 'nothing to commit'" | tee -a "$LOG"
}
pick_gpu() {  # first idle, JAX-visible GPU of the queue's list; waits (5-min polls) until one is free or the budget is gone
  local g n=0
  while :; do
    for g in "${GPUS[@]}"; do gpu_busy "$g" || { gpu_visible "$g" && { echo "$g"; return 0; }; }; done
    [ $((n % 6)) -eq 0 ] && step "waiting for an idle GPU among ${GPUS[*]}"; n=$((n + 1))
    [ "$(remaining_min)" -gt $((6 * MPY + 30)) ] || return 1
    sleep 300
  done
}
touch "$REPO/runs/p16_finish.started"     # A/B/C then skip their final block; D runs it after they are done
step "start queue $Q, commit $(git rev-parse --short HEAD), GPUs ${GPUS[*]}, budget $BUDGET_H h (deadline $(date -d @"$DEADLINE" -Is)), years $YEARS"
runlog "started (commit $(git rev-parse --short HEAD), GPUs ${GPUS[*]}, budget $BUDGET_H h)"

run_entry() {  # <name> <experiment> <overrides> <desc>
  local name=$1 exp=$2 ov=$3 desc=$4; local prefix="p16_$name"; local agg="${prefix}_10yr"
  if [ -s "$SCORES/$name.json" ]; then step "skip $name (scored)"; return 0; fi
  # segments already finished (the linked 1990-1994 of the bases) do not cost time
  local todo=0 y; for y in $(seq "${YEARS%-*}" "${YEARS#*-}"); do grep -q '\[launch\].*exit=0' "runs/${prefix}_${y}0101/log.txt" 2>/dev/null || todo=$((todo + 1)); done
  local need=$(( todo * MPY + 25 ))
  if [ "$(remaining_min)" -lt "$need" ]; then step "SKIP $name for budget: ~$need min needed, $(remaining_min) left"; runlog "**skipped for budget**: $name ($desc)"; return 2; fi
  local gpu; gpu=$(pick_gpu) || { step "SKIP $name: no idle GPU within the budget"; runlog "**skipped**: $name (no idle GPU within the budget)"; return 2; }
  local extra=""; [ "$ov" != "-" ] && extra="$ov"
  step "run $name on GPU $gpu: experiment $exp, $todo segment(s) to run, overrides: ${extra:-none}"
  local t1; t1=$(date +%s)
  EXPERIMENT="$exp" PREFIX="$prefix" SCHEME=calendar YEARS="$YEARS" AGG="$agg" SAVE_INTERVAL=0.25 GPU="$gpu" EXTRA="$extra" \
    bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/${prefix}_chain_stdout.log" 2>&1; local rc=$?
  local mins=$(( ($(date +%s) - t1) / 60 ))
  step "chain $name exit=$rc after $mins min (runs/${prefix}_chain.log)"
  if [ $rc -ne 0 ]; then runlog "**FAILED** chain $name after $mins min (runs/${prefix}_chain.log)"; record "$name failed"; return 1; fi
  [ "$todo" -gt 0 ] && [ "$mins" -gt $((5 * todo)) ] && { MPY=$(( (mins + todo - 1) / todo )); step "measured $MPY min/yr"; }
  JAX_PLATFORMS=cpu python scripts/sweep_score.py "runs/$agg" --name "$name" --stage "$Q" --desc "$desc" --window-years 2 --out "$SCORES" \
    > "$REPO/runs/p16_score_$name.log" 2>&1; local sc=$?
  local line; line=$(tail -1 "$REPO/runs/p16_score_$name.log" | cut -c1-400)
  step "score $name exit=$sc: $line"
  runlog "**$name** ($desc): $mins min for $todo new year(s); $line"
  record "$name scored"
}
while IFS='|' read -r q name exp ov desc; do
  q=$(echo "$q" | xargs); [ "$q" = "$Q" ] || continue
  run_entry "$(echo "$name" | xargs)" "$(echo "$exp" | xargs)" "$(echo "$ov" | xargs)" "$(echo "$desc" | xargs)"
done < <(grep -v '^\s*#' "$QUEUES")
touch "$REPO/runs/p16_queue_$Q.done"; step "queue $Q finished; $(remaining_min) min left"

# ---- queue D waits for A, B and C, then runs the cross-run diagnostics
n=0; until [ -f runs/p16_queue_A.done ] && [ -f runs/p16_queue_B.done ] && [ -f runs/p16_queue_C.done ]; do
  [ $((n % 12)) -eq 0 ] && step "waiting for queues A/B/C to finish"; n=$((n + 1)); sleep 300
  [ "$(remaining_min)" -gt 0 ] || { step "budget exhausted while waiting for A/B/C - final diagnostics not run"; break; }
done
if true; then
  export JAX_PLATFORMS=cpu
  step "final diagnostics (last queue): phase12_compare of every run vs base10, aoa_vs_clams for the mixing runs"
  base="runs/p16_base_10yr"; final="$OUT/final"; mkdir -p "$final"
  if [ -d "$base" ]; then
    for r in mix10 mix30 qbonarrow hdiff2 slit2 n100_10 n100mix10 mix10trop; do
      [ -d "runs/p16_${r}_10yr" ] || continue
      python scripts/phase12_compare.py --before "$base" --after "runs/p16_${r}_10yr" --tag "${r}_vs_base" --stride 1 --last-days 60 \
        --label "Phase 16 $r vs the ten-year base (ray30+n100), 1990-1999" --before-label "base10" --after-label "$r" \
        --clocks aoa_sfc aoa500 aoa150 --out "$final" > "$REPO/runs/p16_compare_$r.log" 2>&1 &
      # at most three compares at once (each reads two 10-yr archives)
      while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 60; done
    done
    wait
    for r in base10 mix10 mix30 n100_10 n100mix10 mix10trop; do
      [ -d "runs/p16_${r}_10yr" ] || continue
      for v in aoa_sfc aoa150; do
        python scripts/aoa_vs_clams.py "runs/p16_${r}_10yr" "$final" --years 2005-2009 --last-saves 240 --var "$v" \
          --second-run "$P13/p13jucker_5yr" --second-label "Jucker base (5 yr)" \
          --label "P16 $r 1990-1999 [$v]: age after 10 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p16_aoa_${r}_${v}.log" 2>&1 &
      done
    done
    wait
    step "final diagnostics done -> $final"; runlog "final diagnostics written to \`final/\` (\`<run>_vs_base_*\` w*/ages/metrics, \`*_aoa_*\` vs CLaMS)"
  else
    step "no ten-year base - final diagnostics skipped"; runlog "final diagnostics skipped: no ten-year base"
  fi
  sed -i 's/| \*\*running\*\* (three GPU queues)/| **done** (see the leaderboard in the record)/' PROGRESS.md
  record "finished"; step "finished"
fi

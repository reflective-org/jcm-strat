#!/usr/bin/env bash
# Phase 22 confirmation of a track's best correction: the full 1990-2009 run from the 1989-12 spin-up (as P20b), so the clocks
# reflect only the new circulation, scored on the iteration window (2005-04..2007-12, comparable with the iterations) and with
# the vortex / seasonal age / age-vs-CLaMS diagnostics on 2005-2009 (as P20b's). Best = lowest u_ls_ext among the track's scores.
#   bash scripts/p22_final.sh T GPU
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
T="${1:?track}"; GPU="${2:?gpu}"; PY="$REPO/.venv/bin/python"
OUT="$REPO/docs/outputs/22_teq_vortex"; SC="$OUT/scores"; CO="$OUT/corrections"; LOG="$REPO/runs/p22_$T.log"; LOCK="$REPO/runs/.p22_git.lock"
DEADLINE=$(cat "$REPO/runs/p22_deadline")
# shellcheck disable=SC1090
source "$REPO/runs/p22_track_$T.env"
step() { echo "[p22 ${T}_final] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
note() { flock "$LOCK" bash -c "echo '- $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') - **${T}_final** $*' >> '$OUT/runlog.md'"; }
best=$(python3 - "$SC" "$T" <<'PY'
import glob, json, os, re, sys
sc, t = sys.argv[1:]
rows = [(json.load(open(f))["u_ls_ext"], os.path.basename(f)[:-5]) for f in glob.glob(os.path.join(sc, f"{t}*.json")) if re.fullmatch(rf"{t}\d+", os.path.basename(f)[:-5])]
print(min(rows)[1] if rows else "")
PY
)
[ -n "$best" ] || { step "no scored iteration of $T"; exit 1; }
i=${best#$T}; corr=""; [ "$i" -gt 0 ] && corr="$CO/$best.nc"
name="${T}_final"; pre="p22_$name"
left=$(( (DEADLINE - $(date +%s)) / 60 ))
[ "$left" -gt 420 ] || { step "SKIP: only $left min to the deadline (needs ~7 h)"; note "skipped for the deadline ($left min left)"; exit 0; }
extra="$OVR"; [ -n "$corr" ] && extra="$extra ++physics.terms.held_suarez.te_correction_file=$corr ++physics.terms.held_suarez.te_correction_mode=$CMODE"
while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do sleep 300; done
step "run $name: 1990-2009 from the 1989-12 spin-up with the best iteration $best (${corr##*/}), overrides ${extra:-none}"; note "started: 1990-2009 with $best"
t1=$(date +%s)
SPINUP="1989-12-01 31" EXPERIMENT=p22_teq PREFIX="$pre" SCHEME=calendar YEARS=1990-2009 AGG="${pre}_20yr" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$extra" \
  bash scripts/chain_segments.sh > "runs/${pre}_chain_stdout.log" 2>&1; rc=$?
bad=$(grep -l 'atmosphere unhealthy' runs/${pre}_*0101/log.txt 2>/dev/null | tr '\n' ' ')
step "chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
if [ $rc -ne 0 ] || [ -n "$bad" ]; then note "**FAILED** (exit $rc ${bad:+health stop})"; exit 1; fi
export JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES=""
D="$OUT/final/$name"; mkdir -p "$D"
"$PY" scripts/teq_score.py "runs/${pre}_20yr" --t0 2005-04-01 --t1 2008-01-01 --name "$name" --desc "$DESC: best iteration $best, 1990-2009 from spin-up" --out "$SC" > "runs/p22_score_$name.log" 2>&1
line=$(grep '^\[score\]' "runs/p22_score_$name.log" | tail -1); step "$line"; note "$line"
"$PY" scripts/vortex_jets.py "runs/${pre}_20yr" "$D" --years 2005-2009 --label "$name" > "runs/p22_${name}_vortex.log" 2>&1
"$PY" scripts/seasonal_age_winds.py "runs/${pre}_20yr" "$D" --years 2005-2009 --label "P22 $name" > "runs/p22_${name}_seasonal.log" 2>&1
for v in aoa150 aoa_sfc; do
  "$PY" scripts/aoa_vs_clams.py "runs/${pre}_20yr" "$D" --years 2005-2009 --last-saves 240 --var "$v" --label "P22 $name [$v] vs CLaMS/WACCM" > "runs/p22_${name}_aoa_$v.log" 2>&1
done
step "diagnostics in $D"; note "diagnostics in \`final/$name/\`"
flock "$LOCK" bash -c "cd '$REPO' && '$PY' scripts/p22_leaderboard.py '$OUT' >/dev/null 2>&1; git add '$OUT' >/dev/null 2>&1; git add -f '$SC'/*.json >/dev/null 2>&1; git commit -q -m 'Phase 22: $name' >/dev/null 2>&1" 

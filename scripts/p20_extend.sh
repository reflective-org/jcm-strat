#!/usr/bin/env bash
# Phase 20 extension (Susanne 2026-10-08): continue p20jhsso from 1997 through 2011 with the 11a tracers written
# (experiment p20_ext), one calendar year per chain_segments.sh call so every year gets a disk check and, if jcm's
# health check stops it, ONE rescue:
#   rescue = rerun from the segment's last healthy checkpoint (the checkpoint is written only after a passing chunk) to
#   the end of that calendar year at run.time_step=6 instead of 12 min, nothing else changed (Susanne: "rerunning the
#   few days before it at a 6 min interval"). The failed segment is kept as <seg>_part1, the rescue run as <seg>_rescue,
#   and <seg> is rebuilt from links (part1 chunk files up to the healthy day + rescue chunk files renumbered after it,
#   the rescue checkpoint) so the chain and every analysis see one complete year. A second health stop in the same
#   year, a failed rescue or a crash stops the extension.
# Afterwards: aggregate runs/p20jhsso_22yr, seasonal age + wind plots (2005-2009, CLaMS/WACCM/ERA5 overlap) and the
# Phase 12 comparison of the aggregate's last 5 years. Log runs/p20_ext.log.
#   tmux new-session -d -s strat_p20_ext 'GPU=1 bash scripts/p20_extend.sh'
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${GPU:-1}"; PREFIX=p20jhsso; EXP=p20_ext; Y_FIRST=1990; Y_LAST="${Y_LAST:-2011}"; AGG=${PREFIX}_22yr
RESCUE_DT=6; MIN_FREE_GB="${MIN_FREE_GB:-500}"
OUT=/data/JCM_stripped/jcm-strat-phase20/docs/outputs/20_sso_fixed/extension
LOG="$REPO/runs/p20_ext.log"; mkdir -p "$OUT"
say() { echo "[p20-ext] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
export CUDA_VISIBLE_DEVICES="$GPU"

last_ok_day() { grep -oE 'Day [0-9]+ \([0-9.]+ yr\) \| OK' "$1/log.txt" | tail -1 | awk '{print $2}'; }

rescue() {     # $1 = runs/<PREFIX>_<YYYY>0101 stopped on a health check
  local seg="$1" y; y="$(basename "$seg" | sed -E 's/.*_([0-9]{4})0101$/\1/')"
  local part1="${seg}_part1" r="${seg}_rescue"
  local src="$seg"
  if [ -e "$part1" ]; then
    # a rescue that was interrupted (node reboot) left part1 and no rebuilt $seg: redo the rescue from part1
    [ -e "$seg" ] && { say "FAIL: $y already had a rescue and stopped again - not retrying"; return 1; }
    src="$part1"; say "resuming the interrupted rescue of $y from $part1"
  fi
  local D; D="$(last_ok_day "$src")"; [ -n "$D" ] || { say "FAIL: no healthy chunk in $src"; return 1; }
  local ndays start rem
  ndays=$(python3 -c "import datetime as d; print((d.date($y+1,1,1)-d.date($y,1,1)).days)")
  start=$(python3 -c "import datetime as d; print(d.date($y,1,1)+d.timedelta(days=$D))"); rem=$(( ndays - D ))
  say "rescue $y: last healthy day $D ($start), rerun $rem d at run.time_step=$RESCUE_DT from its checkpoint"
  [ "$src" = "$part1" ] || mv "$seg" "$part1"; rm -rf "$r"; mkdir -p "$r"
  echo "[launch] $(date -Is) rescue of $part1 from day $D at dt=$RESCUE_DT GPU=$GPU" >> "$r/log.txt"
  ( cd "$r" && python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$EXP" ++run.checkpoint_path=checkpoint.ckpt \
      "run.start_time=$start" "run.total_time=$rem" "run.time_step=$RESCUE_DT" "physics.terms.held_suarez.qbo.year=$y" \
      init=from_state "init.file=$part1/checkpoint.ckpt" hydra.run.dir="$r" ) >> "$r/log.txt" 2>&1
  local rc=$?
  if [ $rc -ne 0 ] || grep -q "atmosphere unhealthy" "$r/log.txt"; then say "FAIL: rescue of $y (exit $rc, $(grep -m1 'atmosphere unhealthy' "$r/log.txt"))"; return 1; fi
  mkdir -p "$seg"
  for f in "$part1"/longrun_day*.nc; do
    n=$(basename "$f" | sed -E 's/longrun_day([0-9]+)\.nc/\1/'); [ "$n" -le "$D" ] || continue
    ln -s "$f" "$seg/longrun_day$n.nc"; [ -e "$f.provenance.json" ] && ln -s "$f.provenance.json" "$seg/longrun_day$n.nc.provenance.json"
  done
  for f in "$r"/longrun_day*.nc; do
    m=$(basename "$f" | sed -E 's/longrun_day([0-9]+)\.nc/\1/')
    ln -s "$f" "$seg/longrun_day$((D + m)).nc"; [ -e "$f.provenance.json" ] && ln -s "$f.provenance.json" "$seg/longrun_day$((D + m)).nc.provenance.json"
  done
  cp "$r/checkpoint.ckpt" "$seg/checkpoint.ckpt"
  { echo "[rescue] $y = $part1 days 1-$D (12-min step) + $r days $((D + 1))-$ndays (6-min step); the health stop of part1 is kept there"
    sed 's/atmosphere unhealthy/atmosphere UNHEALTHY (rescued, see header)/' "$part1/log.txt"
    cat "$r/log.txt"; echo "[launch] $(date -Is) exit=0"; } > "$seg/log.txt"
  say "rescue $y done: $(ls "$seg"/longrun_day*.nc | wc -l) chunk files linked into $seg"
  ( JAX_PLATFORMS=cpu nohup python "$REPO/scripts/compact_run.py" "$part1" >> "$part1/compact.log" 2>&1 & )
  return 0
}

say "start: $PREFIX $Y_FIRST-$Y_LAST on GPU $GPU, experiment $EXP, commit $(git rev-parse --short HEAD)"
for y in $(seq 1997 "$Y_LAST"); do
  seg="$REPO/runs/${PREFIX}_${y}0101"
  if grep -q '\[launch\].*exit=0' "$seg/log.txt" 2>/dev/null && ! grep -q "atmosphere unhealthy" "$seg/log.txt"; then continue; fi
  # 1997 already stopped on the health check (2026-10-07): rescue it directly instead of rerunning the whole year
  if [ -d "$seg" ] && grep -q "atmosphere unhealthy" "$seg/log.txt" 2>/dev/null; then rescue "$seg" || exit 1; continue; fi
  if [ ! -e "$seg" ] && [ -d "${seg}_part1" ]; then rescue "$seg" || exit 1; continue; fi
  free=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9)
  [ "$free" -ge "$MIN_FREE_GB" ] || { say "FAIL: only ${free} GB free on /data (< $MIN_FREE_GB) before $y - stopping"; exit 1; }
  say "year $y (free ${free} GB)"
  SPINUP="1989-12-01 31" EXPERIMENT=$EXP PREFIX=$PREFIX SCHEME=calendar YEARS="$Y_FIRST-$y" AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
    bash scripts/chain_segments.sh >> "$REPO/runs/${PREFIX}_chain_stdout.log" 2>&1
  if grep -q '\[launch\].*exit=0' "$seg/log.txt" 2>/dev/null && ! grep -q "atmosphere unhealthy" "$seg/log.txt"; then continue; fi
  if grep -q "atmosphere unhealthy" "$seg/log.txt" 2>/dev/null; then
    say "$y stopped on the health check: $(grep -m1 'atmosphere unhealthy' "$seg/log.txt")"; rescue "$seg" || exit 1
  else
    say "FAIL: $y did not finish and was not a health stop (see runs/${PREFIX}_chain.log)"; exit 1
  fi
done
say "all years done; linking runs/$AGG"
LINK_ONLY=1 SPINUP="1989-12-01 31" EXPERIMENT=$EXP PREFIX=$PREFIX SCHEME=calendar YEARS="$Y_FIRST-$Y_LAST" AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash scripts/chain_segments.sh >> "$REPO/runs/${PREFIX}_chain_stdout.log" 2>&1 || { say "FAIL: linking"; exit 1; }

export JAX_PLATFORMS=cpu
python scripts/seasonal_age_winds.py "runs/$AGG" "$OUT" --years 2005-2009 --label "P20 fixed Lott-Miller" > runs/p20_ext_seasonal.log 2>&1
say "seasonal age + winds 2005-2009 exit=$?"
python scripts/strat_compare.py "$OUT" --run "P20=runs/$AGG" --years 2005-2009 > runs/p20_ext_strat_compare.log 2>&1
say "strat_compare 2005-2009 exit=$?"
for v in aoa150 aoa_sfc; do
  python scripts/aoa_vs_clams.py "runs/$AGG" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P20 fixed Lott-Miller 1990-$Y_LAST [$v]: age at the end vs CLaMS/WACCM" > "runs/p20_ext_aoa_$v.log" 2>&1
  say "aoa $v exit=$?"
done
git -C /data/JCM_stripped/jcm-strat-phase20 add docs/outputs/20_sso_fixed/extension && \
  git -C /data/JCM_stripped/jcm-strat-phase20 commit -q -m "Phase 20 extension to $Y_LAST: seasonal age and wind diagnostics" && say "committed"
say "finished"

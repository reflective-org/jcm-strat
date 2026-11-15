#!/usr/bin/env bash
# AL7h 1970-2022 (Susanne 2026-11-14): AL7h on every segment, all real ERA5 - no recycling. The WB2 ERA5 store runs
# 1959-01-01 .. 2023-01-10, so the last full calendar year is 2022 (the run ends 2023-01-01, 53 years). Otherwise exactly
# p31_AL7h50 (scripts/phase31_50yr.sh): experiment p20b_ext (all tracers written), the AL7h T_e correction, QBO tau 1 d with
# the target = the model year, 31-day spin-up from ERA5 (here 1969-12-01), production tracers injected on 1970-01-01.
# No matching run without AL7h (Susanne: "we just want AL7h").
#
# Three streams, so the GPU does not wait for all the CPU preparation:
#   1. CDS: monthly zonal-mean u/T 1969-1988 for the QBO target (cache/era5_ref has 1989-2022)  -> runs/<P>_qboref.log
#   2. CPU: nudging windows, spin-up month (+ initial state 1969-12-01), then 1970..1989 one year at a time, under
#      memcap (one year peaks ~184 GB RSS), retried; a marker runs/<P>_prefetch/<tag>.ok after each   -> runs/<P>_prefetch.log
#   3. GPU: the chain, extended one year at a time as soon as that year's window and QBO year are on disk; from 1990 on
#      everything is cached and the rest runs in one call. chain_segments skips finished segments.
# A health stop or a failed stream ends the pipeline. Restartable.
#   tmux new-session -d -s train_p31_al7h70 'GPU=0 bash scripts/phase31_al7h70.sh'      log runs/p31_AL7h70.log
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${GPU:-0}"; P=p31_AL7h70; AGG=p31_AL7h70_1970_2022; EXP=p20b_ext; Y0=1970; Y1=2022; PF_LAST=1989
LOG="$REPO/runs/$P.log"; PFLOG="$REPO/runs/${P}_prefetch.log"; QLOG="$REPO/runs/${P}_qboref.log"; MK="$REPO/runs/${P}_prefetch"
MIN_FREE_GB="${MIN_FREE_GB:-12000}"; mkdir -p "$MK"
CORR="$REPO/docs/outputs/25_al7_half/corrections/AL7h.nc"
EXTRA="++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total"
step() { echo "[p31-AL7h70] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
fail() { step "FAILED: $*"; kill $(jobs -p) 2>/dev/null; exit 1; }
free=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9)
[ "$free" -ge "$MIN_FREE_GB" ] || fail "only ${free} GB free on /data"
[ -f "$CORR" ] || fail "no correction file $CORR"
step "start, commit $(git rev-parse --short HEAD) (+ working tree), GPU $GPU, free ${free} GB: $P $Y0-$Y1, spin-up 1969-12"

# 1. QBO target years (CDS, small monthly means; the script skips years already on disk)
( bash scripts/memcap.sh -m 16G -- python scripts/fetch_era5_strat_ref.py 1969 1988 --monthly-only >> "$QLOG" 2>&1
  echo "QBOREF_EXIT=$?" >> "$QLOG" ) &

# 2. nudging windows
prefetch() {
  local tag=$1; shift
  [ -f "$MK/$tag.ok" ] && return 0
  for a in 1 2 3; do
    echo "--- $tag attempt $a $(TZ=America/Los_Angeles date '+%m-%d %H:%M')" >> "$PFLOG"
    bash scripts/memcap.sh -m 200G -- env JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 "$@" -- +experiment=$EXP >> "$PFLOG" 2>&1 \
      && { touch "$MK/$tag.ok"; echo "$tag ok $(TZ=America/Los_Angeles date '+%m-%d %H:%M')" >> "$PFLOG"; return 0; }
    echo "$tag attempt $a failed" >> "$PFLOG"; sleep 600
  done
  touch "$MK/$tag.failed"; return 1
}
( prefetch spinup --years 1969 --start 1969-12-01 --days 31 || exit 1
  for y in $(seq $Y0 $PF_LAST); do prefetch "$y" --scheme calendar --save-interval 0.25 --years "$y-$y" --no-init || exit 1; done ) &

# 3. the chain
qbo_ready() { [ -f "cache/era5_ref/era5_zm_monthly_$1.nc" ] && { [ "$1" -gt 1988 ] || grep -q -E "^\[.*\] $1 monthly: (wrote|present)" "$QLOG" 2>/dev/null; }; }
wait_for() {   # $1 = model year, $2 = prefetch tag
  until [ -f "$MK/$2.ok" ] && qbo_ready "$1" && { [ "$1" = 1969 ] || qbo_ready 1969; }; do
    [ -f "$MK/$2.failed" ] && fail "prefetch of $2 failed ($PFLOG)"
    grep -q '^QBOREF_EXIT=[1-9]' "$QLOG" 2>/dev/null && ! qbo_ready "$1" && fail "QBO reference fetch failed ($QLOG)"
    sleep 120
  done
}
chain() {      # extend the chain to the end of model year $1
  while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy, waiting"; sleep 300; done
  SPINUP="1969-12-01 31" EXPERIMENT=$EXP PREFIX=$P SCHEME=calendar YEARS="$Y0-$1" AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
    EXTRA="$EXTRA" bash scripts/chain_segments.sh >> "runs/${P}_chain_stdout.log" 2>&1
  local rc=$? bad; bad=$(grep -l 'atmosphere unhealthy' runs/${P}_*/log.txt 2>/dev/null | tr '\n' ' ')
  [ $rc -eq 0 ] && [ -z "$bad" ] || fail "chain to $1 exit=$rc ${bad:+HEALTH STOP: $bad} (runs/${P}_chain.log)"
}
t1=$(date +%s)
wait_for 1969 spinup
for y in $(seq $Y0 $PF_LAST); do wait_for "$y" "$y"; step "inputs for $y ready, chain to $y"; chain "$y"; done
step "all inputs cached from 1990 on, chain to $Y1"; chain $Y1
step "chain exit=0 after $(( ($(date +%s) - t1) / 60 )) min, no health stops"
wait
touch "runs/$P.done"
step "finished -> runs/$AGG"

# Phase 19-21 shared helpers, sourced by scripts/phase19_run.sh, phase20_run.sh, phase21_run.sh.
# Never edit while a pipeline that sourced it is running (bash reads sourced files once, but keep the rule).
REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
export PYTHONUNBUFFERED=1

pdt() { TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z'; }

# gpu_free <n>: no compute process on GPU n
gpu_free() { ! nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }

# wait_gpu <n>: block until GPU n is free (another user's job may hold it)
wait_gpu() { until gpu_free "$1"; do sleep 120; done; }

# smoke <experiment> <name> <gpu> [overrides...]: 5 days from 1990-01-01 (ERA5), first_segment=true, checks the run header
# and the output. Writes runs/<name>/ and returns non-zero on failure.
smoke() {
  local exp="$1" name="$2" gpu="$3"; shift 3
  local rundir="$REPO/runs/$name"
  if grep -q '\[launch\].*exit=0' "$rundir/log.txt" 2>/dev/null && [ -f "$rundir/smoke_check.txt" ] && grep -q "^RESULT PASS" "$rundir/smoke_check.txt"; then
    echo "[smoke] $name already passed"; return 0
  fi
  rm -rf "$rundir"; mkdir -p "$rundir"
  echo "[launch] $(date -Is) jcm-strat $(git -C "$REPO" rev-parse --short HEAD) smoke GPU=$gpu" >> "$rundir/log.txt"
  ( cd "$rundir" && CUDA_VISIBLE_DEVICES="$gpu" python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$exp" \
      ++run.checkpoint_path=checkpoint.ckpt run.start_time=1990-01-01 run.total_time=5 run.chunk_days=5 \
      physics.terms.production_tracers.first_segment=true "$@" hydra.run.dir="$rundir" ) >> "$rundir/log.txt" 2>&1
  local rc=$?; echo "[launch] $(date -Is) exit=$rc" >> "$rundir/log.txt"
  [ $rc -eq 0 ] || { echo "[smoke] $name FAILED exit=$rc (see $rundir/log.txt)"; return 1; }
  JAX_PLATFORMS=cpu python "$REPO/scripts/p19_smoke_check.py" "$rundir" > "$rundir/smoke_check.txt" 2>&1
  local rc2=$?; cat "$rundir/smoke_check.txt"; return $rc2
}

# writeup_agent <prompt file> <log>: headless write-up / diagnose agent (the brief's last pipeline step)
run_agent() {
  local prompt="$1" log="$2"
  echo "[agent] $(pdt) start $prompt" >> "$log"
  ( cd /data/JCM_stripped && claude -p "$(cat "$prompt")" --model claude-opus-5-5 --dangerously-skip-permissions \
      --output-format stream-json --verbose >> "$log" 2>&1 )
  echo "[agent] $(pdt) exit $?" >> "$log"
}

PROMPTS="$REPO/scripts/p19_prompts"

# writeup_agent <NN>: runs/pNN_writeup_prompt.md = common rules + the phase's write-up prompt, then the headless agent
writeup_agent() {
  local nn="$1" pf="$REPO/runs/p$1_writeup_prompt.md"
  cat "$PROMPTS/writeup_p$nn.md" "$PROMPTS/common_rules.md" > "$pf"
  run_agent "$pf" "$REPO/runs/p${nn}_writeup.log"
}

# failure_agent <NN> <message> <script> <log> <relaunch command>: diagnose / fix if mechanical / relaunch once
failure_agent() {
  local nn="$1" msg="$2" script="$3" log="$4" relaunch="$5" pf="$REPO/runs/p$1_failure_prompt.md"
  python3 - "$PROMPTS/failure.md" "$pf" "$nn" "$msg" "$script" "$log" "${RELAUNCHED:-0}" "$relaunch" <<'PY'
import sys
src, dst, nn, msg, script, log, rel, cmd = sys.argv[1:]
t = open(src).read()
for k, v in (("{PHASE}", nn), ("{MSG}", msg), ("{SCRIPT}", script), ("{LOG}", log), ("{RELAUNCHED}", rel), ("{RELAUNCH}", cmd)):
    t = t.replace(k, v)
open(dst, "w").write(t)
PY
  cat "$PROMPTS/common_rules.md" >> "$pf"
  run_agent "$pf" "$REPO/runs/p${nn}_failure_agent.log"
}

# link_first_years <src aggregate> <dst dir> <ndays>: a 5-yr view of an older 10-yr aggregate (cumulative day numbers)
link_first_days() {
  local src="$1" dst="$2" ndays="$3" f n
  mkdir -p "$dst"; rm -f "$dst"/longrun_day*.nc
  for f in "$src"/longrun_day*.nc; do
    n=$(basename "$f" | sed -E 's/longrun_day([0-9]+)\.nc/\1/')
    [ "$n" -le "$ndays" ] && ln -s "$(readlink -f "$f")" "$dst/longrun_day$n.nc"
  done
  [ -d "$src/.hydra" ] && cp -r "$src/.hydra" "$dst/" 2>/dev/null
  echo "$(ls "$dst"/longrun_day*.nc | wc -l) files linked from $src (day <= $ndays)"
}

# wait_file <path> <max hours>: block until the file exists
wait_file() { local i=0; until [ -e "$1" ]; do sleep 120; i=$((i + 1)); [ $i -gt $(( $2 * 30 )) ] && return 1; done; return 0; }

# wait_chain_finished <prefix> <max hours>
wait_chain() { local i=0; until grep -q "chain finished" "$REPO/runs/$1_chain.log" 2>/dev/null; do
  tail -1 "$REPO/runs/$1_chain.log" 2>/dev/null | grep -q "FAILED - stopping\|refusing" && return 2
  sleep 300; i=$((i + 1)); [ $i -gt $(( $2 * 12 )) ] && return 1; done; return 0; }

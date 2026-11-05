#!/usr/bin/env bash
# Run a command under a hard memory cap (Susanne 2026-10-22: the node went down when four analysis processes
# each loaded 18 years of output at once).
#
#   bash scripts/memcap.sh [-m PER_JOB] -- command args...      e.g. bash scripts/memcap.sh -m 64G -- python scripts/x.py ...
#
# Two limits, both cgroup v2 via the systemd user manager (no root needed):
#   PER_JOB  (-m, default $MEMCAP_JOB or 96G): MemoryMax of this command's own scope; only this command is killed
#            (exit 137) when it goes over.
#   TOTAL    ($MEMCAP_TOTAL, default 256G): MemoryMax of the shared slice jcmcpu.slice that every memcap'd command
#            runs in, so parallel jobs together cannot exceed it either. Re-applied on every call (it does not
#            survive a reboot).
# Swap is disabled inside both, so a job over its limit is killed instead of thrashing.
set -euo pipefail
JOB="${MEMCAP_JOB:-96G}"; TOTAL="${MEMCAP_TOTAL:-256G}"
if [ "${1:-}" = "-m" ]; then JOB="$2"; shift 2; fi
[ "${1:-}" = "--" ] && shift
[ $# -gt 0 ] || { echo "usage: memcap.sh [-m PER_JOB] -- command ..." >&2; exit 2; }
systemctl --user set-property --runtime jcmcpu.slice MemoryMax="$TOTAL" MemorySwapMax=0
exec systemd-run --user --scope -q --slice=jcmcpu.slice -p MemoryMax="$JOB" -p MemorySwapMax=0 -- "$@"

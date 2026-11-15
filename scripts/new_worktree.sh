#!/usr/bin/env bash
# Create a worktree for a phase/feature branch next to the main checkout (Susanne 2026-11-15, after cleaning up
# 25 worktrees whose runs/, cache and venv were chained worktree -> worktree -> worktree).
#
#   bash scripts/new_worktree.sh <branch> [<base>]       base defaults to origin/dev; an existing branch is checked out
#
# -> /data/JCM_stripped/jcm-strat-<branch>, with .venv, cache, runs and scratch symlinked STRAIGHT to the main
#    checkout's real directories (never to another worktree), so every run lands in the one runs/ and removing the
#    worktree later (scripts/drop_worktree.sh) cannot take data with it.
# The shared venv imports jcm from the main checkout's external/jax-gcm; jcm_strat resolves to this worktree's copy
# when run from here (python -m / scripts cd to $REPO). If the branch pins a different jax-gcm, the venv does not follow
# it: that is reported below and needs its own venv.
set -euo pipefail
[ $# -ge 1 ] || { sed -n '2,8p' "$0"; exit 2; }
BR="$1"; BASE="${2:-origin/dev}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$(cd "$HERE" && cd "$(git rev-parse --git-common-dir)" && pwd)"
MAIN="$(dirname "$COMMON")"
DIR="$(dirname "$MAIN")/jcm-strat-$BR"

for x in .venv cache runs scratch; do
  [ -d "$MAIN/$x" ] && [ ! -L "$MAIN/$x" ] || { echo "main checkout $MAIN/$x is not a real directory - refusing to chain" >&2; exit 1; }
done
[ ! -e "$DIR" ] || { echo "$DIR already exists" >&2; exit 1; }
if git -C "$MAIN" worktree list --porcelain | grep -qx "branch refs/heads/$BR"; then
  echo "branch $BR is already checked out:" >&2; git -C "$MAIN" worktree list | grep "\[$BR\]" >&2; exit 1
fi

git -C "$MAIN" fetch -q origin
if git -C "$MAIN" show-ref -q --verify "refs/heads/$BR"; then
  git -C "$MAIN" worktree add -q "$DIR" "$BR"
else
  git -C "$MAIN" worktree add -q -b "$BR" "$DIR" "$BASE"
fi
for x in .venv cache runs scratch; do ln -s "$MAIN/$x" "$DIR/$x"; done

want=$(git -C "$DIR" ls-tree HEAD external/jax-gcm | awk '{print $3}')
have=$(git -C "$MAIN/external/jax-gcm" rev-parse HEAD)
[ "$want" = "$have" ] || echo "WARNING: $BR pins jax-gcm ${want:0:9} but the shared venv runs ${have:0:9} (main checkout)" >&2

echo "worktree $DIR  [$BR]  (.venv cache runs scratch -> $MAIN)"
echo "remove it when its PR is merged:  bash $MAIN/scripts/drop_worktree.sh $BR"

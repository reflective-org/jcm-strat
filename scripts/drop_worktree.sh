#!/usr/bin/env bash
# Remove a worktree made by scripts/new_worktree.sh once its work is safe (Susanne 2026-11-15).
#
#   bash scripts/drop_worktree.sh <branch | worktree path> [--delete-branch]
#
# Refuses unless ALL of these hold, and says which one failed:
#   - it is not the main checkout, and no process is working inside it
#   - no uncommitted or untracked files
#   - HEAD is on GitHub (contained in some origin/* branch), so no commit exists only here
#   - .venv, cache, runs and scratch are symlinks or absent - `git worktree remove` deletes ignored files, so a real
#     runs/ here would be deleted with it (this is how old worktrees held TBs of runs)
#   - nothing else is ignored except Python caches (anything else is listed; move it first)
# Then unlinks the four symlinks (never following them) and removes the worktree. --delete-branch also deletes the
# local branch, but only if it is merged into origin/dev.
set -euo pipefail
[ $# -ge 1 ] || { sed -n '2,13p' "$0"; exit 2; }
ARG="$1"; DELBR=0; [ "${2:-}" = "--delete-branch" ] && DELBR=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMON="$(cd "$HERE" && cd "$(git rev-parse --git-common-dir)" && pwd)"
MAIN="$(dirname "$COMMON")"
if [ -d "$ARG" ]; then DIR="$(cd "$ARG" && pwd)"; else DIR="$(dirname "$MAIN")/jcm-strat-$ARG"; fi
die() { echo "REFUSED ($DIR): $*" >&2; exit 1; }

[ -d "$DIR" ] || die "no such worktree"
[ "$DIR" != "$MAIN" ] || die "that is the main checkout"
git -C "$MAIN" worktree list --porcelain | grep -qx "worktree $DIR" || die "not a worktree of $MAIN"
BR="$(git -C "$DIR" branch --show-current)"

busy=$(for p in /proc/[0-9]*; do c=$(readlink "$p/cwd" 2>/dev/null) || continue
         case "$c/" in "$DIR"/*) echo "${p#/proc/} $(cat "$p/comm" 2>/dev/null)";; esac; done)
[ -z "$busy" ] || die "processes are working inside it:"$'\n'"$busy"

dirty=$(git -C "$DIR" status --porcelain)
[ -z "$dirty" ] || die "uncommitted/untracked files:"$'\n'"$dirty"

git -C "$MAIN" fetch -q origin
[ -n "$(git -C "$DIR" branch -r --contains HEAD)" ] || die "HEAD $(git -C "$DIR" rev-parse --short HEAD) is not on GitHub - push it first"

for x in .venv cache runs scratch; do
  [ ! -e "$DIR/$x" ] || [ -L "$DIR/$x" ] || die "$x is a real directory, not a symlink - move its contents to $MAIN/$x first"
done
other=$(git -C "$DIR" status --porcelain --ignored | sed -n 's/^!! //p' \
        | grep -vxE '\.venv|cache|runs|scratch' | grep -vE '(^|/)(__pycache__|\.pytest_cache|[^/]*\.egg-info)/$' || true)
[ -z "$other" ] || die "ignored files that would be deleted:"$'\n'"$other"

for x in .venv cache runs scratch; do if [ -L "${DIR:?}/$x" ]; then rm -- "${DIR:?}/$x"; fi; done
if git -C "$DIR" submodule status 2>/dev/null | grep -q '^[ +U]'; then
  for s in $(git -C "$DIR" submodule status | awk '{print $2}'); do
    [ -z "$(git -C "$DIR/$s" status --porcelain 2>/dev/null)" ] || die "submodule $s has local changes"
  done
  git -C "$MAIN" worktree remove --force "$DIR"      # needed for any worktree with initialised submodules (checked clean)
else
  git -C "$MAIN" worktree remove "$DIR"
fi
echo "removed $DIR"
if [ "$DELBR" = 1 ] && [ -n "$BR" ]; then
  if git -C "$MAIN" merge-base --is-ancestor "$BR" origin/dev; then
    echo "deleting merged branch $BR ($(git -C "$MAIN" rev-parse --short "$BR"))"; git -C "$MAIN" branch -D -q "$BR"
  else
    echo "kept branch $BR: not merged into origin/dev"
  fi
fi

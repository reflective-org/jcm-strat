# Shared by the phase9_*.sh scripts: read scripts/phase9_matrix.txt and split a row into
# PREFIX / SCHEME / EXPERIMENT / EXTRA. Source after env.sh.
#   matrix_rows [prefix...]        -> prints the matching rows (all rows if no prefix given)
#   parse_row "<row>"              -> sets PREFIX SCHEME EXPERIMENT EXTRA
P9_MATRIX="$REPO/scripts/phase9_matrix.txt"
P9_MARKER_DIR="$REPO/cache/era5"

matrix_rows() {
  grep -v '^\s*#' "$P9_MATRIX" | grep -v '^\s*$' | while read -r line; do
    if [ $# -eq 0 ]; then echo "$line"; continue; fi
    for want in "$@"; do [ "${line%% *}" = "$want" ] && echo "$line"; done
  done
}

parse_row() {
  read -r PREFIX SCHEME rest <<< "$1"
  EXPERIMENT=""; EXTRA=""
  for tok in $rest; do
    case "$tok" in +experiment=*) EXPERIMENT="${tok#+experiment=}";; *) EXTRA="${EXTRA:+$EXTRA }$tok";; esac
  done
  [ -n "$EXPERIMENT" ] || { echo "row without +experiment: $1" >&2; return 1; }
}

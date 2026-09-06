#!/usr/bin/env bash
# rulial-markets — fresh clone to running demo, one command.
#
#   ./scripts/bootstrap.sh          install, build data if missing, run the demo
#   ./scripts/bootstrap.sh --no-run install and build data, then stop
#   ./scripts/bootstrap.sh --rebuild-data  force a data rebuild even if present
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RUN=1
REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --no-run)        RUN=0 ;;
    --rebuild-data)  REBUILD=1 ;;
    -h|--help)       sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
die() { printf '\n\033[31mERROR: %s\033[0m\n' "$1" >&2; exit 1; }

# --- 0. prerequisites --------------------------------------------------------
say "checking prerequisites"
command -v python3 >/dev/null || die "python3 not found. Install Python 3.10+."
PYV="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
  || die "python3 is $PYV; this project needs 3.10+."
echo "    python3 $PYV  ($(command -v python3))"
if command -v node >/dev/null; then
  echo "    node $(node -v)"
else
  echo "    node NOT FOUND — backend will run, frontend will not."
fi

# --- 1. dependencies ---------------------------------------------------------
say "installing dependencies (make install)"
make install

# --- 2. dataset --------------------------------------------------------------
# Price CSVs and the event ledger are committed to the repo, so a normal clone
# already has them and this step is a no-op. It only does real work on a fresh
# dataset or when --rebuild-data is passed.
if [[ "$REBUILD" == "1" ]]; then
  say "rebuilding dataset (--rebuild-data)"
  make data
elif [[ -f data/events.jsonl && -n "$(ls -A data/prices 2>/dev/null || true)" ]]; then
  say "dataset already present — skipping build"
  echo "    data/prices: $(ls data/prices | wc -l | tr -d ' ') files"
  echo "    data/events.jsonl: $(wc -l < data/events.jsonl | tr -d ' ') events"
  echo "    (force a rebuild with: ./scripts/bootstrap.sh --rebuild-data)"
else
  say "building dataset (make data) — this hits the network"
  make data
fi

# --- 3. tests ----------------------------------------------------------------
say "running tests (make test)"
make test || echo "    tests failed — continuing so you can still see the demo"

# --- 4. run ------------------------------------------------------------------
if [[ "$RUN" == "0" ]]; then
  say "done (--no-run). Start it yourself with: make demo"
  exit 0
fi

say "starting demo"
echo "    api: http://127.0.0.1:8000/api/health"
echo "    ui:  http://localhost:3000"
echo "    Ctrl-C stops both."
exec make demo

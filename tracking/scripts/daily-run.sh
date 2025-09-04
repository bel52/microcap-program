#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Reconcile and update positions for today, then chart
./scripts/trade_tracker.py reconcile --date today
./scripts/trade_tracker.py update-positions --date today
python3 ./scripts/chart_equity_vs_bench.py
echo "Done. See data/reports/ for outputs."

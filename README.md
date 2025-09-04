# microcap-tracker

A small, auditable toolkit to **track daily research recommendations**, **record your actual broker fills**, **reconcile** the two (slippage/partials/misses), **maintain positions**, and **chart an equity curve** versus benchmarks (SPY/IWM/IWC). Pure Python + CSVs — simple to diff and version.

---

## Built on
- The **InvestOps Central / Micro-Cap Experiment** research workflow.
- The **Micro-Cap Manager Runbook** (see `docs/` for details).  
  > That project handles the **system recommendations**.  
  > This repo adds the **execution layer** (tracking actual trades).

---

## What’s inside
- `scripts/trade_tracker.py` — CLI to log **recommendations** and **fills**, produce a **reconciliation report**, and roll **positions** forward.
- `scripts/chart_equity_vs_bench.py` — charts your **actual equity curve** from fills vs. SPY/IWM/IWC.
- `scripts/daily-run.sh` — convenience wrapper (reconcile → positions → chart).
- `data/` — CSV inputs/outputs (ignored by Git by default to protect privacy).
- `docs/` — optional copy of your Micro-Cap Manager Runbook.

---

## Install
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Daily routine
1. **Record recommendations** (from research system):
   ```bash
   ./scripts/trade_tracker.py log-rec --date today \
     DOUG,buy,2.60,13 \
     PRLD,buy,1.22,27 \
     OSUR,buy,3.21,10
   ```
   Format: `TICKER,action,limit,shares[,note]`

2. **Record fills** (from broker confirmations):
   ```bash
   ./scripts/trade_tracker.py log-fill --date today \
     DOUG,buy,13,2.59 \
     PRLD,buy,27,1.22 \
     OSUR,buy,10,3.21
   ```
   Format: `TICKER,side,qty,avg_price[,order_id][,note]`

3. **Reconcile & update positions**:
   ```bash
   ./scripts/trade_tracker.py reconcile --date today
   ./scripts/trade_tracker.py update-positions --date today
   ```

4. **Chart portfolio vs benchmarks**:
   ```bash
   python scripts/chart_equity_vs_bench.py
   ```
   Output → `data/reports/equity_vs_benchmarks.png`

---

## File outputs
- `data/recs/YYYY-MM-DD.csv` — system recs (“what you intended”)
- `data/fills/YYYY-MM-DD.csv` — broker fills (“what happened”)
- `data/reports/recon_YYYY-MM-DD.csv` — status + slippage
- `data/positions.csv` — rolling quantity + avg cost
- `data/reports/equity_vs_benchmarks.png` — chart of portfolio vs benchmarks

---

## Privacy & Git
This repo is **privacy-first**: CSVs in `data/` are ignored by default.  
If you want an audit trail, remove the relevant `data/*` lines in `.gitignore`.

---

## Roadmap
- Optional Docker image with `yfinance` baked in.
- Benchmarks configurable via `.env`.
- Automatic EOD run via `cron` or systemd timer.

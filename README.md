# Microcap Program

This project builds upon and extends the excellent work from the original **[microcap-tracker](https://github.com/bel52/microcap-tracker)** repository.  
The upstream project provided the foundation for logging trade recommendations, fills, reconciliations, and equity-vs-benchmark charting.  
This repo reorganizes into a single-tree layout, adds a unified runbook, and integrates daily/weekly user instructions.

---

## 📂 Repository Layout

```
microcap-program/
├── README.md
├── requirements.txt        # Python dependencies
├── scripts/                # Core scripts
│   ├── trade_tracker.py    # Log recs/fills, reconcile, update positions
│   ├── chart_equity_vs_bench.py  # Chart portfolio vs SPY/IWM/IWC
│   └── daily-run.sh        # Automates daily workflow
├── data/                   # Data (ignored in git, placeholders only)
│   ├── .keep
│   ├── recs/               # Daily recommendations (YYYY-MM-DD.csv)
│   ├── fills/              # Executed fills from broker (YYYY-MM-DD.csv)
│   ├── reports/            # Reconciliation + charts
│   └── positions.csv       # Current rolling positions
└── docs/                   # (Optional) project notes and examples
```

---

## ⚙️ Setup

```bash
git clone git@github.com:bel52/microcap-program.git
cd microcap-program
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📝 Workflow

### Daily

- **Pre-open (09:25–10:00 ET):**
  - Place **limit DAY orders** from the weekly CSV (shares, not dollars).
  - Prepare **stop-losses** at the prices specified in the CSV.

- **Intraday:**
  - If a buy fills → set the stop immediately.
  - If a stop triggers → log the SELL with actual price & shares.

- **Post-close (≥16:10 ET):**
  - Cron runs `daily-run.sh`.
  - Check the run log (`run-YYYY-MM-DD.log`).
  - Reconcile fills vs recommendations.
  - Update positions and generate equity-vs-benchmark chart.

### Weekly

- Run Deep Research (separate project).
- Produce **CSV-only target file** with schema:
  ```
  Date,Action,Ticker,Shares,Buy Price,Cost Basis,Stop Loss,Cash Balance
  ```
  - 2–4 tickers + 1 TOTAL row.
  - Cash Balance = Budget − Σ(Cost Basis).
- **Validation rules**:
  - Headers must exactly match schema above.
  - Action = BUY or SELL.
  - Shares = integer, no fractions.
  - Stop Loss = explicit price (no %).
  - TOTAL row required:
    - `Shares` = sum of all tickers’ shares.
    - `Cost Basis` = sum of all tickers’ cost basis.
    - `Cash Balance` = budget left after allocations.
  - Math must balance: **Cost Basis + Cash Balance = Budget.**
- Save as `Start Your Own/chatgpt_portfolio_update.csv`.
- Confirm one post-close run after update.
- Next day: place orders + stops.

---

## 🛠️ Commands

- **Log recommendations**:
  ```bash
  ./scripts/trade_tracker.py log-rec --date today TICKER,buy,limit,shares,note
  ```
- **Log fills**:
  ```bash
  ./scripts/trade_tracker.py log-fill --date today TICKER,buy,shares,avg_price
  ```
- **Reconcile**:
  ```bash
  ./scripts/trade_tracker.py reconcile --date today
  ```
- **Update positions**:
  ```bash
  ./scripts/trade_tracker.py update-positions --date today
  ```
- **Generate chart**:
  ```bash
  python scripts/chart_equity_vs_bench.py
  ```
- **Pipeline**:
  ```bash
  ./scripts/daily-run.sh
  ```

---

## 📊 Outputs

- `data/reports/recon_YYYY-MM-DD.csv` → recs vs fills  
- `data/positions.csv` → current holdings  
- `data/reports/equity_vs_benchmarks.png` → portfolio vs SPY/IWM/IWC  

---

## ⏱️ Automation (Cron)

Installed as:

```cron
10 16 * * 1-5 cd /home/brett/microcap-program-clean && . .venv/bin/activate && ./scripts/daily-run.sh >> /home/brett/microcap-program-clean/run-$(date +\%F).log 2>&1
```

- Runs Mon–Fri at **16:10 ET** (post-close).
- Logs rotate daily.

---

## ⚠️ Stop-Loss & Execution Guidance

- **Stops are prices, not % levels.** Always enter explicit stop values in CSV.  
- **Limit orders** only; **no fractional shares**.  
- **If a stop hits intraday → log SELL immediately** in trade log.  
- **Partial fills**: log separately or as one averaged entry at day end.  

---

## 🔒 Git Ignore Policy

- `.venv/`, `venv/`, `.env*`
- `__pycache__/`, `*.pyc`
- Data: `data/**/*.csv`, `data/positions.csv`, `data/reports/*.csv`, `data/reports/*.png`
- `.DS_Store`, `.idea/`, `.vscode/`
- Keeps `.keep` placeholders

---

## ✅ Summary

This repo is the **single source of truth**:
- Weekly: Deep Research → validated CSV → orders + stops.
- Daily: Place orders, set stops, log fills, cron reconciles.
- Outputs: reconciliation CSV, rolling positions, equity-vs-benchmarks chart.

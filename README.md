# Microcap Program

A self-contained framework to track **microcap trade recommendations, fills, reconciliations, and performance vs benchmarks**.

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

Clone and set up a virtual environment:

```bash
git clone git@github.com:bel52/microcap-program.git
cd microcap-program
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📝 Workflow

1. **Log recommendations** (system output):
   ```bash
   ./scripts/trade_tracker.py log-rec --date YYYY-MM-DD TICKER,action,limit,shares[,note]
   ```
   Example:
   ```bash
   ./scripts/trade_tracker.py log-rec --date today DOUG,buy,2.60,13,daily_pick
   ```

2. **Log fills** (broker executions):
   ```bash
   ./scripts/trade_tracker.py log-fill --date YYYY-MM-DD TICKER,action,shares,avg_price
   ```
   Example:
   ```bash
   ./scripts/trade_tracker.py log-fill --date today DOUG,buy,13,2.59
   ```

3. **Reconcile recs vs fills**:
   ```bash
   ./scripts/trade_tracker.py reconcile --date YYYY-MM-DD
   ```

4. **Update positions**:
   ```bash
   ./scripts/trade_tracker.py update-positions --date YYYY-MM-DD
   ```

5. **Generate chart vs benchmarks**:
   ```bash
   python scripts/chart_equity_vs_bench.py
   ```

6. **Or run the daily pipeline** (steps 3–5):
   ```bash
   ./scripts/daily-run.sh
   ```

---

## 📊 Outputs

- `data/reports/recon_YYYY-MM-DD.csv` → reconciliation of recs vs fills  
- `data/positions.csv` → current holdings  
- `data/reports/equity_vs_benchmarks.png` → equity curve vs SPY/IWM/IWC  

---

## ⏱️ Automation

A cron job runs the daily pipeline automatically **Mon–Fri at 16:10 ET**:

```cron
10 16 * * 1-5 cd /home/brett/microcap-program-clean && . .venv/bin/activate && ./scripts/daily-run.sh >> /home/brett/microcap-program-clean/run-$(date +\%F).log 2>&1
```

- Runs after market close.
- Rotates logs daily (`run-YYYY-MM-DD.log`).

---

## 🔒 Git Ignore Policy

- Virtual environments (`.venv/`, `venv/`, `.env*`)
- Python caches (`__pycache__/`, `*.pyc`)
- Data files (`data/**/*.csv`, `data/positions.csv`, reports `.csv`/`.png`)
- Editor/OS artifacts (`.DS_Store`, `.idea/`, `.vscode/`)
- Keeps placeholders (`data/.keep`, etc.) so directories exist in git.

---

## ✅ Summary

This repo is the **single source of truth** for the full microcap program:
- Research recs in → `data/recs/`
- Executed fills in → `data/fills/`
- Automated reconciliation + positions
- Equity chart vs benchmarks
- Scheduled daily job for end-of-day reporting

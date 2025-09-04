#!/usr/bin/env python3
import glob
from pathlib import Path
from datetime import timedelta
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
FILLS_DIR = DATA / "fills"
REPORTS = DATA / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

BENCH = ["SPY","IWM","IWC"]  # S&P 500, Russell 2000, Micro-Cap ETF

def load_fills():
    files = sorted(glob.glob(str(FILLS_DIR / "*.csv")))
    if not files:
        raise SystemExit("No fills found under data/fills/.")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df["ticker"] = df["ticker"].str.upper()
    df["side"] = df["side"].str.lower()
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    df["avg_price"] = pd.to_numeric(df["avg_price"], errors="coerce")
    return df.sort_values("date")

def build_daily_positions(fills: pd.DataFrame) -> pd.DataFrame:
    tickers = sorted(fills["ticker"].unique().tolist())
    start = fills["date"].min().normalize()
    end = max(pd.Timestamp.today().normalize(), start + pd.Timedelta(days=7))
    days = pd.bdate_range(start - pd.offsets.BDay(1), end + pd.offsets.BDay(1))
    pos = pd.DataFrame(0, index=days, columns=tickers, dtype=int)
    for _, r in fills.iterrows():
        delta = r["qty"] if r["side"].startswith("b") else -r["qty"]
        pos.loc[r["date"].normalize():, r["ticker"]] += delta
    pos = pos.loc[:, (pos != 0).any(axis=0)]
    return pos

def fetch_prices(tickers, start, end):
    df = yf.download(
        tickers, start=start, end=end + timedelta(days=1),
        progress=False, auto_adjust=False, group_by="column"
    )
    if isinstance(df.columns, pd.MultiIndex):
        if "Adj Close" in df.columns.get_level_values(0):
            data = df["Adj Close"].copy()
        elif "Close" in df.columns.get_level_values(0):
            data = df["Close"].copy()
        else:
            raise SystemExit("Neither Adj Close nor Close found.")
    else:
        data = df.copy()
    cols = [t for t in tickers if t in data.columns]
    return data[cols]

def main():
    fills = load_fills()
    positions = build_daily_positions(fills)
    if positions.empty:
        raise SystemExit("No positions to chart.")
    pf_tickers = positions.columns.tolist()
    start, end = positions.index.min(), positions.index.max()
    prices = fetch_prices(sorted(set(pf_tickers + BENCH)), start, end).reindex(positions.index).ffill()

    value = (positions * prices[pf_tickers]).sum(axis=1)
    first = value.first_valid_index()
    value_norm = value / value.loc[first]

    bench_cols = [b for b in BENCH if b in prices.columns]
    bench = prices[bench_cols].copy()
    for c in bench.columns:
        bench[c] = bench[c] / bench[c].iloc[0]

    plt.figure(figsize=(11,6))
    value_norm.plot(label="Portfolio (fills-based)", linewidth=2)
    for c in bench.columns:
        bench[c].plot(label=c, alpha=0.85)
    plt.title("Portfolio vs Benchmarks (normalized to 1.0)")
    plt.xlabel("Date"); plt.ylabel("Growth (×)")
    plt.grid(True, alpha=0.3); plt.legend()
    out = REPORTS / "equity_vs_benchmarks.png"
    plt.tight_layout(); plt.savefig(out, dpi=140)
    print(f"Saved chart: {out}")

if __name__ == "__main__":
    main()

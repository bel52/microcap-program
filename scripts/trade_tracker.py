#!/usr/bin/env python3
import csv, sys, argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parents[1]
DATA = BASE_DIR / "data"
RECS = DATA / "recs"
FILLS = DATA / "fills"
REPORTS = DATA / "reports"
POSITIONS = DATA / "positions.csv"

def ensure_dirs():
    for p in (RECS, FILLS, REPORTS):
        p.mkdir(parents=True, exist_ok=True)

def parse_date(s):
    if s.lower() == "today":
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        print("Date must be YYYY-MM-DD or 'today'", file=sys.stderr); sys.exit(2)

def csv_write(path, rows, header):
    exists = path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)

def csv_read(path):
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))

def float_or_none(x):
    try: return float(x)
    except: return None

def int_or_none(x):
    try: return int(x)
    except: return None

def cmd_log_rec(args):
    d = parse_date(args.date)
    path = RECS / f"{d}.csv"
    header = ["date","ticker","action","limit_price","target_shares","note"]
    rows = []
    for item in args.items:
        parts = item.split(",")
        if len(parts) < 4:
            print("Use TICKER,action,limit,shares[,note]", file=sys.stderr); sys.exit(2)
        ticker = parts[0].strip().upper()
        action = parts[1].strip().lower()
        limit = parts[2].strip()
        shares = parts[3].strip()
        note = ",".join(parts[4:]).strip() if len(parts) > 4 else ""
        rows.append({"date": d, "ticker": ticker, "action": action,
                     "limit_price": limit, "target_shares": shares, "note": note})
    csv_write(path, rows, header)
    print(f"Wrote {len(rows)} recommendation(s) to {path}")

def cmd_log_fill(args):
    d = parse_date(args.date)
    path = FILLS / f"{d}.csv"
    header = ["date","ticker","side","qty","avg_price","timestamp","broker","order_id","note"]
    ts = args.timestamp if args.timestamp else datetime.now().isoformat(timespec="seconds")
    rows = []
    for item in args.items:
        parts = item.split(",")
        if len(parts) < 4:
            print("Use TICKER,side,qty,avg_price[,order_id][,note]", file=sys.stderr); sys.exit(2)
        ticker = parts[0].strip().upper()
        side = parts[1].strip().lower()
        qty = parts[2].strip()
        price = parts[3].strip()
        order_id = parts[4].strip() if len(parts) >= 5 else ""
        note = ",".join(parts[5:]).strip() if len(parts) >= 6 else ""
        rows.append({"date": d, "ticker": ticker, "side": side, "qty": qty,
                     "avg_price": price, "timestamp": ts, "broker": args.broker,
                     "order_id": order_id, "note": note})
    csv_write(path, rows, header)
    print(f"Wrote {len(rows)} fill(s) to {path}")

def load_positions():
    rows = csv_read(POSITIONS)
    pos = defaultdict(lambda: {"ticker":"", "qty":0, "avg_price":0.0})
    for r in rows:
        t = r["ticker"].upper()
        q = int_or_none(r["qty"]) or 0
        p = float_or_none(r["avg_price"]) or 0.0
        pos[t] = {"ticker": t, "qty": q, "avg_price": p}
    return pos

def save_positions(pos):
    header = ["ticker","qty","avg_price"]
    rows = [{"ticker":t, "qty":v["qty"], "avg_price":f"{v['avg_price']:.4f}"} 
            for t,v in sorted(pos.items()) if v["qty"]!=0]
    with POSITIONS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header); w.writeheader()
        for r in rows: w.writerow(r)

def cmd_update_positions(args):
    d = parse_date(args.date)
    fills = csv_read(FILLS / f"{d}.csv")
    if not fills:
        print("No fills to apply for that date."); return
    pos = load_positions()
    for f in fills:
        t = f["ticker"].upper()
        side = f["side"].lower()
        qty = int_or_none(f["qty"]) or 0
        price = float_or_none(f["avg_price"]) or 0.0
        rec = pos[t]
        if side.startswith("b"):
            new_qty = rec["qty"] + qty
            if new_qty <= 0:
                rec["qty"] = 0; rec["avg_price"] = 0.0
            else:
                rec["avg_price"] = (rec["avg_price"]*rec["qty"] + price*qty) / new_qty
                rec["qty"] = new_qty
        elif side.startswith("s"):
            rec["qty"] = max(0, rec["qty"] - qty)
        pos[t] = rec
    save_positions(pos)
    print(f"Updated positions using fills from {d}. See {POSITIONS}")

def cmd_reconcile(args):
    d = parse_date(args.date)
    recs = {(r["ticker"].upper(), r["action"].lower()): r for r in csv_read(RECS / f"{d}.csv")}
    fills = csv_read(FILS / f"{d}.csv") if False else csv_read(FILLS / f"{d}.csv")
    out = REPORTS / f"recon_{d}.csv"
    header = ["date","ticker","action","limit_price","target_shares",
              "filled_shares","avg_fill_price","slippage_abs","slippage_pct","status","note"]
    agg = defaultdict(lambda: {"qty":0, "notional":0.0})
    for f in fills:
        key = (f["ticker"].upper(), "buy" if f["side"].lower().startswith("b") else "sell")
        q = int_or_none(f["qty"]) or 0
        p = float_or_none(f["avg_price"]) or 0.0
        agg[key]["qty"] += q
        agg[key]["notional"] += q*p

    rows = []
    tickers = set([k[0] for k in recs.keys()]) | set([k[0] for k in agg.keys()])
    for t in sorted(tickers):
        for side in ("buy","sell"):
            r = recs.get((t, side))
            a = agg.get((t, side), {"qty":0,"notional":0.0})
            filled_qty = a["qty"]
            avg_fill = (a["notional"]/filled_qty) if filled_qty else None
            limit = float_or_none(r["limit_price"]) if r else None
            target = int_or_none(r["target_shares"]) if r else None
            slip_abs = (avg_fill - limit) if (avg_fill is not None and limit is not None) else None
            slip_pct = (slip_abs/limit*100.0) if (slip_abs is not None and limit) else None
            if r and filled_qty:
                status = "filled" if target and filled_qty>=target else "partial"
            elif r and not filled_qty:
                status = "missed"
            elif not r and filled_qty:
                status = "unplanned"
            else:
                status = "no_activity"
            rows.append({
                "date": d, "ticker": t, "action": side,
                "limit_price": f"{limit:.4f}" if limit is not None else "",
                "target_shares": str(target) if target is not None else "",
                "filled_shares": str(filled_qty) if filled_qty else "0",
                "avg_fill_price": f"{avg_fill:.4f}" if avg_fill is not None else "",
                "slippage_abs": f"{slip_abs:.4f}" if slip_abs is not None else "",
                "slippage_pct": f"{slip_pct:.2f}" if slip_pct is not None else "",
                "status": status, "note": r["note"] if r else ""
            })
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header); w.writeheader()
        for r in rows: w.writerow(r)
    print(f"Wrote reconciliation report: {out}")

def main():
    ensure_dirs()
    ap = argparse.ArgumentParser(description="Simple recs/fills tracker")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("log-rec", help="Log recommendation(s)")
    p1.add_argument("--date", required=True, help="YYYY-MM-DD or 'today'")
    p1.add_argument("items", nargs="+", help="TICKER,action,limit,shares[,note]")
    p1.set_defaults(func=cmd_log_rec)

    p2 = sub.add_parser("log-fill", help="Log broker fill(s)")
    p2.add_argument("--date", required=True, help="YYYY-MM-DD or 'today'")
    p2.add_argument("--broker", default="Robinhood", help="Broker name")
    p2.add_argument("--timestamp", help="ISO timestamp (optional)")
    p2.add_argument("items", nargs="+", help="TICKER,side,qty,avg_price[,order_id][,note]")
    p2.set_defaults(func=cmd_log_fill)

    p3 = sub.add_parser("reconcile", help="Compare recs vs fills for a date")
    p3.add_argument("--date", required=True, help="YYYY-MM-DD or 'today'")
    p3.set_defaults(func=cmd_reconcile)

    p4 = sub.add_parser("update-positions", help="Apply a date's fills to positions.csv")
    p4.add_argument("--date", required=True, help="YYYY-MM-DD or 'today'")
    p4.set_defaults(func=cmd_update_positions)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

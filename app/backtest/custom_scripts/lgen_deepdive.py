"""Deep-dive analysis of the two top custom strategies for LGEN.L."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

# Load data
data = pd.read_csv("/media/gavin/Data1/Workspace/stock-market-ta-local/data/analysis-data/LGEN.L.csv")
data["Date"] = pd.to_datetime(data["Date"])
data = data[data["Date"] >= "2016-01-01"].reset_index(drop=True)
print(f"Data: {len(data)} rows from {data['Date'].min().strftime('%Y-%m-%d')} to {data['Date'].max().strftime('%Y-%m-%d')}")

# ======================================================================
# Strategy 1: dividend_meanrev
# Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising
# Exit: BB Upper
# ======================================================================

garch_not_rising = data["ta_garch_vol"] <= data["ta_garch_vol"].shift(1)
div_entry = (
    (data["Close"] <= data["ta_bband_lower"]) &
    (data["ta_rsi14"] < 35) &
    (data["ta_cci"] < -100) &
    garch_not_rising
)

div_dates = data[div_entry]["Date"].tolist()
div_prices = data[div_entry]["Close"].tolist()

print(f"\n=== Dividend MeanRev ===")
print(f"Entry signals: {div_entry.sum()} ({div_entry.sum()/len(data)*100:.2f}%)")

trades_div = []
for d, p in zip(div_dates, div_prices):
    remaining = data[data["Date"] > d]
    exit_mask = remaining["Close"] >= remaining["ta_bband_upper"]
    if exit_mask.any():
        exit_d = remaining[exit_mask]["Date"].iloc[0]
        exit_p = remaining[exit_mask]["Close"].iloc[0]
        trades_div.append({"date": d, "exit": exit_d, "entry": p, "exit_p": exit_p,
                           "days": (exit_d - d).days, "pnl": (exit_p - p) / p * 100})
    else:
        last = data.iloc[-1]
        trades_div.append({"date": d, "exit": last["Date"], "entry": p, "exit_p": last["Close"],
                           "days": (last["Date"] - d).days, "pnl": (last["Close"] - p) / p * 100, "no_exit": True})

returns_div = [t["pnl"] for t in trades_div]
winners_div = [t for t in trades_div if t["pnl"] > 0]
losers_div = [t for t in trades_div if t["pnl"] <= 0]
print(f"Trades: {len(trades_div)}, Winners: {len(winners_div)} ({len(winners_div)/len(trades_div)*100:.1f}%)")
print(f"Total return: {sum(returns_div):.2f}%")
print(f"Avg win: {np.mean([t['pnl'] for t in winners_div]):.2f}%, Avg loss: {np.mean([t['pnl'] for t in losers_div]):.2f}%")
print(f"Avg hold: {np.mean([t['days'] for t in trades_div]):.1f} days")

print("\n--- Trade Details ---")
for t in trades_div:
    note = " [no exit]" if t.get("no_exit") else ""
    print(f"  {t['date'].strftime('%Y-%m-%d')}→{t['exit'].strftime('%Y-%m-%d')}: {t['pnl']:+.2f}% ({t['days']}d){note}")

# ======================================================================
# Strategy 2: dual_exit_div_meanrev
# Entry: Same as above
# Exit: BB Middle OR 5-day high - 3xATR trail
# ======================================================================

dual_entry = div_entry  # Same entry
dual_trades = []
for d, p in zip(div_dates, div_prices):
    remaining = data[data["Date"] > d]
    bb_middle = remaining["Close"] >= remaining["ta_bband_middle"]
    three_day_high = remaining["Close"].rolling(5).max()
    atr_trail = three_day_high - 3 * remaining["ta_atr14"]
    atr_exit = remaining["Close"] < atr_trail
    exit_mask = bb_middle | atr_exit
    
    if exit_mask.any():
        exit_d = remaining[exit_mask]["Date"].iloc[0]
        exit_p = remaining[exit_mask]["Close"].iloc[0]
        exit_idx = remaining[exit_mask].index[0]
        is_atr = exit_idx in remaining[atr_exit].index
        dual_trades.append({"date": d, "exit": exit_d, "entry": p, "exit_p": exit_p,
                           "days": (exit_d - d).days, "pnl": (exit_p - p) / p * 100,
                           "exit_type": "atr" if is_atr else "bb_mid"})
    else:
        last = data.iloc[-1]
        dual_trades.append({"date": d, "exit": last["Date"], "entry": p, "exit_p": last["Close"],
                           "days": (last["Date"] - d).days, "pnl": (last["Close"] - p) / p * 100,
                           "exit_type": "no_exit"})

returns_dual = [t["pnl"] for t in dual_trades]
winners_dual = [t for t in dual_trades if t["pnl"] > 0]
losers_dual = [t for t in dual_trades if t["pnl"] <= 0]
exit_types = {}
for t in dual_trades:
    et = t["exit_type"]
    exit_types[et] = exit_types.get(et, 0) + 1

print(f"\n=== Dual-Exit Div MeanRev ===")
print(f"Trades: {len(dual_trades)}, Winners: {len(winners_dual)} ({len(winners_dual)/len(dual_trades)*100:.1f}%)")
print(f"Total return: {sum(returns_dual):.2f}%")
print(f"Avg win: {np.mean([t['pnl'] for t in winners_dual]):.2f}%, Avg loss: {np.mean([t['pnl'] for t in losers_dual]):.2f}%")
print(f"Avg hold: {np.mean([t['days'] for t in dual_trades]):.1f} days")
print(f"Exit types: {exit_types}")

print("\n--- Trade Details ---")
for t in dual_trades:
    print(f"  {t['date'].strftime('%Y-%m-%d')}→{t['exit'].strftime('%Y-%m-%d')}: {t['pnl']:+.2f}% ({t['days']}d) [{t['exit_type']}]")

# ======================================================================
# Key comparison
# ======================================================================

print(f"\n=== COMPARISON ===")
print(f"{'Strategy':<30} {'Return':>10} {'Sharpe':>8} {'DD':>10} {'Trades':>8} {'WR':>8} {'Avg Win':>10} {'Avg Loss':>10}")
print("-" * 100)
print(f"{'Dividend MeanRev':<30} {sum(returns_div):>10.2f} {'0.50':>8} {'52.48%':>10} {len(trades_div):>8} {len(winners_div)/len(trades_div)*100:>7.1f}% {np.mean([t['pnl'] for t in winners_div]):>10.2f}% {np.mean([t['pnl'] for t in losers_div]):>10.2f}%")
print(f"{'Dual-Exit Div MeanRev':<30} {sum(returns_dual):>10.2f} {'0.69':>8} {'14.66%':>10} {len(dual_trades):>8} {len(winners_dual)/len(dual_trades)*100:>7.1f}% {np.mean([t['pnl'] for t in winners_dual]):>10.2f}% {np.mean([t['pnl'] for t in losers_dual]):>10.2f}%")
print(f"{'BB MeanRev Upper Exit':<30} {'87.82':>10} {'0.47':>8} {'50.59%':>10} {'12':>8} {'83.3%':>8} {'10.54':>10} {'-8.46':>10}")

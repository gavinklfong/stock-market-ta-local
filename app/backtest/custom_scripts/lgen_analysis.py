"""Deep-dive analysis of bb_meanrev_upper strategy performance on LGEN.L."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

# Load data
data = pd.read_csv("/media/gavin/Data1/Workspace/stock-market-ta-local/data/analysis-data/LGEN.L.csv")
data["Date"] = pd.to_datetime(data["Date"])
data = data[data["Date"] >= "2016-01-01"].reset_index(drop=True)
print(f"Data: {len(data)} rows from {data['Date'].min()} to {data['Date'].max()}")

# ======================================================================
# BB Mean Rev Upper Exit - Detailed signal analysis
# ======================================================================

# Entry conditions
bb_entry_upper = (
    (data["Close"] <= data["ta_bband_lower"]) &
    (data["ta_rsi14"] < 30) &
    (data["ta_williams_r"] < -80)
)

# Count entry signals
entry_signals = bb_entry_upper.sum()
print(f"\n=== BB MeanRev Upper Exit ===")
print(f"Entry signals: {entry_signals} ({entry_signals/len(data)*100:.2f}%)")

# Find entry dates
entry_dates = data[bb_entry_upper]["Date"].tolist()
entry_prices = data[bb_entry_upper]["Close"].tolist()
bb_lower_at_entry = data[bb_entry_upper]["ta_bband_lower"].tolist()
rsi_at_entry = data[bb_entry_upper]["ta_rsi14"].tolist()
wr_at_entry = data[bb_entry_upper]["ta_williams_r"].tolist()

print("\n--- Entry Details ---")
for i, (d, p, bl, r, w) in enumerate(zip(entry_dates, entry_prices, bb_lower_at_entry, rsi_at_entry, wr_at_entry)):
    print(f"  {d.strftime('%Y-%m-%d')}: Close={p:.2f}, BB Lower={bl:.2f}, RSI={r:.1f}, W%R={w:.1f}")

# Simulate trades with BB Upper exit
trades_upper = []
for i, (date, price, bl, r, w) in enumerate(zip(entry_dates, entry_prices, bb_lower_at_entry, rsi_at_entry, wr_at_entry)):
    # Find exit: Close >= BB Upper
    remaining = data[data["Date"] > date]
    exit_mask = remaining["Close"] >= remaining["ta_bband_upper"]
    
    if exit_mask.any():
        exit_date = remaining[exit_mask]["Date"].iloc[0]
        exit_price = remaining[exit_mask]["Close"].iloc[0]
        hold_days = (exit_date - date).days
        pnl_pct = (exit_price - price) / price * 100
        trades_upper.append({
            "entry_date": date,
            "exit_date": exit_date,
            "entry_price": price,
            "exit_price": exit_price,
            "hold_days": hold_days,
            "pnl_pct": pnl_pct
        })
    else:
        # Never reached upper - use end of data
        last = data.iloc[-1]
        trades_upper.append({
            "entry_date": date,
            "exit_date": last["Date"],
            "entry_price": price,
            "exit_price": last["Close"],
            "hold_days": (last["Date"] - date).days,
            "pnl_pct": (last["Close"] - price) / price * 100,
            "note": "no exit (ran to end)"
        })

if trades_upper:
    returns = [t["pnl_pct"] for t in trades_upper]
    winners = [t for t in trades_upper if t["pnl_pct"] > 0]
    losers = [t for t in trades_upper if t["pnl_pct"] <= 0]
    
    print(f"\n--- Trade Results ---")
    print(f"Total trades: {len(trades_upper)}")
    print(f"Winners: {len(winners)} ({len(winners)/len(trades_upper)*100:.1f}%)")
    print(f"Losers: {len(losers)}")
    print(f"Win rate: {len(winners)/len(trades_upper)*100:.1f}%")
    print(f"Avg win: {np.mean([t['pnl_pct'] for t in winners]):.2f}%")
    print(f"Avg loss: {np.mean([t['pnl_pct'] for t in losers]):.2f}%")
    print(f"Total return: {sum(returns):.2f}%")
    print(f"Avg hold days: {np.mean([t['hold_days'] for t in trades_upper]):.1f}")
    
    print("\n--- Trade Details ---")
    for t in trades_upper:
        note = f" [{t.get('note', '')}]" if 'note' in t else ""
        print(f"  {t['entry_date'].strftime('%Y-%m-%d')}→{t['exit_date'].strftime('%Y-%m-%d')}: {t['pnl_pct']:+.2f}% ({t['hold_days']}d){note}")

# ======================================================================
# Compare with standard BB Middle exit
# ======================================================================

bb_entry_mid = (
    (data["Close"] <= data["ta_bband_lower"]) &
    (data["ta_rsi14"] < 30) &
    (data["ta_williams_r"] < -80)
)
entry_dates_mid = data[bb_entry_mid]["Date"].tolist()
entry_prices_mid = data[bb_entry_mid]["Close"].tolist()

trades_mid = []
for i, (date, price) in enumerate(zip(entry_dates_mid, entry_prices_mid)):
    remaining = data[data["Date"] > date]
    exit_mask = remaining["Close"] >= remaining["ta_bband_middle"]
    
    if exit_mask.any():
        exit_date = remaining[exit_mask]["Date"].iloc[0]
        exit_price = remaining[exit_mask]["Close"].iloc[0]
        hold_days = (exit_date - date).days
        pnl_pct = (exit_price - price) / price * 100
        trades_mid.append({"pnl_pct": pnl_pct, "hold_days": hold_days})
    else:
        last = data.iloc[-1]
        trades_mid.append({
            "pnl_pct": (last["Close"] - price) / price * 100,
            "hold_days": (last["Date"] - date).days
        })

if trades_mid:
    returns_mid = [t["pnl_pct"] for t in trades_mid]
    winners_mid = [t for t in trades_mid if t["pnl_pct"] > 0]
    print(f"\n=== BB MeanRev Middle Exit (for comparison) ===")
    print(f"Total trades: {len(trades_mid)}")
    print(f"Winners: {len(winners_mid)} ({len(winners_mid)/len(trades_mid)*100:.1f}%)")
    print(f"Total return: {sum(returns_mid):.2f}%")
    print(f"Avg hold days: {np.mean([t['hold_days'] for t in trades_mid]):.1f}")

# ======================================================================
# Analyze BB width at entry - do wide bands capture more?
# ======================================================================

bb_width = (data["ta_bband_upper"] - data["ta_bband_lower"]) / data["ta_bband_middle"]
data_with_width = data[bb_entry_upper].copy()
if len(data_with_width) > 0:
    print(f"\n=== BB Width at Entry (Upper Exit Strategy) ===")
    print(f"Mean BB width at entry: {bb_width[bb_entry_upper].mean():.4f}")
    print(f"Median BB width at entry: {bb_width[bb_entry_upper].median():.4f}")
    
    # Average BB Upper - BB Lower distance
    spread = data_with_width["ta_bband_upper"] - data_with_width["ta_bband_lower"]
    print(f"Avg spread (Upper-Lower) at entry: {spread.mean():.2f}")

# ======================================================================
# Key insight: BB Upper exit captures the FULL mean-reversion range
# ======================================================================

print(f"\n=== KEY INSIGHT ANALYSIS ===")
print(f"LGEN.L mean price: {data['Close'].mean():.2f}")
print(f"LGEN.L BB Upper mean: {data['ta_bband_upper'].mean():.2f}")
print(f"LGEN.L BB Lower mean: {data['ta_bband_lower'].mean():.2f}")
print(f"Mean-reversion range (Upper - Lower): {(data['ta_bband_upper'] - data['ta_bband_lower']).mean():.2f}")
print(f"Entry price mean (at BB Lower): {data[bb_entry_upper]['Close'].mean():.2f}")
print(f"Target price mean (BB Upper at entry time): {data[bb_entry_upper]['ta_bband_upper'].mean():.2f}")
print(f"Avg potential gain per trade: {(data[bb_entry_upper]['ta_bband_upper'].mean() - data[bb_entry_upper]['Close'].mean()) / data[bb_entry_upper]['Close'].mean() * 100:.2f}%")

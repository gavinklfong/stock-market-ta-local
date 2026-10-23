"""Deep analysis: top strategies comparison + parameter tuning + trade-level detail."""
import sys
from pathlib import Path
import itertools

BACKTEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKTEST_DIR))

import pandas as pd
import numpy as np
from framework.engine import BacktestEngine, DEFAULT_CUTOFF
from framework.extensions import load_custom_strategies
from framework.metrics import calculate_metrics
import vectorbt as vbt
from vectorbt.portfolio.enums import SizeType

# ============================================================
# Load data
# ============================================================
df_raw = pd.read_csv("data/analysis-data/LGEN.L.csv")
df_raw["Date"] = pd.to_datetime(df_raw["Date"])
df_raw = df_raw.sort_values("Date").reset_index(drop=True)
df_raw = df_raw.dropna(subset=["Close", "High", "Low"])
df_raw.index = df_raw["Date"]
cutoff = DEFAULT_CUTOFF
df = df_raw[df_raw["Date"] >= cutoff].reset_index(drop=True)
df.index = df["Date"]

print(f"Data: {len(df)} rows, {df['Date'].iloc[0].date()} to {df['Date'].iloc[-1].date()}")
print(f"Price range: {df['Close'].min():.2f} - {df['Close'].max():.2f}")
print(f"BH return: {(df['Close'].iloc[-1]/df['Close'].iloc[0] - 1)*100:.2f}%\n")

close = df["Close"]
INITIAL_CAPITAL = 100_000
COMMISSION = 0.001
SLIPPAGE = 0.001

def run_portfolio(entries, exits):
    """Run a vectorbt portfolio and return metrics."""
    pf = vbt.Portfolio.from_signals(
        close=close, entries=entries, exits=exits,
        init_cash=INITIAL_CAPITAL, freq="1D",
        slippage=SLIPPAGE, size=1.0, size_type=SizeType.Percent,
        fees=COMMISSION,
    )
    return pf, calculate_metrics(pf)

def print_result(name, metrics):
    tr = metrics.get("Total Return (%)", 0)
    sr = metrics.get("Sharpe Ratio", 0)
    dd = metrics.get("Max Drawdown (%)", 0)
    tt = metrics.get("Total Trades", 0)
    wr = metrics.get("Win Rate (%)", 0)
    pf = metrics.get("Profit Factor", 0)
    print(f"  {name:35s}  Ret: {tr:8.2f}%  Sharpe: {sr:7.3f}  MaxDD: {dd:7.2f}%  Trades: {int(tt):4d}  Win: {wr:5.1f}%  PF: {pf:.2f}")

# ============================================================
# 1. Top Built-in Strategies (re-run for direct comparison)
# ============================================================
print("=" * 90)
print("  TOP BUILT-IN STRATEGIES — Direct Re-run for Comparison")
print("=" * 90)

from strategies.builtins import (
    signal_bb_meanrev_upper, signal_dual_exit_meanrev, signal_vol_filtered_meanrev,
    signal_bb_meanrev_atr, signal_bb_meanrev,
)

builtin_top = {
    "BB MeanRev (Upper Exit)": signal_bb_meanrev_upper,
    "Dual-Exit MeanRev (Built-in)": signal_dual_exit_meanrev,
    "Vol-Filtered MeanRev": signal_vol_filtered_meanrev,
    "BB MeanRev (ATR Trail)": signal_bb_meanrev_atr,
    "BB MeanRev (Baseline)": signal_bb_meanrev,
}

results = []
for name, fn in builtin_top.items():
    entries, exits = fn(df)
    pf, metrics = run_portfolio(entries, exits)
    metrics["Strategy"] = name
    results.append(metrics)
    print_result(name, metrics)

# ============================================================
# 2. Top Custom Strategies
# ============================================================
print(f"\n{'='*90}")
print("  TOP CUSTOM STRATEGIES")
print("=" * 90)

custom_dir = BACKTEST_DIR / "custom"
all_custom = load_custom_strategies(custom_dir)
custom_top = {
    "dividend_meanrev": all_custom["dividend_meanrev"],
    "dual_exit_div_meanrev": all_custom["dual_exit_div_meanrev"],
    "low_vol_meanrev": all_custom["low_vol_meanrev"],
}

for name, fn in custom_top.items():
    entries, exits = fn(df)
    pf, metrics = run_portfolio(entries, exits)
    metrics["Strategy"] = name
    results.append(metrics)
    print_result(name, metrics)

# ============================================================
# 3. Parameter Sensitivity: dual_exit_div_meanrev variants
# ============================================================
print(f"\n{'='*90}")
print("  PARAMETER SENSITIVITY: dual_exit_div_meanrev Variants")
print("=" * 90)

def custom_dual_exit_var(df, rsi_thresh=35, cci_thresh=-100,
                         garch_filter=True,
                         bb_middle_exit=True, atr_mult=3):
    """Parameterized dual-exit dividend mean reversion."""
    garch_not_rising = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < rsi_thresh) &
        (df["ta_cci"] < cci_thresh) &
        (not garch_filter or garch_not_rising)
    )
    if bb_middle_exit:
        exit_ = df["Close"] >= df["ta_bband_middle"]
    else:
        five_day_high = df["Close"].rolling(5).max()
        atr_stop = five_day_high - atr_mult * df["ta_atr14"]
        atr_exit = df["Close"] < atr_stop
        exit_ = atr_exit
    return entry.astype(int), exit_.astype(int) * -1

param_grid = {
    "rsi_thresh": [30, 32, 35, 38, 40],
    "cci_thresh": [-80, -100, -120],
    "garch_filter": [True, False],
    "bb_middle_exit": [True, False],
    "atr_mult": [2, 3, 4],
}

best_sharpe = -999
best_config = None
best_metrics = None
sensitivity_results = []

for rsi_t, cci_t, garch_f, bb_me, atr_m in itertools.product(
    param_grid["rsi_thresh"], param_grid["cci_thresh"],
    param_grid["garch_filter"], param_grid["bb_middle_exit"],
    param_grid["atr_mult"]
):
    name = f"RSI<{rsi_t} CCI<{cci_t} GARCH={garch_f} BBExit={bb_me} ATRx{atr_m}"
    entries, exits = custom_dual_exit_var(df, rsi_t, cci_t, garch_f, bb_me, atr_m)
    if entries.sum() == 0:
        continue
    pf, metrics = run_portfolio(entries, exits)
    sr = metrics.get("Sharpe Ratio", 0)
    tr = metrics.get("Total Return (%)", 0)
    dd = metrics.get("Max Drawdown (%)", 0)
    tt = metrics.get("Total Trades", 0)
    wr = metrics.get("Win Rate (%)", 0)
    sensitivity_results.append({
        "config": name, "Sharpe": sr, "Return": tr, "MaxDD": dd,
        "Trades": int(tt), "WinRate": wr, "entries": entries.sum(),
    })
    if sr > best_sharpe:
        best_sharpe = sr
        best_config = name
        best_metrics = metrics

sens_df = pd.DataFrame(sensitivity_results).sort_values("Sharpe", ascending=False)
print(f"\n  {'Config':50s}  Sharpe  Return  MaxDD   Trades  Win%")
print(f"  {'─'*50}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*6}")
for _, row in sens_df.head(15).iterrows():
    print(f"  {row['config']:50s}  {row['Sharpe']:6.3f}  {row['Return']:6.1f}%  {row['MaxDD']:5.1f}%  {row['Trades']:5d}  {row['WinRate']:5.1f}%")

print(f"\n  ★ Best Sharpe: {best_config}")
if best_metrics:
    print_result("  Best Config", best_metrics)

# ============================================================
# 4. Trade-level analysis of top 3 strategies
# ============================================================
print(f"\n{'='*90}")
print("  TRADE-LEVEL ANALYSIS — Top 3 Strategies")
print("=" * 90)

top3_funcs = {
    "BB MeanRev (Upper Exit)": signal_bb_meanrev_upper,
    "Dual-Exit Div MeanRev (Custom)": all_custom["dual_exit_div_meanrev"],
    "Dividend MeanRev (Custom)": all_custom["dividend_meanrev"],
}

for name, fn in top3_funcs.items():
    print(f"\n  ┌─ {name}")
    entries, exits = fn(df)
    pf = vbt.Portfolio.from_signals(
        close=close, entries=entries, exits=exits,
        init_cash=INITIAL_CAPITAL, freq="1D",
        slippage=SLIPPAGE, size=1.0, size_type=SizeType.Percent,
        fees=COMMISSION,
    )
    trades = pf.trades.records_readable
    if len(trades) == 0:
        print("  └─ No trades")
        continue
    
    pnl = trades["PnL"]
    returns = trades["Return"]
    entry_ts = trades["Entry Timestamp"]
    exit_ts = trades["Exit Timestamp"]
    holding = (exit_ts - entry_ts).dt.days
    
    print(f"  Total trades: {len(trades)}")
    print(f"  Winning trades: {(pnl > 0).sum()} ({(pnl > 0).mean()*100:.1f}%)")
    print(f"  Avg PnL: {pnl.mean():.2f} ({pnl.mean()/INITIAL_CAPITAL*100:.2f}%)")
    print(f"  Avg return: {returns.mean()*100:.2f}%")
    print(f"  Max single trade PnL: {pnl.max():.2f}")
    print(f"  Avg holding period: {holding.mean():.1f} days")
    print(f"  Longest hold: {holding.max()} days")
    
    # Drawdown analysis using vectorbt-correct API
    eq_curve = pf.value()
    peak = eq_curve.max()
    trough = eq_curve.min()
    print(f"  Peak equity: {peak:.0f}")
    print(f"  Trough equity: {trough:.0f}")
    print(f"  Final equity: {eq_curve.iloc[-1]:.0f}")
    print(f"  Max drawdown from peak: {(trough/peak - 1)*100:.1f}%")
    print(f"  └─ End")

# ============================================================
# 5. Sector / regime breakdown
# ============================================================
print(f"\n{'='*90}")
print("  YEAR-BY-YEAR RETURN BREAKDOWN")
print("=" * 90)

df_with_year = df.copy()
df_with_year["Year"] = df_with_year["Date"].dt.year

for strat_name, fn in [("BH", None), ("BB Upper", signal_bb_meanrev_upper),
                        ("Dual-Exit Div", all_custom["dual_exit_div_meanrev"]),
                        ("Div MeanRev", all_custom["dividend_meanrev"])]:
    print(f"\n  {strat_name}:")
    years = sorted(df_with_year["Year"].unique())
    for year in years:
        ydf = df_with_year[df_with_year["Year"] == year]
        if len(ydf) < 5:
            continue
        yclose = ydf["Close"]
        if strat_name == "BH":
            ret = (yclose.iloc[-1] / yclose.iloc[0] - 1) * 100
        else:
            e, x = fn(ydf)
            pf = vbt.Portfolio.from_signals(
                close=yclose, entries=e, exits=x,
                init_cash=INITIAL_CAPITAL, freq="1D",
                slippage=SLIPPAGE, size=1.0, size_type=SizeType.Percent,
                fees=COMMISSION,
            )
            ret = pf.total_return() * 100
        print(f"    {year}: {ret:+7.2f}%")

# ============================================================
# 6. Summary comparison table
# ============================================================
print(f"\n{'='*90}")
print("  COMBINED RANKING — ALL STRATEGIES")
print("=" * 90)

final_df = pd.DataFrame(results)
final_df["Strategy"] = [m["Strategy"] for m in results]
final_df = final_df.sort_values("Sharpe Ratio", ascending=False)

print(f"\n  {'Rank':4s}  {'Strategy':35s}  {'Return':>8s}  {'Sharpe':>7s}  {'MaxDD':>7s}  {'Trades':>6s}  {'Win%':>6s}  {'PF':>5s}")
print(f"  {'─'*4}  {'─'*35}  {'─'*8}  {'─'*7}  {'─'*7}  {'─'*6}  {'─'*6}  {'─'*5}")
for i, (_, row) in enumerate(final_df.iterrows(), 1):
    print(f"  {i:4d}  {row['Strategy']:35s}  {row['Total Return (%)']:8.2f}  {row['Sharpe Ratio']:7.3f}  {row['Max Drawdown (%)']:7.2f}  {int(row['Total Trades']):6d}  {row['Win Rate (%)']:6.1f}  {row['Profit Factor']:5.2f}")

"""
AZN.L (AstraZeneca) Backtest v2 - Hybrid strategies with risk management.

Based on v1 findings: All standard trend-following strategies lose money on AZN.L
despite +260% total return. Key insight: severe periodic corrections (-50.5% max DD)
cause whipsaw losses.

v2 focuses on:
1. Strong MA200 slope filter (only trade in confirmed uptrends)
2. Momentum Composite entry (best v1 performer at -0.7%)
3. Aggressive exits (time stop + ATR trail + RSI overbought)
4. Regime awareness (HMM + volume filters)
5. Pullback-to-strength entries (buy dips in uptrends)
6. 5-year focus (2021-2026) per user request

Strategies tested:
  --- Hybrid Trend + Momentum (Entry Filters) ---
   1. Hybrid_Strong    - MA200 up + Price>MA200 + MomentumComposite
   2. Hybrid_HMM       - HMM regime 0 dominant + MA200 up + MomentumComposite
   3. Hybrid_Volume    - MomentumComposite + Volume percentile > 50

  --- Exit Optimization for Momentum Composite ---
   4. MC_TimeStop5     - MomentumComposite + exit after 5 days
   5. MC_ATRTrail2     - MomentumComposite + ATR trail (2xATR from entry)
   6. MC_ATRTrail3     - MomentumComposite + ATR trail (3xATR from entry)
   7. MC_RSIExit70     - MomentumComposite + exit on RSI>70
   8. MC_RSIExit65     - MomentumComposite + exit on RSI>65
   9. MC_ComboExit     - MomentumComposite + time stop OR ATR trail OR RSI>65

  --- Pullback-to-Strength ---
   10. Pullback20       - Wait for pullback (Close<EMA20, RSI 40-50) then enter
                          when price reclaims EMA20 with momentum confirmation
   11. Pullback50       - Wait for pullback to EMA50, enter on bounce + momentum

  --- Position Sizing + Risk Management ---
   12. MC_RiskManaged   - MomentumComposite with ATR-based sizing (2% risk)
   13. Hybrid_Strong_TM - Strong trend filter + Momentum entry + ATR exit + Time stop

  --- Buy & Hold Baselines ---
   14. BuyAndHold_5Y    - Simple buy and hold (5-year focus)
   15. BuyAndHold_All   - Simple buy and hold (all data)
"""
import pandas as pd
import numpy as np
import warnings
import sys
from pathlib import Path

import vectorbt as vbt
import quantstats as qs
from datetime import datetime

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent / ".." / "calculate-ta"))

# Configuration
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "analysis-data" / "AZN.L.csv"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "backtest-reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INITIAL_CAPITAL = 100000
SLIPPAGE = 0.001  # 0.1% slippage per trade

# 5-year focus period
START_DATE = pd.Timestamp("2021-01-01")


# =============================================================================
# Data Loading
# =============================================================================

def load_data():
    """Load AZN.L analysis data with all TA indicators."""
    df = pd.read_csv(DATA_PATH)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    critical = ["Close", "High", "Low", "Open", "Volume"]
    df = df.dropna(subset=critical)

    # Calculate MA200 slope (percentage change over 20 days)
    df["ma200_slope_20d"] = df["ta_ema200"].pct_change(20)

    print(f"Loaded {len(df)} rows: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Close range: {df['Close'].min():.2f} to {df['Close'].max():.2f}")
    print(f"Total return: {(df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100:.1f}%")

    # 5-year subset
    df_5y = df[df.index >= START_DATE]
    print(f"\n5-year subset ({START_DATE.date()} onwards): {len(df_5y)} rows")
    print(f"5-year return: {(df_5y['Close'].iloc[-1] / df_5y['Close'].iloc[0] - 1) * 100:.1f}%")
    print(f"5-year Close range: {df_5y['Close'].min():.2f} to {df_5y['Close'].max():.2f}")

    return df, df_5y


# =============================================================================
# Signal Generation Functions
# =============================================================================

def signal_momentum_composite(df):
    """Momentum Composite: RSI>55, MACD>Signal, ROC20>0, W%R>-50, CMF>0, EMA20>EMA50."""
    entry = (
        (df["ta_rsi14"] > 55)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
        & (df["ta_roc20"] > 0)
        & (df["ta_williams_r"] > -50)
        & (df["ta_cmf"] > 0)
        & (df["ta_ema20"] > df["ta_ema50"])
    )
    exit_ = (df["ta_rsi14"] < 50) & (df["ta_macd_line"] < df["ta_macd_signal"])
    return entry.astype(int), exit_.astype(int) * -1


def signal_hybrid_strong(df):
    """Hybrid Strong: MA200 up + Price>MA200 + MomentumComposite entry."""
    momentum = signal_momentum_composite(df)
    # Additional filters
    trend_up = (df["Close"] > df["ta_ema200"]) & (df["ma200_slope_20d"] > 0)
    entries = momentum[0] & trend_up
    return entries, momentum[1]


def signal_hybrid_hmm(df):
    """Hybrid HMM: HMM regime 0 dominant + MA200 up + MomentumComposite."""
    momentum = signal_momentum_composite(df)
    regime_0 = (
        (df["ta_hmm_regime_prob_0"] > df["ta_hmm_regime_prob_1"])
        & (df["ta_hmm_regime_prob_0"] > df["ta_hmm_regime_prob_2"])
    )
    trend_up = (df["Close"] > df["ta_ema200"]) & (df["ma200_slope_20d"] > 0)
    entries = momentum[0] & regime_0 & trend_up
    return entries, momentum[1]


def signal_hybrid_volume(df):
    """Hybrid Volume: MomentumComposite + Volume percentile > 50."""
    momentum = signal_momentum_composite(df)
    vol_filter = df["ta_volume_percentile"] > 50
    entries = momentum[0] & vol_filter
    return entries, momentum[1]


def exit_time_stop_5d(df):
    """Exit after 5 days (simplified: RSI<55 as proxy for time stop)."""
    # Real time stop needs trade tracking; use momentum decay as proxy
    return df["ta_roc20"] < 0


def exit_time_stop_10d(df):
    """Exit after 10 days momentum decay."""
    return df["ta_roc10"] < 0 if "ta_roc10" in df.columns else df["ta_rsi14"] < 45


def exit_atr_trail_entry(df, atr_mult=2, lookback=10):
    """Exit when price falls below entry-based ATR trailing stop.
    Uses rolling highest high since entry as reference."""
    # Calculate ATR-based trailing stop from highest high (lookback period)
    highest_high = df["High"].rolling(lookback).max()
    stop = highest_high - atr_mult * df["ta_atr14"]
    return df["Close"] < stop


def exit_atr_trail_entry3(df):
    """3x ATR trailing stop."""
    return exit_atr_trail_entry(df, atr_mult=3, lookback=10)


def exit_atr_trail_entry2(df):
    """2x ATR trailing stop."""
    return exit_atr_trail_entry(df, atr_mult=2, lookback=10)


def exit_rsi_overbought(df, threshold=70):
    """Exit when RSI > threshold."""
    return df["ta_rsi14"] > threshold


def exit_rsi_overbought65(df):
    return exit_rsi_overbought(df, 65)


def exit_rsi_overbought70(df):
    return exit_rsi_overbought(df, 70)


def exit_combo_mc(df):
    """Momentum Composite combo exit: time stop OR ATR trail OR RSI>65."""
    atr_exit = exit_atr_trail_entry2(df)
    rsi_exit = exit_rsi_overbought65(df)
    momentum_decay = df["ta_roc20"] < 0
    return atr_exit | rsi_exit | momentum_decay


def signal_pullback_to_ema20(df):
    """Pullback-to-Strength: Buy pullbacks to EMA20 in uptrend.
    Phase 1: Pullback zone - Close<EMA20, RSI 40-50, MA200 up
    Phase 2: Recovery - Close reclaims EMA20, MACD>Signal, RSI>50"""
    # Pullback zone
    in_pullback = (
        (df["Close"] < df["ta_ema20"])
        & (df["ta_rsi14"] >= 40)
        & (df["ta_rsi14"] <= 50)
        & (df["Close"] > df["ta_ema200"])
        & (df["ma200_slope_20d"] > 0)
    )
    # Recovery signal
    recovery = (
        (df["Close"] > df["ta_ema20"])
        & (df["ta_macd_line"] > df["ta_macd_signal"])
        & (df["ta_rsi14"] > 50)
        & (df["ta_roc20"] > 0)
    )
    entries = recovery & in_pullback.shift(1)  # Enter next day after recovery
    exit_ = (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 70)
    return entries.astype(int), exit_.astype(int) * -1


def signal_pullback_to_ema50(df):
    """Pullback-to-EMA50: Buy dips to EMA50 in strong uptrend.
    Phase 1: Deep pullback - Close<EMA50, RSI 35-45
    Phase 2: Bounce - Close>EMA50, MACD histogram positive, volume up"""
    in_pullback = (
        (df["Close"] < df["ta_ema50"])
        & (df["ta_rsi14"] >= 35)
        & (df["ta_rsi14"] <= 45)
        & (df["Close"] > df["ta_ema200"])
        & (df["ma200_slope_20d"] > 0)
    )
    roc5_positive = (
        df["ta_roc5"] > 0 if "ta_roc5" in df.columns
        else pd.Series(True, index=df.index)
    )
    bounce = (
        (df["Close"] > df["ta_ema50"])
        & (df["ta_macd_histogram"] > 0)
        & (df["ta_volume_percentile"] > 30)
        & roc5_positive
    )
    entries = bounce & in_pullback.shift(1)
    exit_ = (df["Close"] < df["ta_ema200"]) | (df["ta_rsi14"] > 70)
    return entries.astype(int), exit_.astype(int) * -1


def signal_hybrid_strong_time_atr(df):
    """Hybrid Strong Trend + Momentum + Combined ATR + Time Stop."""
    entries, _ = signal_hybrid_strong(df)
    return entries, None  # Exits will be optimized


def signal_buy_and_hold(df):
    """Buy and hold signal (always in market after day 0)."""
    entries = pd.Series(1, index=df.index)
    entries.iloc[0] = 1
    exits = pd.Series(0, index=df.index)
    return entries.astype(int), exits.astype(int) * -1


# =============================================================================
# Backtest Engine
# =============================================================================

def run_backtest(df, entries, exits=None, name="", initial_capital=INITIAL_CAPITAL):
    """Run a vectorbt backtest."""
    entries = pd.Series(entries).reindex(df.index).fillna(False).astype(int)
    if exits is not None:
        exits = pd.Series(exits).reindex(df.index).fillna(False).astype(int)

    pf = vbt.Portfolio.from_signals(
        close=df["Close"], entries=entries, exits=exits,
        init_cash=initial_capital, slippage=SLIPPAGE, freq="1D",
    )
    stats = pf.stats()
    total_return = stats.get("Total Return [%]", 0)
    win_rate = stats.get("Win Rate [%]", 0)
    total_trades = int(stats.get("Total Trades", 0))
    profit_factor = stats.get("Profit Factor", 0)
    max_drawdown = stats.get("Max Drawdown [%]", 0)
    sharpe_ratio = stats.get("Sharpe Ratio", 0)
    calmar_ratio = stats.get("Calmar Ratio", 0)
    avg_drawdown = stats.get("Average Drawdown [%]", 0)

    # Handle NaN values
    if pd.isna(total_return): total_return = 0
    if pd.isna(win_rate): win_rate = 0
    if pd.isna(profit_factor): profit_factor = 0
    if pd.isna(max_drawdown): max_drawdown = 0
    if pd.isna(sharpe_ratio): sharpe_ratio = 0
    if pd.isna(calmar_ratio): calmar_ratio = 0
    if pd.isna(avg_drawdown): avg_drawdown = 0

    n_days = len(df)
    annualized_return = (1 + total_return / 100) ** (252 / n_days) - 1 if n_days > 0 else 0
    winning_trades = int(round(total_trades * win_rate / 100)) if total_trades > 0 else 0
    losing_trades = total_trades - winning_trades

    results = {
        "name": name, "total_return": total_return / 100,
        "annualized_return": annualized_return,
        "win_rate": win_rate / 100, "total_trades": total_trades,
        "winning_trades": winning_trades, "losing_trades": losing_trades,
        "profit_factor": profit_factor, "max_drawdown": max_drawdown / 100,
        "sharpe_ratio": sharpe_ratio, "calmar_ratio": calmar_ratio,
        "avg_drawdown": avg_drawdown / 100, "final_value": pf.final_value(),
        "entry_count": int(entries.sum()),
    }
    return results, pf


def run_strategy_group(df, group_name, entry_fn, exit_fns):
    """Run entry function with multiple exit variants."""
    entries, default_exits = entry_fn(df)
    print(f"\n  {group_name}: {entries.sum()} entries ({entries.mean()*100:.1f}%)")

    results = []
    for exit_name, exit_fn in exit_fns.items():
        name = f"{group_name} / {exit_name}" if exit_name else group_name
        if exit_fn is not None:
            exits = default_exits | exit_fn(df)
        else:
            exits = default_exits
        result, pf = run_backtest(df, entries, exits, name)
        results.append(result)
        print(f"    {exit_name if exit_name else 'Default':20s} | "
              f"WR: {result['win_rate']*100:5.1f}% | Trades: {result['total_trades']:4d} | "
              f"Ret: {result['total_return']*100:7.1f}% | Sharpe: {result['sharpe_ratio']:6.3f} | "
              f"MaxDD: {result['max_drawdown']*100:6.1f}%")
    return results


def run_single_strategy(df, name, entry_fn, exit_fn=None, default_exits=None):
    """Run a single strategy."""
    entries, sig_exits = entry_fn(df) if callable(entry_fn) and not hasattr(entry_fn, '__len__') else (entry_fn, default_exits or sig_exits)

    if hasattr(entry_fn, '__len__'):
        entries = entry_fn
        sig_exits = default_exits
    else:
        entries, sig_exits = entry_fn(df)

    if exit_fn is not None:
        exits = exit_fn(df)
    else:
        exits = sig_exits

    result, pf = run_backtest(df, entries, exits, name)
    print(f"  {name:35s} | WR: {result['win_rate']*100:5.1f}% | Trades: {result['total_trades']:4d} | "
          f"Ret: {result['total_return']*100:7.1f}% | Sharpe: {result['sharpe_ratio']:6.3f} | "
          f"MaxDD: {result['max_drawdown']*100:6.1f}%")
    return result, pf


# =============================================================================
# Main Backtest Runner
# =============================================================================


def main():
    print("=" * 80)
    print("AZN.L (AstraZeneca) Backtest v2 - Hybrid Strategies with Risk Management")
    print("=" * 80)

    # Load data
    df, df_5y = load_data()

    all_results = []

    # =====================================================================
    # Group 1: Buy & Hold Baselines
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 1: Buy & Hold Baselines")
    print("=" * 80)

    bha_entries, bha_exits = signal_buy_and_hold(df_5y)
    result, pf = run_backtest(df_5y, bha_entries, bha_exits, "Buy & Hold 5Y (Baseline)")
    all_results.append(result)

    bha_entries_all, bha_exits_all = signal_buy_and_hold(df)
    result, pf = run_backtest(df, bha_entries_all, bha_exits_all, "Buy & Hold All (Baseline)")
    all_results.append(result)

    # =====================================================================
    # Group 2: Hybrid Trend + Momentum (Entry Filters)
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 2: Hybrid Trend + Momentum Entry Filters")
    print("=" * 80)

    hybrid_exit_fns = {
        "No Filter": None,
        "ATR Trail 2x": exit_atr_trail_entry2,
        "ATR Trail 3x": exit_atr_trail_entry3,
        "RSI > 65": exit_rsi_overbought65,
        "RSI > 70": exit_rsi_overbought70,
        "Combo (ATR+RSI+Momentum)": exit_combo_mc,
    }

    print("\n  --- Hybrid Strong (MA200 slope > 0 + Price > MA200) ---")
    h_results = run_strategy_group(df_5y, "Hybrid_Strong", signal_hybrid_strong, hybrid_exit_fns)
    all_results.extend(h_results)

    print("\n  --- Hybrid HMM (Regime 0 dominant) ---")
    h_results_hmm = run_strategy_group(df_5y, "Hybrid_HMM", signal_hybrid_hmm, hybrid_exit_fns)
    all_results.extend(h_results_hmm)

    print("\n  --- Hybrid Volume (Volume %ile > 50) ---")
    h_results_vol = run_strategy_group(df_5y, "Hybrid_Volume", signal_hybrid_volume, hybrid_exit_fns)
    all_results.extend(h_results_vol)

    # =====================================================================
    # Group 3: Exit Optimization for Momentum Composite
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 3: Momentum Composite Exit Optimization (5Y)")
    print("=" * 80)

    mc_exit_fns = {
        "Default (v1 baseline)": None,
        "Time Stop (ROC20<0)": lambda df: df["ta_roc20"] < 0,
        "Time Stop 10d (ROC10<0)": lambda df: df["ta_roc10"] < 0 if "ta_roc10" in df.columns else df["ta_rsi14"] < 45,
        "ATR Trail 2x": exit_atr_trail_entry2,
        "ATR Trail 3x": exit_atr_trail_entry3,
        "RSI > 65": exit_rsi_overbought65,
        "RSI > 70": exit_rsi_overbought70,
        "Combo (ATR+RSI+ROC)": exit_combo_mc,
    }

    mc_results = run_strategy_group(df_5y, "Momentum_Composite", signal_momentum_composite, mc_exit_fns)
    all_results.extend(mc_results)

    # Also test on full dataset for comparison
    mc_results_full = run_strategy_group(df, "Momentum_Composite_All", signal_momentum_composite, mc_exit_fns)
    all_results.extend(mc_results_full)

    # =====================================================================
    # Group 4: Pullback-to-Strength Strategies
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 4: Pullback-to-Strength Strategies")
    print("=" * 80)

    for name, signal_fn in [
        ("Pullback_20", signal_pullback_to_ema20),
        ("Pullback_50", signal_pullback_to_ema50),
    ]:
        entries, exits = signal_fn(df_5y)
        print(f"\n  {name}: {entries.sum()} entries ({entries.mean()*100:.1f}%)")

        # Test with different exit overrides
        for exit_name, exit_fn in {
            "Default": None,
            "ATR Trail 2x": exit_atr_trail_entry2,
            "RSI > 70": exit_rsi_overbought70,
            "Combo": exit_combo_mc,
        }.items():
            strat_name = f"{name} / {exit_name}"
            if exit_fn is not None:
                exits_combined = exits | exit_fn(df_5y)
            else:
                exits_combined = exits
            result, pf = run_backtest(df_5y, entries, exits_combined, strat_name)
            all_results.append(result)
            print(f"    {exit_name:20s} | WR: {result['win_rate']*100:5.1f}% | Trades: {result['total_trades']:4d} | Ret: {result['total_return']*100:7.1f}% | Sharpe: {result['sharpe_ratio']:6.3f} | MaxDD: {result['max_drawdown']*100:6.1f}%")

    # =====================================================================
    # Group 5: Hybrid Strong + Momentum + Combined Exits
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 5: Hybrid Strong + Momentum + Combined Exits (5Y)")
    print("=" * 80)

    for exit_name, exit_fn in {
        "No Filter": None,
        "ATR Trail 2x": exit_atr_trail_entry2,
        "ATR Trail 3x": exit_atr_trail_entry3,
        "RSI > 65": exit_rsi_overbought65,
        "RSI > 70": exit_rsi_overbought70,
        "Combo (ATR+RSI+ROC)": exit_combo_mc,
    }.items():
        entries, _ = signal_hybrid_strong(df_5y)
        if exit_fn is not None:
            exits_combined = exit_fn(df_5y)
        else:
            exits_combined = signal_momentum_composite(df_5y)[1]  # Use momentum composite default exits
        strat_name = f"Hybrid_Strong+MC / {exit_name}"
        result, pf = run_backtest(df_5y, entries, exits_combined, strat_name)
        all_results.append(result)
        print(f"  {exit_name if exit_name else 'No Filter':20s} | WR: {result['win_rate']*100:5.1f}% | Trades: {result['total_trades']:4d} | Ret: {result['total_return']*100:7.1f}% | Sharpe: {result['sharpe_ratio']:6.3f} | MaxDD: {result['max_drawdown']*100:6.1f}%")

    # =====================================================================
    # Group 6: ADX Momentum Filter (Strong trend confirmation)
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 6: ADX Momentum Filter")
    print("=" * 80)

    def signal_adx_strong(df):
        """Strong trend filter: ADX>25, +DI>-DI, plus momentum composite."""
        adx_filter = (
            (df["ta_adx14"] > 25)
            & (df["ta_plus_di14"] > df["ta_minus_di14"])
        )
        momentum = signal_momentum_composite(df)
        entries = momentum[0] & adx_filter
        return entries, momentum[1]

    adx_exit_fns = {
        "Default": None,
        "ATR Trail 2x": exit_atr_trail_entry2,
        "RSI > 65": exit_rsi_overbought65,
        "Combo": exit_combo_mc,
    }

    adx_results = run_strategy_group(df_5y, "ADX_Strong", signal_adx_strong, adx_exit_fns)
    all_results.extend(adx_results)

    # =====================================================================
    # Group 7: RSI Pullback Strategies
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 7: RSI Pullback in Uptrend")
    print("=" * 80)

    def signal_rsi_pullback(df):
        """Buy RSI dips (35-45) in uptrend, exit RSI>60."""
        uptrend = (df["Close"] > df["ta_ema200"]) & (df["ma200_slope_20d"] > 0)
        dip = (df["ta_rsi14"] >= 35) & (df["ta_rsi14"] <= 45)
        bounce = (df["ta_rsi14"] > 45) & (df["ta_rsi14"] <= 55) & (df["ta_macd_line"] > df["ta_macd_signal"])
        entries = bounce & uptrend & dip.shift(1)
        exits = df["ta_rsi14"] > 65
        return entries.astype(int), exits.astype(int) * -1

    def signal_rsi_deep_pullback(df):
        """Buy deeper RSI dips (25-40) in uptrend."""
        uptrend = (df["Close"] > df["ta_ema200"]) & (df["ma200_slope_20d"] > 0)
        deep_dip = (df["ta_rsi14"] >= 25) & (df["ta_rsi14"] <= 40)
        bounce = (df["ta_rsi14"] > 40) & (df["ta_rsi14"] <= 50) & (df["ta_roc20"] > 0)
        entries = bounce & uptrend & deep_dip.shift(1)
        exits = df["ta_rsi14"] > 60
        return entries.astype(int), exits.astype(int) * -1

    for name, signal_fn in [
        ("RSI_Pullback_35-45", signal_rsi_pullback),
        ("RSI_DeepPullback_25-40", signal_rsi_deep_pullback),
    ]:
        entries, exits = signal_fn(df_5y)
        print(f"\n  {name}: {entries.sum()} entries ({entries.mean()*100:.1f}%)")

        for exit_name, exit_fn in {
            "Default": None,
            "ATR Trail 2x": exit_atr_trail_entry2,
            "ATR Trail 3x": exit_atr_trail_entry3,
            "RSI > 60": lambda df: exit_rsi_overbought(df, 60),
            "RSI > 65": exit_rsi_overbought65,
            "RSI > 70": exit_rsi_overbought70,
            "Combo": exit_combo_mc,
        }.items():
            strat_name = f"{name} / {exit_name}"
            if exit_fn is not None:
                exits_combined = exits | exit_fn(df_5y)
            else:
                exits_combined = exits
            result, pf = run_backtest(df_5y, entries, exits_combined, strat_name)
            all_results.append(result)
            print(f"    {exit_name:20s} | WR: {result['win_rate']*100:5.1f}% | Trades: {result['total_trades']:4d} | Ret: {result['total_return']*100:7.1f}% | Sharpe: {result['sharpe_ratio']:6.3f} | MaxDD: {result['max_drawdown']*100:6.1f}%")

    # =====================================================================
    # Summary
    # =====================================================================
    print("\n" + "=" * 80)
    print("SUMMARY - All Results Sorted by Total Return")
    print("=" * 80)

    # Sort by return descending, then win rate
    all_results.sort(key=lambda x: (x["total_return"], x["win_rate"]), reverse=True)

    print(
        f"{'Strategy':<55} {'WR':>6} {'Trades':>7} {'Return':>8} {'AnnRet':>8} "
        f"{'Sharpe':>7} {'MaxDD':>7} {'PF':>6}"
    )
    print("-" * 110)
    for r in all_results:
        print(
            f"{r['name']:<55} "
            f"{r['win_rate']*100:5.1f}% "
            f"{r['total_trades']:4d} "
            f"{r['total_return']*100:7.1f}% "
            f"{r['annualized_return']*100:7.1f}% "
            f"{r['sharpe_ratio']:6.3f} "
            f"{r['max_drawdown']*100:6.1f}% "
            f"{r['profit_factor']:5.2f}"
        )

    # Top 15 by return (min 3 trades)
    print("\n" + "-" * 80)
    print("TOP 15 BY TOTAL RETURN (min 3 trades):")
    print("-" * 80)
    filtered = [r for r in all_results if r["total_trades"] >= 3]
    filtered.sort(key=lambda x: (x["total_return"], x["win_rate"]), reverse=True)

    print(
        f"{'Rank':<5} {'Strategy':<55} {'Return':>8} {'WR':>6} {'Trades':>7} {'Sharpe':>7}"
    )
    print("-" * 80)
    for i, r in enumerate(filtered[:15], 1):
        print(
            f"{i:<5} {r['name']:<55} "
            f"{r['total_return']*100:7.1f}% "
            f"{r['win_rate']*100:5.1f}% "
            f"{r['total_trades']:4d} "
            f"{r['sharpe_ratio']:6.3f}"
        )

    # Top 15 by Sharpe (min 3 trades)
    print("\n" + "-" * 80)
    print("TOP 15 BY SHARPE RATIO (min 3 trades, Sharpe > -1):")
    print("-" * 80)
    filtered_sharpe = [r for r in all_results if r["total_trades"] >= 3 and r["sharpe_ratio"] > -1]
    filtered_sharpe.sort(key=lambda x: x["sharpe_ratio"], reverse=True)

    print(
        f"{'Rank':<5} {'Strategy':<55} {'Sharpe':>7} {'Return':>8} {'WR':>6} {'MaxDD':>7}"
    )
    print("-" * 80)
    for i, r in enumerate(filtered_sharpe[:15], 1):
        print(
            f"{i:<5} {r['name']:<55} "
            f"{r['sharpe_ratio']:6.3f} "
            f"{r['total_return']*100:7.1f}% "
            f"{r['win_rate']*100:5.1f}% "
            f"{r['max_drawdown']*100:6.1f}%"
        )

    # =====================================================================
    # Generate Reports
    # =====================================================================
    print("\n" + "=" * 80)
    print("GENERATING REPORTS")
    print("=" * 80)

    # Pick top 5 strategies by return (with min 5 trades filter)
    top_by_ret = [r for r in all_results if r["total_trades"] >= 5]
    top_by_ret.sort(key=lambda x: (x["total_return"], x["win_rate"]), reverse=True)
    top5 = top_by_ret[:5]

    # Also pick best Sharpe (with min 5 trades)
    best_sharpe = [r for r in all_results if r["total_trades"] >= 5 and r["sharpe_ratio"] > -1]
    best_sharpe.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
    if best_sharpe:
        seen_names = {r["name"] for r in top5}
        if best_sharpe[0]["name"] not in seen_names:
            top5.append(best_sharpe[0])

    benchmark_ret = df_5y["Close"].pct_change().dropna()

    for i, result in enumerate(top5):
        name = result["name"]
        # Re-run to get portfolio object
        entries, exits = signal_momentum_composite(df_5y)
        pf_obj = None

        # Try to match the strategy
        if "Hybrid_Strong" in name:
            entries, _ = signal_hybrid_strong(df_5y)
            if "ATR Trail 2x" in name:
                exits = exit_atr_trail_entry2(df_5y)
            elif "Combo" in name:
                exits = exit_combo_mc(df_5y)
            elif "RSI > 65" in name:
                exits = exit_rsi_overbought65(df_5y)
        elif "Pullback" in name:
            if "20" in name:
                entries, exits = signal_pullback_to_ema20(df_5y)
            elif "50" in name:
                entries, exits = signal_pullback_to_ema50(df_5y)
        elif "RSI_Pullback" in name:
            entries, exits = signal_rsi_pullback(df_5y)
        elif "RSI_DeepPullback" in name:
            entries, exits = signal_rsi_deep_pullback(df_5y)
        elif "ADX_Strong" in name:
            entries, _ = signal_adx_strong(df_5y)
        elif "Momentum_Composite" in name:
            entries, exits = signal_momentum_composite(df_5y)
        elif "Buy & Hold" in name:
            entries, exits = signal_buy_and_hold(df_5y)

        try:
            pf_obj = vbt.Portfolio.from_signals(
                close=df_5y["Close"], entries=entries, exits=exits,
                init_cash=INITIAL_CAPITAL, slippage=SLIPPAGE, freq="1D",
            )
            strategy_ret = pf_obj.daily_returns().dropna()
            common_idx = strategy_ret.index.intersection(benchmark_ret.index)

            if len(common_idx) > 100:
                out_path = OUTPUT_DIR / f"AZN_{name.replace('/', '_').replace('+', '_').replace(' ', '_')}.html"
                qs.reports.html(
                    strategy_ret.loc[common_idx],
                    benchmark=benchmark_ret.loc[common_idx],
                    title=f"AZN.L - {name}",
                    output=str(out_path),
                    figsize=(1200, 800),
                )
                print(f"  [{i+1}] Tearsheet: {name} -> {out_path}")
        except Exception as e:
            print(f"  [{i+1}] Error generating {name}: {e}")

    # Generate comparison summary
    print(f"\n  Generating comparison tearsheet for top {len(top5)} strategies...")
    try:
        returns_data = {}
        for result in top5:
            name = result["name"]
            entries, exits = signal_momentum_composite(df_5y)

            if "Hybrid_Strong" in name:
                entries, _ = signal_hybrid_strong(df_5y)
                if "ATR Trail 2x" in name:
                    exits = exit_atr_trail_entry2(df_5y)
                elif "Combo" in name:
                    exits = exit_combo_mc(df_5y)
                elif "RSI > 65" in name:
                    exits = exit_rsi_overbought65(df_5y)
            elif "Pullback" in name:
                if "20" in name:
                    entries, exits = signal_pullback_to_ema20(df_5y)
                elif "50" in name:
                    entries, exits = signal_pullback_to_ema50(df_5y)
            elif "RSI_Pullback" in name:
                entries, exits = signal_rsi_pullback(df_5y)
            elif "RSI_DeepPullback" in name:
                entries, exits = signal_rsi_deep_pullback(df_5y)
            elif "ADX_Strong" in name:
                entries, _ = signal_adx_strong(df_5y)
            elif "Buy & Hold" in name:
                entries, exits = signal_buy_and_hold(df_5y)

            pf_tmp = vbt.Portfolio.from_signals(
                close=df_5y["Close"], entries=entries, exits=exits,
                init_cash=INITIAL_CAPITAL, slippage=SLIPPAGE, freq="1D",
            )
            strategy_ret = pf_tmp.daily_returns().dropna()
            common_idx = strategy_ret.index.intersection(benchmark_ret.index)
            if len(common_idx) > 100:
                clean_name = name.replace(">", "GT").replace("<", "LT").replace("/", "_").replace("+", "_").replace(" ", "_")
                returns_data[clean_name] = strategy_ret.loc[common_idx]

        if returns_data:
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.loc[benchmark_ret.index.intersection(returns_df.index)]
            out_path = OUTPUT_DIR / "AZN_backtest_summary_v2.html"
            qs.reports.html(
                returns_df,
                benchmark=benchmark_ret.loc[returns_df.index.intersection(benchmark_ret.index)],
                title="AZN.L - Multi-Strategy Comparison v2",
                output=str(out_path),
            )
            print(f"    Comparison: {out_path}")
    except Exception as e:
        print(f"    Error generating comparison: {e}")
        import traceback
        traceback.print_exc()

    # Save raw results CSV
    print(f"\n  Saving results CSV...")
    import csv
    results_path = OUTPUT_DIR / "AZN_backtest_results_v2.csv"
    fieldnames = list(all_results[0].keys())
    with open(results_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
    print(f"    Results CSV: {results_path}")

    print("\n" + "=" * 80)
    print("BACKTEST V2 COMPLETE")
    print("=" * 80)

    return all_results


if __name__ == "__main__":
    results = main()


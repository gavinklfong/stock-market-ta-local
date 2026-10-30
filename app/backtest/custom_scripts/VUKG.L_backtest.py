"""
VUKG.L (Vanguard FTSE 100 UCITS ETF) Backtest - Multi-strategy evaluation with vectorbt.

Strategies tested on data/analysis-data/VUKG.L.csv (OHLCV + all TA + P/E):

VUKG.L is a broad UK market ETF tracking the FTSE 100.
Profile: ~92.9% total return over 7.5y (~9.2% annualized), 15.9% vol, max DD -34.3%.
65.5% of time in uptrend (EMA20>50>200), SuperTrend+1 71.9% of time.
ADX mean 21.3 (moderate trending) -- trend-following works best with tight exits.

  --- Trend-Following Strategies ---
   1. GoldenCross    - EMA20>EMA50>EMA200, MA20 slope>0, SuperTrend+1, RSI>50, MACD>Signal
   2. EMAPullback    - EMA20>EMA50>EMA200, price near EMA20, RSI 40-55, SuperTrend+1
   3. SuperTrendEMA  - SuperTrend flip up + EMA20>EMA50 + RSI>40 filter
   4. VWAPTrend      - Close > VWAP, VWAP rising, RSI>50, ADX>20
   5. BOSBreakout    - BOS=1, Close>DonchianUpper, CMF>0 or OFI>0
   6. ADXMomentum    - ADX>25, +DI>-DI, RSI>50, MACD>Signal

  --- Composite / Multi-Factor Strategies ---
   7. MomentumComp   - RSI>55, MACD>Signal, ROC20>0, W%R>-50, CMF>0, EMA20>EMA50
   8. HighProbMulti  - Full checklist: EMA20>50, RSI>50, MACD>Signal, CMF>0, OFI>0, BOS
   9. Score3+        - Signal scoring >= 3 (of 6): EMA, RSI, MACD, CMF, OFI, ADX

  --- Exit Criteria Optimization Strategies ---
  10. GC_ExitST      - Golden Cross, exit on SuperTrend flip only
  11. GC_ExitEMA50   - Golden Cross, exit on Close < EMA50
  12. GC_ExitRSI70   - Golden Cross, exit on RSI>70
  13. GC_ExitRSI75   - Golden Cross, exit on RSI>75
  14. GC_ExitBBU     - Golden Cross, exit on Close > BB Upper
  15. GC_ExitATR3    - Golden Cross, exit on ATR trailing stop (3xATR, 10d)
  16. GC_ExitATR2    - Golden Cross, exit on ATR trailing stop (2xATR, 10d)
  17. GC_ExitCombo   - Golden Cross, exit on ST flip OR EMA cross OR RSI>75
  18. GC_ExitRSIWeak - Golden Cross, exit on RSI<45 (momentum loss)

  19. EP_ExitEMA50   - EMA Pullback, exit on Close < EMA50
  20. EP_ExitRSI65   - EMA Pullback, exit on RSI>65
  21. EP_ExitRSI70   - EMA Pullback, exit on RSI>70
  22. EP_ExitATR3    - EMA Pullback, exit on ATR trailing (3xATR, 10d)
  23. EP_ExitST      - EMA Pullback, exit on SuperTrend flip
  24. EP_ExitEMA20   - EMA Pullback, exit on EMA20<EMA50
  25. EP_ExitCombo   - EMA Pullback, exit on ST flip OR EMA cross OR RSI>75
  26. EP_ExitRSIWeak - EMA Pullback, exit on RSI<45

  --- Adaptive / Regime-Based ---
  27. HMMBull        - HMM regime 0 dominant + RSI>50 + MACD>Signal
  28. ScoreAdapt     - Dynamic scoring with regime awareness (regime 0 boost)
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

# Ensure we can import local modules
sys.path.insert(0, str(Path(__file__).parent / ".." / "calculate_ta"))

# Configuration
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "analysis-data" / "VUKG.L.csv"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "reports" / "backtest"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INITIAL_CAPITAL = 100000
SLIPPAGE = 0.001  # 0.1% slippage per trade


# =============================================================================
# Data Loading
# =============================================================================


def load_data():
    """Load VUKG.L analysis data with all TA indicators."""
    df = pd.read_csv(DATA_PATH)

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")

    # Drop rows with NaN in critical columns
    critical = ["Close", "High", "Low", "Open", "Volume"]
    df = df.dropna(subset=critical)

    print(f"Loaded {len(df)} rows: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Close range: {df['Close'].min():.2f} to {df['Close'].max():.2f}")
    print(f"Total return: {(df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100:.1f}%")
    print(f"Volatility (annualized): {(df['Close'].pct_change().std() * np.sqrt(252) * 100):.1f}%")
    return df


# =============================================================================
# Signal Generation Functions
# =============================================================================


def signal_goldencross(df):
    """Golden Cross: EMA20>EMA50>EMA200, MA20 slope>0, ST+1, RSI>50, MACD>Signal."""
    entry = (
        (df["ta_ema20"] > df["ta_ema50"])
        & (df["ta_ema50"] > df["ta_ema200"])
        & (df["ta_ma20_slope"] > 0)
        & (df["ta_supertrend_direction"] == 1)
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    exit_ = (
        (df["ta_ema20"] < df["ta_ema50"])
        | (df["ta_supertrend_direction"] == -1)
        | (df["ta_rsi14"] < 45)
    )
    return entry.astype(int), exit_.astype(int) * -1


def signal_emapullback(df):
    """EMA Pullback: EMA20>EMA50>EMA200, price near EMA20, RSI 40-55, ST+1."""
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03
    entry = (
        (df["ta_ema20"] > df["ta_ema50"])
        & (df["ta_ema50"] > df["ta_ema200"])
        & (near_ema20)
        & (df["ta_rsi14"] >= 40)
        & (df["ta_rsi14"] <= 55)
        & (df["ta_supertrend_direction"] == 1)
    )
    exit_ = (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 70)
    return entry.astype(int), exit_.astype(int) * -1


def signal_supertrend_ema(df):
    """SuperTrend+EMA: SuperTrend flip up + EMA20>EMA50 + RSI>40."""
    st = df["ta_supertrend_direction"]
    flip_up = (st == 1) & (st.shift(1) == -1)
    entry = flip_up & (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_rsi14"] > 40)
    exit_ = (df["ta_supertrend_direction"] == -1) | (df["ta_ema20"] < df["ta_ema50"])
    return entry.astype(int), exit_.astype(int) * -1


def signal_vwap_trend(df):
    """VWAP Trend: Close > VWAP, VWAP rising, RSI>50, ADX>20."""
    entry = (
        (df["Close"] > df["ta_vwap"])
        & (df["ta_vwap"] > df["ta_vwap"].shift(1))
        & (df["ta_rsi14"] > 50)
        & (df["ta_adx14"] > 20)
    )
    exit_ = (df["Close"] < df["ta_vwap"]) | (df["ta_adx14"] < 20)
    return entry.astype(int), exit_.astype(int) * -1


def signal_bos_breakout(df):
    """BOS Breakout: BOS=1, Close>DonchianUpper, CMF>0 or OFI>0."""
    entry = (
        (df["ta_bos"].fillna(0).astype(int) == 1)
        & (df["Close"] > df["ta_donchian_upper"])
        & ((df["ta_cmf"] > 0) | (df["ta_ofi"] > 0))
    )
    exit_ = df["Close"] < df["ta_donchian_upper"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_adx_momentum(df):
    """ADX Momentum: ADX>25, +DI>-DI, RSI>50, MACD>Signal."""
    entry = (
        (df["ta_adx14"] > 25)
        & (df["ta_plus_di14"] > df["ta_minus_di14"])
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    exit_ = (df["ta_adx14"] < 20) | (df["ta_rsi14"] < 45)
    return entry.astype(int), exit_.astype(int) * -1


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


def signal_high_prob_multi(df):
    """High Probability Multi: Full checklist for highest confidence entries."""
    entry = (
        (df["ta_ema20"] > df["ta_ema50"])
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
        & (df["ta_cmf"] > 0)
        & (df["ta_ofi"] > 0)
        & (df["ta_bos"].fillna(0).astype(int) == 1)
    )
    exit_ = (
        (df["ta_supertrend_direction"] == -1)
        | (df["ta_rsi14"] < 50)
        | (df["Close"] < df["ta_ema50"])
    )
    return entry.astype(int), exit_.astype(int) * -1


def signal_score_entry(df, min_score=3):
    """Signal Score: 0-6 score based on confluence. >= min_score triggers entry."""
    score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int)
        + (df["ta_rsi14"] > 50).astype(int)
        + (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int)
        + (df["ta_cmf"] > 0).astype(int)
        + (df["ta_ofi"] > 0).astype(int)
        + (df["ta_adx14"] > 20).astype(int)
    )
    entry = score >= min_score
    exit_ = score < (min_score - 2)
    return entry.astype(int), exit_.astype(int) * -1


def signal_hmm_bull(df):
    """HMM Bull: Regime 0 dominant + RSI>50 + MACD>Signal."""
    regime_0 = df["ta_hmm_regime_prob_0"] > df["ta_hmm_regime_prob_1"]
    regime_0 = regime_0 & (df["ta_hmm_regime_prob_0"] > df["ta_hmm_regime_prob_2"])
    entry = (
        regime_0
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    regime_1 = ~regime_0
    exit_ = regime_1 | (df["ta_rsi14"] < 45)
    return entry.astype(int), exit_.astype(int) * -1


def signal_score_adaptive(df):
    """Adaptive Score: Different thresholds based on HMM regime."""
    score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int)
        + (df["ta_ema50"] > df["ta_ema200"]).astype(int)
        + (df["ta_rsi14"] > 50).astype(int)
        + (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int)
        + (df["ta_cmf"] > 0).astype(int)
        + (df["ta_ofi"] > 0).astype(int)
        + (df["ta_adx14"] > 20).astype(int)
    )
    regime_0 = df["ta_hmm_regime_prob_0"] > df["ta_hmm_regime_prob_1"]
    regime_0 = regime_0 & (df["ta_hmm_regime_prob_0"] > df["ta_hmm_regime_prob_2"])
    threshold = np.where(regime_0, 3, 4)
    entry = score >= threshold
    exit_ = score < 2
    return entry.astype(int), exit_.astype(int) * -1


# =============================================================================
# Exit Signal Generation Functions
# =============================================================================


def exit_supertrend_flip(df):
    """Exit when SuperTrend flips down."""
    return df["ta_supertrend_direction"] == -1


def exit_ema20_cross(df):
    """Exit when EMA20 crosses below EMA50."""
    return df["ta_ema20"] < df["ta_ema50"]


def exit_ema50_cross(df):
    """Exit when Close crosses below EMA50."""
    return df["Close"] < df["ta_ema50"]


def exit_rsi_overbought(df, threshold=70):
    """Exit when RSI > threshold (overbought)."""
    return df["ta_rsi14"] > threshold


def exit_rsi_weakness(df, threshold=45):
    """Exit when RSI drops below threshold (momentum loss)."""
    return df["ta_rsi14"] < threshold


def exit_bb_upper(df):
    """Exit when Close > BB Upper (momentum exhaustion)."""
    return df["Close"] > df["ta_bband_upper"]


def exit_atr_trail(df, atr_mult=3, lookback=10):
    """Exit when price falls below trailing stop: highest high - atr_mult * ATR."""
    highest_high = df["High"].rolling(lookback).max()
    stop = highest_high - atr_mult * df["ta_atr14"]
    return df["Close"] < stop


def exit_combo_st_ema_rsi(df):
    """Exit on SuperTrend flip OR EMA20<EMA50 OR RSI>75."""
    return (
        (df["ta_supertrend_direction"] == -1)
        | (df["ta_ema20"] < df["ta_ema50"])
        | (df["ta_rsi14"] > 75)
    )


# =============================================================================
# Backtest Engine
# =============================================================================


def run_backtest(df, entries, exits=None, name="", initial_capital=INITIAL_CAPITAL):
    """
    Run a vectorbt backtest with the given entry/exit signals.

    Args:
        df: DataFrame with OHLCV and TA columns
        entries: boolean or int Series of entry signals
        exits: boolean or int Series of exit signals (optional)
        name: Strategy name for reporting
        initial_capital: Starting capital

    Returns:
        tuple: (dict with backtest results, vbt.Portfolio)
    """
    # Ensure entries and exits align to df index
    entries = pd.Series(entries).reindex(df.index).fillna(False).astype(int)
    if exits is not None:
        exits = pd.Series(exits).reindex(df.index).fillna(False).astype(int)

    # Create Portfolio
    pf = vbt.Portfolio.from_signals(
        close=df["Close"],
        entries=entries,
        exits=exits,
        init_cash=initial_capital,
        slippage=SLIPPAGE,
        freq="1D",
    )

    # Extract metrics from pf.stats() DataFrame
    stats = pf.stats()
    total_return = stats.get("Total Return [%]", 0)
    win_rate = stats.get("Win Rate [%]", 0)
    total_trades = int(stats.get("Total Trades", 0))
    profit_factor = stats.get("Profit Factor", 0)
    max_drawdown = stats.get("Max Drawdown [%]", 0)
    sharpe_ratio = stats.get("Sharpe Ratio", 0)
    calmar_ratio = stats.get("Calmar Ratio", 0)
    avg_drawdown = stats.get("Average Drawdown [%]", 0)

    # Calculate annualized return
    n_days = len(df)
    annualized_return = (1 + total_return / 100) ** (252 / n_days) - 1 if n_days > 0 else 0

    # Count winning/losing trades
    winning_trades = 0
    losing_trades = 0
    if total_trades > 0:
        winning_trades = int(round(total_trades * win_rate / 100))
        losing_trades = total_trades - winning_trades

    results = {
        "name": name,
        "total_return": total_return / 100,
        "annualized_return": annualized_return,
        "win_rate": win_rate / 100,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown / 100,
        "sharpe_ratio": sharpe_ratio,
        "calmar_ratio": calmar_ratio,
        "avg_drawdown": avg_drawdown / 100,
        "final_value": pf.final_value(),
        "entry_count": int(entries.sum()),
    }

    return results, pf


# =============================================================================
# Strategy Group Runner
# =============================================================================


def run_strategy_group(df, group_name, entry_fn, exit_fns, group_exit_name=""):
    """
    Run a group of strategies with the same entry but different exits.

    Args:
        df: DataFrame
        group_name: Group name (e.g., "Golden Cross")
        entry_fn: Function returning (entries, default_exits) tuple
        exit_fns: Dict of exit_name -> exit_signal_function (boolean)
        group_exit_name: Optional suffix for exit names

    Returns:
        List of results dicts
    """
    entries, default_exits = entry_fn(df)
    print(f"\n  {group_name}: {entries.sum()} entries ({entries.mean()*100:.1f}%)")

    results = []
    for exit_name, exit_fn in exit_fns.items():
        name = f"{group_name} / {exit_name}" if group_exit_name else f"{group_name}"

        if exit_fn is not None:
            extra_exits = exit_fn(df)
            exits = default_exits | extra_exits
        else:
            exits = default_exits

        result, pf = run_backtest(df, entries, exits, name)
        results.append(result)

        print(
            f"    {exit_name or 'No exit filter':20s} | "
            f"WinRate: {result['win_rate']*100:5.1f}% | "
            f"Trades: {result['total_trades']:4d} | "
            f"Return: {result['total_return']*100:7.1f}% | "
            f"Sharpe: {result['sharpe_ratio']:6.3f} | "
            f"MaxDD: {result['max_drawdown']*100:6.1f}%"
        )

    return results


def run_single_strategy(df, name, entry_fn, exit_fn=None):
    """Run a single strategy with specific entry and exit."""
    entries, default_exits = entry_fn(df)

    if exit_fn is not None:
        exits = exit_fn(df)
    else:
        exits = default_exits

    result, pf = run_backtest(df, entries, exits, name)
    print(
        f"  {name:30s} | "
        f"WinRate: {result['win_rate']*100:5.1f}% | "
        f"Trades: {result['total_trades']:4d} | "
        f"Return: {result['total_return']*100:7.1f}% | "
        f"Sharpe: {result['sharpe_ratio']:6.3f} | "
        f"MaxDD: {result['max_drawdown']*100:6.1f}%"
    )
    return result, pf


# =============================================================================
# Main Backtest Runner
# =============================================================================


def main():
    print("=" * 80)
    print("VUKG.L (Vanguard FTSE 100 UCITS ETF) Backtest")
    print("=" * 80)

    # Load data
    df = load_data()

    # Baseline: bought and held
    bh_ret = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
    bh_sharpe = (df["Close"].pct_change().mean() * 252 - 0.02) / (df["Close"].pct_change().std() * np.sqrt(252))
    print(f"\n  Baseline - Bought & Held: Return: {bh_ret:.1f}%, Sharpe: {bh_sharpe:.3f}")

    # =====================================================================
    # Group 1: Golden Cross with Different Exit Criteria
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 1: Golden Cross Exit Optimization")
    print("=" * 80)

    gc_exits = {
        "No Filter": None,
        "ST Flip": exit_supertrend_flip,
        "EMA50 Cross": exit_ema50_cross,
        "RSI > 70": lambda df: exit_rsi_overbought(df, 70),
        "RSI > 75": lambda df: exit_rsi_overbought(df, 75),
        "BB Upper": exit_bb_upper,
        "ATR Trail (3x,10d)": lambda df: exit_atr_trail(df, 3, 10),
        "ATR Trail (2x,10d)": lambda df: exit_atr_trail(df, 2, 10),
        "ST + EMA + RSI>75": exit_combo_st_ema_rsi,
        "RSI Weakness (<45)": lambda df: exit_rsi_weakness(df, 45),
    }

    gc_results = run_strategy_group(df, "Golden Cross", signal_goldencross, gc_exits)

    # =====================================================================
    # Group 2: EMA Pullback with Different Exit Criteria
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 2: EMA Pullback Exit Optimization")
    print("=" * 80)

    ep_exits = {
        "No Filter": None,
        "Close < EMA50": exit_ema50_cross,
        "RSI > 65": lambda df: exit_rsi_overbought(df, 65),
        "RSI > 70": lambda df: exit_rsi_overbought(df, 70),
        "ATR Trail (3x,10d)": lambda df: exit_atr_trail(df, 3, 10),
        "ST Flip": exit_supertrend_flip,
        "EMA20 Cross": exit_ema20_cross,
        "ST + EMA + RSI>75": exit_combo_st_ema_rsi,
        "RSI Weakness (<45)": lambda df: exit_rsi_weakness(df, 45),
    }

    ep_results = run_strategy_group(df, "EMA Pullback", signal_emapullback, ep_exits)

    # =====================================================================
    # Group 3: SuperTrend+EMA with Different Exit Criteria
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 3: SuperTrend+EMA Exit Optimization")
    print("=" * 80)

    st_exits = {
        "No Filter": None,
        "ST Flip": exit_supertrend_flip,
        "EMA20 Cross": exit_ema20_cross,
        "EMA50 Cross": exit_ema50_cross,
        "RSI > 70": lambda df: exit_rsi_overbought(df, 70),
        "RSI > 65": lambda df: exit_rsi_overbought(df, 65),
        "ATR Trail (3x,10d)": lambda df: exit_atr_trail(df, 3, 10),
        "ST + EMA + RSI>75": exit_combo_st_ema_rsi,
        "RSI Weakness (<45)": lambda df: exit_rsi_weakness(df, 45),
    }

    st_results = run_strategy_group(df, "SuperTrend+EMA", signal_supertrend_ema, st_exits)

    # =====================================================================
    # Group 4: Individual Trend Strategies (no exit optimization)
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 4: Individual Trend Strategies")
    print("=" * 80)

    individual = [
        ("VWAP Trend", signal_vwap_trend),
        ("BOS Breakout", signal_bos_breakout),
        ("ADX Momentum", signal_adx_momentum),
    ]

    for name, entry_fn in individual:
        run_single_strategy(df, name, entry_fn)

    # =====================================================================
    # Group 5: Composite / Multi-Factor Strategies
    # =====================================================================
    print("\n" + "=" * 80)
    print("GROUP 5: Composite Strategies")
    print("=" * 80)

    composite = [
        ("Momentum Composite", signal_momentum_composite),
        ("High Prob Multi", signal_high_prob_multi),
        ("Score 3+", lambda df: signal_score_entry(df, 3)),
        ("Score 4+", lambda df: signal_score_entry(df, 4)),
        ("HMM Bull", signal_hmm_bull),
        ("Score Adaptive", signal_score_adaptive),
    ]

    for name, entry_fn in composite:
        run_single_strategy(df, name, entry_fn)

    # =====================================================================
    # Summary
    # =====================================================================
    print("\n" + "=" * 80)
    print("SUMMARY - All Results Sorted by Win Rate")
    print("=" * 80)

    all_results = list(gc_results) + list(ep_results) + list(st_results)

    for name, entry_fn in individual:
        result, _ = run_single_strategy(df, name, entry_fn)
        all_results.append(result)

    for name, entry_fn in composite:
        result, _ = run_single_strategy(df, name, entry_fn)
        all_results.append(result)

    # Sort by win rate descending, then by total return
    all_results.sort(key=lambda x: (x["win_rate"], x["total_return"]), reverse=True)

    print(
        f"{'Strategy':<45} {'WR':>6} {'Trades':>7} {'Win':>5} {'Lose':>5} "
        f"{'Return':>8} {'AnnRet':>8} {'PF':>6} {'Sharpe':>7} {'MaxDD':>7}"
    )
    print("-" * 110)
    for r in all_results:
        print(
            f"{r['name']:<45} "
            f"{r['win_rate']*100:5.1f}% "
            f"{r['total_trades']:4d} "
            f"{r['winning_trades']:3d} "
            f"{r['losing_trades']:3d} "
            f"{r['total_return']*100:6.1f}% "
            f"{r['annualized_return']*100:6.1f}% "
            f"{r['profit_factor']:5.2f} "
            f"{r['sharpe_ratio']:6.3f} "
            f"{r['max_drawdown']*100:5.1f}%"
        )

    # Top 10 by win rate (with min 10 trades filter)
    print("\n" + "-" * 80)
    print("TOP 10 BY WIN RATE (min 10 trades):")
    print("-" * 80)
    filtered = [r for r in all_results if r["total_trades"] >= 10]
    filtered.sort(key=lambda x: (x["win_rate"], x["total_return"]), reverse=True)

    print(
        f"{'Rank':<5} {'Strategy':<45} {'WR':>6} {'Trades':>7} {'Return':>8} {'Sharpe':>7}"
    )
    print("-" * 80)
    for i, r in enumerate(filtered[:10], 1):
        print(
            f"{i:<5} {r['name']:<45} "
            f"{r['win_rate']*100:5.1f}% "
            f"{r['total_trades']:4d} "
            f"{r['total_return']*100:6.1f}% "
            f"{r['sharpe_ratio']:6.3f}"
        )

    # Top 10 by return (with min 10 trades filter)
    print("\n" + "-" * 80)
    print("TOP 10 BY TOTAL RETURN (min 10 trades):")
    print("-" * 80)
    filtered.sort(key=lambda x: x["total_return"], reverse=True)
    print(
        f"{'Rank':<5} {'Strategy':<45} {'Return':>8} {'WR':>6} {'Trades':>7} {'Sharpe':>7}"
    )
    print("-" * 80)
    for i, r in enumerate(filtered[:10], 1):
        print(
            f"{i:<5} {r['name']:<45} "
            f"{r['total_return']*100:6.1f}% "
            f"{r['win_rate']*100:5.1f}% "
            f"{r['total_trades']:4d} "
            f"{r['sharpe_ratio']:6.3f}"
        )

    # =====================================================================
    # Generate Reports
    # =====================================================================
    print("\n" + "=" * 80)
    print("GENERATING REPORTS")
    print("=" * 80)

    # Build signal dict from individual + composite
    strategy_signals = {}
    for name, entry_fn in individual:
        entries, exits = entry_fn(df)
        strategy_signals[name] = (entries, exits)

    for name, entry_fn in composite:
        entries, exits = entry_fn(df)
        strategy_signals[name] = (entries, exits)

    # Add group exit variants
    for group_name, signal_fn, exit_fns in [
        ("Golden Cross", signal_goldencross, gc_exits),
        ("EMA Pullback", signal_emapullback, ep_exits),
        ("SuperTrend+EMA", signal_supertrend_ema, st_exits),
    ]:
        entries, default_exits = signal_fn(df)
        for exit_name, exit_fn in exit_fns.items():
            if exit_fn is not None:
                exits = default_exits | exit_fn(df)
            else:
                exits = default_exits
            variant_name = f"{group_name} / {exit_name}"
            strategy_signals[variant_name] = (entries, exits)

    # Pick top strategies by win rate (min 5 trades)
    top_by_wr = []
    for name, (entries, exits) in strategy_signals.items():
        r, pf = run_backtest(df, entries, exits, name)
        if r["total_trades"] >= 5:
            top_by_wr.append((name, pf, r))

    top_by_wr.sort(key=lambda x: (x[2]["win_rate"], x[2]["total_return"]), reverse=True)
    top5 = top_by_wr[:5]

    for i, (name, pf, result) in enumerate(top5):
        print(f"\n  [{i+1}] {name} (WR: {result['win_rate']*100:.1f}%, Return: {result['total_return']*100:.1f}%)")
        try:
            strategy_ret = pf.daily_returns().dropna()
            benchmark_ret = df["Close"].pct_change().dropna()
            common_idx = strategy_ret.index.intersection(benchmark_ret.index)

            out_path = OUTPUT_DIR / f"{name.replace(' ', '_').replace('/', '_')}.html"
            qs.reports.html(
                strategy_ret.loc[common_idx],
                benchmark=benchmark_ret.loc[common_idx],
                title=f"VUKG.L - {name}",
                output=str(out_path),
                figsize=(1200, 800),
            )
            print(f"    Tearsheet: {out_path}")
        except Exception as e:
            print(f"    Error: {e}")

    # Also generate a summary comparison for top 5 by return
    print(f"\n  Generating comparison tearsheet for top 5 strategies...")
    try:
        top_by_ret = sorted(top_by_wr, key=lambda x: x[2]["total_return"], reverse=True)[:5]

        benchmark_ret = df["Close"].pct_change().dropna()
        returns_data = {}

        for name, pf, _ in top_by_ret:
            strategy_ret = pf.daily_returns().dropna()
            common_idx = strategy_ret.index.intersection(benchmark_ret.index)
            if len(common_idx) > 0:
                returns_data[name] = strategy_ret.loc[common_idx]

        if returns_data:
            returns_df = pd.DataFrame(returns_data)
            common_idx = returns_df.index.intersection(benchmark_ret.index)
            returns_df = returns_df.loc[common_idx]
            benchmark_aligned = benchmark_ret.loc[common_idx]

            # Clean column names for quantstats compatibility
            returns_df.columns = [c.replace(">", "GT").replace("<", "LT").replace("/", "_") for c in returns_df.columns]

            out_path = OUTPUT_DIR / "VUKG.L_backtest_summary.html"
            qs.reports.html(
                returns_df,
                benchmark=benchmark_aligned,
                title="VUKG.L - Multi-Strategy Comparison (Top 5)",
                output=str(out_path),
            )
            print(f"    Comparison: {out_path}")
        else:
            print("    No strategies with sufficient data for comparison.")
    except Exception as e:
        print(f"    Error generating comparison: {e}")

    # Save raw results CSV
    import csv
    results_path = OUTPUT_DIR / "VUKG.L_backtest_results.csv"
    with open(results_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
    print(f"    Results CSV: {results_path}")

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)

    return all_results


if __name__ == "__main__":
    results = main()


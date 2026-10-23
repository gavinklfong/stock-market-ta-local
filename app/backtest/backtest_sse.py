"""
SSE.L (SSE plc) Backtest - Multi-strategy evaluation with vectorbt.

SSE.L is a UK Utilities stock (+66.7% over 5Y, -27.3% max DD).
More stable than AZN.L but with periodic corrections requiring risk management.
Utility stocks tend to have steady uptrends with nice pullbacks.

Strategies tested on data/analysis-data/SSE.L.csv (OHLCV + all TA + P/E):

  --- Trend-Following Strategies ---
   1. GoldenCross    - EMA20>EMA50>EMA200, MA20 slope>0, SuperTrend+1, RSI>50, MACD>Signal
   2. EMAPullback    - EMA20>EMA50>EMA200, price near EMA20, RSI 40-55, SuperTrend+1
   3. SuperTrendEMA  - SuperTrend flip + EMA20>EMA50 + RSI>40 filter (reduces noise)
   4. VWAPTrend      - Close > VWAP, VWAP rising, RSI>50, ADX>20
   5. ADXMomentum    - ADX>25, +DI>-DI, RSI>50, MACD>Signal

  --- Composite / Multi-Factor Strategies ---
   6. MomentumComp   - RSI>55, MACD>Signal, ROC20>0, W%R>-50, CMF>0, EMA20>EMA50
   7. HighProbMulti  - Full checklist: EMA, RSI, MACD, CMF, OFI, BOS, HMM
   8. Score3+        - Signal scoring >= 3
   9. Score4+        - Signal scoring >= 4
  10. HMMBull        - HMM regime 0 dominant + RSI>50 + MACD>Signal

  --- Hybrid Trend + Momentum (Entry Filters) ---
  11. Hybrid_Strong  - MA200 up + Price>MA200 + MomentumComposite
  12. Hybrid_HMM     - HMM regime 0 dominant + MA200 up + MomentumComposite
  13. Hybrid_Volume  - MomentumComposite + Volume percentile > 50

  --- Pullback-to-Strength ---
  14. Pullback20     - Wait for pullback (Close<EMA20, RSI 40-50) then enter
                      when price reclaims EMA20 with momentum confirmation
  15. Pullback50     - Wait for pullback to EMA50, enter on bounce + momentum

  --- Buy & Hold Baselines ---
  16. BuyAndHold_5Y  - Simple buy and hold (5-year focus)
  17. BuyAndHold_All - Simple buy and hold (all data)

5-year focus period (2021-2026) per user request.
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
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "analysis-data" / "SSE.L.csv"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "backtest-reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TICKER_DIR = OUTPUT_DIR / "SSE.L"
TICKER_DIR.mkdir(parents=True, exist_ok=True)
INITIAL_CAPITAL = 100000
SLIPPAGE = 0.001  # 0.1% slippage per trade

# 5-year focus period
START_DATE = pd.Timestamp("2021-01-01")


# =============================================================================
# Data Loading
# =============================================================================

def load_data():
    """Load SSE.L analysis data with all TA indicators."""
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


def signal_market_struct(df):
    """Market Structure: HH+HL+BOS+Trend=1, exit on LH or LL."""
    entry = (
        (df["ta_hh"].fillna(0).astype(int) == 1)
        & (df["ta_hl"].fillna(0).astype(int) == 1)
        & (df["ta_bos"].fillna(0).astype(int) == 1)
        & (df["ta_trend"].fillna(0).astype(int) == 1)
    )
    exit_ = (
        (df["ta_lh"].fillna(0).astype(int) == 1)
        | (df["ta_ll"].fillna(0).astype(int) == 1)
    )
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
        & (df["ta_ema50"] > df["ta_ema200"])
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
        & (df["ta_cmf"] > 0)
        & (df["ta_ofi"] > 0.2)
        & (df["ta_bos"].fillna(0).astype(int) == 1)
    )
    exit_ = (
        (df["ta_supertrend_direction"] == -1)
        | (df["ta_rsi14"] < 50)
        | (df["Close"] < df["ta_ema50"])
    )
    return entry.astype(int), exit_.astype(int) * -1


def signal_score_entry(df, min_score=3):
    """Signal Score: 0-5 score based on confluence. >= min_score triggers entry."""
    score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int)
        + (df["ta_rsi14"] > 50).astype(int)
        + (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int)
        + (df["ta_cmf"] > 0).astype(int)
        + (df["ta_ofi"] > 0).astype(int)
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


# Hybrid Trend + Momentum (from AZN v2)

def signal_hybrid_strong(df):
    """Hybrid Strong: MA200 up + Price>MA200 + MomentumComposite entry."""
    momentum = signal_momentum_composite(df)
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


# Pullback-to-Strength (from AZN v2)

def signal_pullback_to_ema20(df):
    """Pullback-to-Strength: Buy pullbacks to EMA20 in uptrend.
    Phase 1: Pullback zone - Close<EMA20, RSI 40-50, MA200 up
    Phase 2: Recovery - Close reclaims EMA20, MACD>Signal, RSI>50"""
    in_pullback = (
        (df["Close"] < df["ta_ema20"])
        & (df["ta_rsi14"] >= 40)
        & (df["ta_rsi14"] <= 50)
        & (df["Close"] > df["ta_ema200"])
        & (df["ma200_slope_20d"] > 0)
    )
    recovery = (
        (df["Close"] > df["ta_ema20"])
        & (df["ta_macd_line"] > df["ta_macd_signal"])
        & (df["ta_rsi14"] > 50)
        & (df["ta_roc20"] > 0)
    )
    entries = recovery & in_pullback.shift(1)
    exit_ = (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 70)
    return entries.astype(int), exit_.astype(int) * -1


def signal_pullback_to_ema50(df):
    """Pullback-to-EMA50: Buy dips to EMA50 in strong uptrend."""
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


def signal_rsi_pullback(df):
    """Buy RSI dips (35-45) in uptrend, exit RSI>65."""
    uptrend = (df["Close"] > df["ta_ema200"]) & (df["ma200_slope_20d"] > 0)
    dip = (df["ta_rsi14"] >= 35) & (df["ta_rsi14"] <= 45)
    bounce = (df["ta_rsi14"] > 45) & (df["ta_rsi14"] <= 55) & (df["ta_macd_line"] > df["ta_macd_signal"])
    entries = bounce & uptrend & dip.shift(1)
    exits = df["ta_rsi14"] > 65
    return entries.astype(int), exits.astype(int) * -1


def signal_rsi_deep_pullback(df):
    """Buy deeper RSI dips (25-40) in uptrend, exit RSI>60."""
    uptrend = (df["Close"] > df["ta_ema200"]) & (df["ma200_slope_20d"] > 0)
    deep_dip = (df["ta_rsi14"] >= 25) & (df["ta_rsi14"] <= 40)
    bounce = (df["ta_rsi14"] > 40) & (df["ta_rsi14"] <= 50) & (df["ta_roc20"] > 0)
    entries = bounce & uptrend & deep_dip.shift(1)
    exits = df["ta_rsi14"] > 60
    return entries.astype(int), exits.astype(int) * -1


def signal_buy_and_hold(df):
    """Buy and hold signal (always in market after day 0)."""
    entries = pd.Series(1, index=df.index)
    entries.iloc[0] = 1
    exits = pd.Series(0, index=df.index)
    return entries.astype(int), exits.astype(int)


# =============================================================================
# Exit Signal Functions (Enhanced)
# =============================================================================

def signal_atr_trail(df, atr_mult=2.0):
    """ATR trailing stop exit."""
    atr = df["ta_atr14"]
    trail = df["Close"] - atr * atr_mult
    in_pos = pd.Series(False, index=df.index)
    trail_price = pd.Series(np.nan, index=df.index)
    exits = pd.Series(0, index=df.index)

    for i in range(len(df)):
        if in_pos.iloc[i]:
            trail_price.iloc[i] = max(trail_price.iloc[i - 1], trail.iloc[i])
            if df["Close"].iloc[i] <= trail_price.iloc[i]:
                exits.iloc[i] = -1
        else:
            trail_price.iloc[i] = np.nan

    return exits.astype(int)


def signal_rsi_overbought(df, threshold=75):
    """Exit when RSI crosses above overbought threshold."""
    return ((df["ta_rsi14"] > threshold) & (df["ta_rsi14"].shift(1) <= threshold)).astype(int) * -1


def signal_supertrend_flip(df):
    """Exit when SuperTrend flips down."""
    return (df["ta_supertrend_direction"] == -1).astype(int) * -1


def signal_ema_cross_exit(df):
    """Exit when EMA20 crosses below EMA50."""
    return ((df["ta_ema20"] < df["ta_ema50"]) & (df["ta_ema20"].shift(1) >= df["ta_ema50"].shift(1))).astype(int) * -1


def signal_combo_exit(df):
    """Combined exit: any of ATR trail + RSI overbought + SuperTrend flip + EMA cross."""
    atr_exit = signal_atr_trail(df, atr_mult=1.5)
    rsi_exit = signal_rsi_overbought(df, threshold=70)
    st_exit = signal_supertrend_flip(df)
    ema_exit = signal_ema_cross_exit(df)

    exit_signal = pd.Series(0, index=df.index)
    exit_signal = exit_signal.combine_max(atr_exit, lambda a, b: a if a != 0 else b)
    exit_signal = exit_signal.combine_max(rsi_exit, lambda a, b: a if a != 0 else b)
    exit_signal = exit_signal.combine_max(st_exit, lambda a, b: a if a != 0 else b)
    exit_signal = exit_signal.combine_max(ema_exit, lambda a, b: a if a != 0 else b)
    return exit_signal.astype(int)


# =============================================================================
# Backtest Engine
# =============================================================================

def run_backtest(df, entries, exits, strategy_name, initial_capital=INITIAL_CAPITAL):
    """Run a single backtest using vectorbt."""
    try:
        # Ensure no NaN in signals
        entries = entries.fillna(0).astype(int)
        exits_raw = exits.fillna(0).astype(int)

        # Create portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=df["Close"],
            entries=entries,
            exits=exits_raw,
            init_cash=initial_capital,
            slippage=SLIPPAGE,
            fees=0.001,  # 0.1% commission
            freq="1D",
        )

        # Extract metrics
        stats = portfolio.total_return()
        sharpe = portfolio.sharpe_ratio()
        max_dd = portfolio.max_drawdown()
        trades = portfolio.trades
        total_trades = trades.count()
        win_rate = trades.win_rate()
        profit_factor = trades.profit_factor()

        # Calculate 5-year metrics if data spans beyond
        df_5y = df[df.index >= START_DATE]
        if len(df_5y) > 1 and df.index[-1] > START_DATE:
            # Re-run on 5-year subset for comparison
            port_5y = vbt.Portfolio.from_signals(
                close=df_5y["Close"],
                entries=entries[entries.index >= START_DATE],
                exits=exits_raw[exits_raw.index >= START_DATE],
                init_cash=initial_capital,
                slippage=SLIPPAGE,
                fees=0.001,
                freq="1D",
            )
            return_5y = port_5y.total_return()
            sharpe_5y = port_5y.sharpe_ratio()
            dd_5y = port_5y.max_drawdown()
            trades_5y = port_5y.trades.count()
            wr_5y = port_5y.trades.win_rate()
        else:
            return_5y = stats
            sharpe_5y = sharpe
            dd_5y = max_dd
            trades_5y = total_trades
            wr_5y = win_rate

        result = {
            "Strategy": strategy_name,
            "Total_Return_%": stats * 100,
            "Sharpe_Ratio": sharpe,
            "Max_DD_%": max_dd * 100,
            "Total_Trades": total_trades,
            "Win_Rate_%": win_rate * 100,
            "Profit_Factor": profit_factor,
            "Return_5Y_%": return_5y * 100,
            "Sharpe_5Y": sharpe_5y,
            "Max_DD_5Y_%": dd_5y * 100,
            "Trades_5Y": trades_5y,
            "Win_Rate_5Y_%": wr_5y * 100,
        }
        return result

    except Exception as e:
        print(f"  ERROR in {strategy_name}: {e}")
        return {
            "Strategy": strategy_name,
            "Total_Return_%": np.nan,
            "Sharpe_Ratio": np.nan,
            "Max_DD_%": np.nan,
            "Total_Trades": 0,
            "Win_Rate_%": np.nan,
            "Profit_Factor": np.nan,
            "Return_5Y_%": np.nan,
            "Sharpe_5Y": np.nan,
            "Max_DD_5Y_%": np.nan,
            "Trades_5Y": 0,
            "Win_Rate_5Y_%": np.nan,
        }


# =============================================================================
# Strategy Groups
# =============================================================================

def run_single_strategy(df, signal_fn, strategy_name):
    """Run a single strategy and return results dict."""
    entries, exits = signal_fn(df)
    return run_backtest(df, entries, exits, strategy_name)


def run_strategy_group(df, group_name, signal_fns):
    """Run a group of strategies and return results list."""
    print(f"\n{'='*60}")
    print(f"Running: {group_name}")
    print(f"{'='*60}")

    results = []
    for name, fn in signal_fns.items():
        print(f"  Running {name}...", end=" ")
        result = run_single_strategy(df, fn, name)
        results.append(result)
        ret = result.get("Total_Return_%", 0)
        if pd.notna(ret):
            print(f"{ret:+.1f}% return, {result.get('Max_DD_%', 0):+.1f}% DD")
        else:
            print("N/A")

    return results


# =============================================================================
# Report Generation
# =============================================================================

def generate_reports(results, df_5y):
    """Generate comparison table and tearsheet for best strategies."""
    if not results:
        print("No results to report.")
        return

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Sort by 5-year return
    results_df = results_df.sort_values("Return_5Y_%", ascending=False)

    # Save summary CSV
    summary_path = TICKER_DIR / "backtest_summary.csv"
    results_df.to_csv(summary_path, index=False)
    print(f"\nSummary saved to: {summary_path}")

    # Print table
    print(f"\n{'='*80}")
    print("SSE.L BACKTEST RESULTS (sorted by 5Y return)")
    print(f"{'='*80}")
    print(f"{'Strategy':<25} {'5Y Return':>10} {'5Y DD':>10} {'5Y Sharpe':>11} {'5Y Trades':>11} {'5Y Win%':>10}")
    print("-" * 80)
    for _, row in results_df.iterrows():
        print(
            f"{row['Strategy']:<25} "
            f"{row['Return_5Y_%']:>+9.1f}% "
            f"{row['Max_DD_5Y_%']:>+9.1f}% "
            f"{row['Sharpe_5Y']:>+10.2f} "
            f"{int(row['Trades_5Y']):>10} "
            f"{row['Win_Rate_5Y_%']:>+9.1f}%"
        )

    # Find best strategy (by return, filter out NaN)
    valid = results_df.dropna(subset=["Return_5Y_%"])
    if len(valid) == 0:
        print("\nNo valid results to generate tearsheet.")
        return

    best = valid.iloc[0]
    best_name = best["Strategy"]
    print(f"\n>>> Best strategy: {best_name} (5Y Return: {best['Return_5Y_%']:.1f}%)")

    # Generate tearsheet for top 3 strategies
    for i in range(min(3, len(valid))):
        strat = valid.iloc[i]
        strat_name = strat["Strategy"]

        # Re-run to get portfolio object for tearsheet
        print(f"\n  Generating tearsheet for: {strat_name}")

        # Find the matching signal function
        signal_fn = None
        for fn_name, fn in [
            ("GoldenCross", signal_goldencross),
            ("EMAPullback", signal_emapullback),
            ("SuperTrendEMA", signal_supertrend_ema),
            ("VWAPTrend", signal_vwap_trend),
            ("ADXMomentum", signal_adx_momentum),
            ("MomentumComp", signal_momentum_composite),
            ("HighProbMulti", signal_high_prob_multi),
            ("HMMBull", signal_hmm_bull),
            ("Hybrid_Strong", signal_hybrid_strong),
            ("Hybrid_HMM", signal_hybrid_hmm),
            ("Hybrid_Volume", signal_hybrid_volume),
            ("Pullback20", signal_pullback_to_ema20),
            ("Pullback50", signal_pullback_to_ema50),
            ("RSI_Pullback", signal_rsi_pullback),
            ("RSI_DeepPullback", signal_rsi_deep_pullback),
            ("BuyAndHold", signal_buy_and_hold),
        ]:
            if strat_name == fn_name:
                signal_fn = fn
                break

        if signal_fn is None:
            # Try Score strategies
            if "Score3" in strat_name:
                signal_fn = lambda df: signal_score_entry(df, min_score=3)
            elif "Score4" in strat_name:
                signal_fn = lambda df: signal_score_entry(df, min_score=4)
            elif "Adaptive" in strat_name:
                signal_fn = signal_score_adaptive
            else:
                print(f"    Skipping tearsheet for unknown strategy: {strat_name}")
                continue

        entries, exits = signal_fn(df_5y)
        portfolio = vbt.Portfolio.from_signals(
            close=df_5y["Close"],
            entries=entries,
            exits=exits.fillna(0).astype(int),
            init_cash=INITIAL_CAPITAL,
            slippage=SLIPPAGE,
            fees=0.001,
            freq="1D",
        )

        # Generate tearsheet
        report_path = TICKER_DIR / f"{strat_name.replace('+', '').replace(' ', '_')}_tearsheet.html"
        try:
            # Get returns as Series
            returns = portfolio.returns()
            qs.reports.html(
                returns,
                benchmark=None,
                title=f"SSE.L - {strat_name}",
                output=str(report_path),
                download_filename=str(report_path),
            )
            print(f"    Tearsheet saved: {report_path}")
        except Exception as e:
            print(f"    Error generating tearsheet: {e}")

        # Also save equity curve as CSV
        equity_path = TICKER_DIR / f"{strat_name.replace('+', '').replace(' ', '_')}_equity.csv"
        portfolio.cumulative_returns().to_csv(equity_path)
        print(f"    Equity curve saved: {equity_path}")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all SSE.L backtests."""
    print("=" * 60)
    print("SSE.L (SSE plc) Multi-Strategy Backtest")
    print("=" * 60)

    # Load data
    df, df_5y = load_data()

    # Define strategy groups
    trend_strategies = {
        "GoldenCross": signal_goldencross,
        "EMAPullback": signal_emapullback,
        "SuperTrendEMA": signal_supertrend_ema,
        "VWAPTrend": signal_vwap_trend,
        "ADXMomentum": signal_adx_momentum,
    }

    composite_strategies = {
        "MomentumComp": signal_momentum_composite,
        "HighProbMulti": signal_high_prob_multi,
        "Score3+": lambda df: signal_score_entry(df, min_score=3),
        "Score4+": lambda df: signal_score_entry(df, min_score=4),
        "HMMBull": signal_hmm_bull,
    }

    hybrid_strategies = {
        "Hybrid_Strong": signal_hybrid_strong,
        "Hybrid_HMM": signal_hybrid_hmm,
        "Hybrid_Volume": signal_hybrid_volume,
    }

    pullback_strategies = {
        "Pullback20": signal_pullback_to_ema20,
        "Pullback50": signal_pullback_to_ema50,
        "RSI_Pullback": signal_rsi_pullback,
        "RSI_DeepPullback": signal_rsi_deep_pullback,
    }

    baseline_strategies = {
        "BuyAndHold": signal_buy_and_hold,
    }

    # Run all strategy groups
    all_results = []

    all_results.extend(run_strategy_group(df_5y, "Trend-Following Strategies", trend_strategies))
    all_results.extend(run_strategy_group(df_5y, "Composite Strategies", composite_strategies))
    all_results.extend(run_strategy_group(df_5y, "Hybrid Strategies", hybrid_strategies))
    all_results.extend(run_strategy_group(df_5y, "Pullback Strategies", pullback_strategies))
    all_results.extend(run_strategy_group(df_5y, "Baselines", baseline_strategies))

    # Generate reports
    generate_reports(all_results, df_5y)

    print("\n" + "=" * 60)
    print("Backtest complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

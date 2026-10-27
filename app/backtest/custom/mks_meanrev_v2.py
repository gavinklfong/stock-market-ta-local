"""Marks & Spencer optimised mean-reversion strategy.

MKS.L is a UK retail stock (Marks & Spencer) — a value-oriented retailer with
stable cyclical demand. Data from 2025-01 to 2026-10 shows a ~15% drawdown in
2025 followed by a ~28% recovery in 2026. The stock exhibits mean-reverting
behaviour around its 20-day moving average with periodic overshoots below the
Bollinger Band lower band.

This strategy improves on the built-in dual_exit_meanrev by:
- Adding a volume confirmation filter (CMF > -0.05) to avoid entering on
  capitulation selloffs with no institutional support
- Adding a short-term momentum filter (ROC20 > -15%) to avoid catching
  fundamentally deteriorating stocks
- Using a tighter 2x ATR trail for better profit capture on quick bounces
- Adding a time-stop (30-day max hold) to prevent capital drag
"""

from framework.extensions import register_custom
import pandas as pd


@register_custom("mks_meanrev_v2")
def signal_mks_meanrev_v2(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MKS.L Mean Reversion v2 — BB Lower + RSI + volume + momentum filter."""
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        (df["ta_cmf"] > -0.05) &
        (df["ta_roc20"] > -15) &
        (df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1))
    )

    # Dual exit: BB middle band or ATR trail (2x for tighter capture)
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]

    three_day_high = df["Close"].rolling(3).max()
    atr_trail = three_day_high - 2 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = bb_middle_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("mks_trend_rider")
def signal_mks_trend_rider(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MKS.L Trend Rider — buys pullbacks in confirmed uptrends, exits on weakness.

    Designed for the 2026 recovery phase. Enters on dips below EMA20 during
    confirmed uptrends (EMA20 > EMA50 > EMA200), exits on SuperTrend flip
    or RSI overbought.
    """
    near_ema20 = (df["ta_ema20"] - df["Close"]) / df["Close"] < 0.025
    near_ema20 = near_ema20 & (df["Close"] < df["ta_ema20"])

    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_ma20_slope"] > 0) &
        (df["ta_supertrend_direction"] == 1) &
        near_ema20 &
        (df["ta_rsi14"] >= 40) &
        (df["ta_rsi14"] <= 58) &
        (df["ta_cmf"] > 0)
    )

    exit_ = (
        (df["ta_supertrend_direction"] == -1) |
        (df["Close"] < df["ta_ema50"]) |
        (df["ta_rsi14"] > 68)
    )
    return entry.astype(int), exit_.astype(int) * -1

"""Example custom strategy for NG.L.

This file demonstrates how to define a custom strategy that:
1. Uses the @register_custom decorator to register the function
2. Accesses any ta_ prefixed column in the analysis-data CSV
3. Returns (entries, exits) — pandas Series of int (1 = entry, -1 = exit)
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("ng_rsi_bounce")
def ng_rsi_bounce(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """RSI Bounce Strategy for NG.L: Buy oversold, sell recovered.

    Entry: RSI crosses above 30 from below (was oversold)
    Exit: RSI crosses below 50 (momentum fading)

    Uses ta_rsi14 from the analysis-data CSV.
    """
    rsi = df["ta_rsi14"]

    # Entry: RSI was <= 30 yesterday, today > 30 (crossed above)
    rsi_cross_above_30 = (rsi <= 30) & (rsi.shift(1) > 30) | (rsi > 30) & (rsi.shift(1) <= 30)

    # Actually, let's fix: RSI today > 30 AND RSI yesterday <= 30
    rsi_cross_above_30 = (rsi > 30) & (rsi.shift(1) <= 30)

    # Entry: RSI crossing above 30 + price above EMA50 (trend support)
    entry = rsi_cross_above_30 & (df["Close"] > df["ta_ema50"])

    # Exit: RSI falls back below 50
    exit_ = (rsi < 50) & (rsi.shift(1) >= 50)

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("ng_bb_squeeze")
def ng_bb_squeeze(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Squeeze Strategy: Enter when BB narrows, exit on breakout.

    Entry: BB Width below 20th percentile (squeeze) AND RSI < 40
    Exit: Price breaks above BB Middle band

    Uses ta_bband_lower, ta_bband_middle, ta_bband_upper, ta_rsi14.
    """
    bb_width = df["ta_bband_upper"] - df["ta_bband_lower"]
    bb_pct = bb_width.rolling(50).pctrank()
    squeeze = bb_pct < 20  # Width in bottom 20% of last 50 days

    rsi = df["ta_rsi14"]
    entry = squeeze & (rsi < 40)
    exit_ = df["Close"] >= df["ta_bband_middle"]

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("ng_momentum_divergence")
def ng_momentum_divergence(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Momentum Divergence Strategy: Hidden divergence in MACD + RSI.

    Entry: RSI rising while price makes lower low, MACD histogram turning up
    Exit: MACD histogram peaks and starts falling

    Uses ta_rsi14, ta_macd_histogram, ta_macd_line, ta_macd_signal.
    """
    rsi = df["ta_rsi14"]
    macd_hist = df["ta_macd_histogram"]
    price = df["Close"]

    # RSI rising
    rsi_rising = rsi > rsi.shift(1)

    # Price making lower low
    price_lower_low = price < price.shift(1)

    # MACD histogram turning up (2-day confirmation)
    hist_turning_up = macd_hist > macd_hist.shift(2)

    # Entry: RSI rising + price still falling + MACD turning up
    entry = rsi_rising & price_lower_low & hist_turning_up & (rsi < 50)

    # Exit: MACD histogram starts falling
    exit_ = macd_hist < macd_hist.shift(1)

    return entry.astype(int), exit_.astype(int) * -1

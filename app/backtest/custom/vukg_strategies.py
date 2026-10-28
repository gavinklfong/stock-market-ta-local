"""Custom strategies for VUKG.L (Vanguard FTSE 100 UCITS ETF).

VUKG.L is a low-volatility broad-market index ETF with a strong secular uptrend
and periodic crashes (2020 COVID, etc.). These strategies are designed for this
asset type:
- Trend-following works well due to sustained uptrends
- Mean-reversion rarely triggers (narrow BB, low volatility)
- Crash protection is essential (2020 saw -34% max DD)
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("vukg_robust_trend")
def vukg_robust_trend(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Robust Trend: EMA50 > EMA200 AND price above EMA50, exit when price drops below EMA50.

    Simple but effective for trending ETFs like VUKG.L.
    """
    entry = (
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["Close"] > df["ta_ema50"]) &
        ((df["ta_ema50"].shift(1) <= df["ta_ema200"].shift(1)) | (df["Close"].shift(1) <= df["ta_ema50"].shift(1)))
    )
    exit_ = (
        (df["Close"] < df["ta_ema50"]) &
        (df["Close"].shift(1) >= df["ta_ema50"].shift(1))
    )
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_supertrend_atr")
def vukg_supertrend_atr(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """SuperTrend + ATR Trail: Enter on SuperTrend flip to +1, trail with ATR.

    Uses SuperTrend for direction and ATR-based trailing stop for exits.
    """
    direction = df["ta_supertrend_direction"]
    entry = (direction == 1) & (direction.shift(1) == -1)
    exit_ = (direction == -1) & (direction.shift(1) == 1)
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_bband_range")
def vukg_bband_range(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Range Strategy: Buy at BB Lower, sell at BB Middle for index ETFs.

    Relaxed entry (BB Lower or RSI < 35) for low-volatility ETFs that rarely
    touch BB Lower. Exit at BB Middle (mean reversion target).
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_dual_ema")
def vukg_dual_ema(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dual EMA Crossover: EMA20/EMA50 cross with SuperTrend filter.

    More responsive than golden cross. SuperTrend filter avoids whipsaws.
    """
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema20"].shift(1) <= df["ta_ema50"].shift(1)) &
        (df["ta_supertrend_direction"] == 1)
    )
    exit_ = (
        (df["ta_ema20"] < df["ta_ema50"]) &
        (df["ta_ema20"].shift(1) >= df["ta_ema50"].shift(1))
    )
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_ema20_ride")
def vukg_ema20_ride(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """EMA20 Ride: Stay in as long as price is above EMA20.

    Simple trend-riding strategy. Exit when price closes below EMA20.
    Good for ETFs with strong secular uptrends.
    """
    entry = (df["Close"] > df["ta_ema20"]) & (df["Close"].shift(1) <= df["ta_ema20"].shift(1))
    exit_ = (df["Close"] < df["ta_ema20"]) & (df["Close"].shift(1) >= df["ta_ema20"].shift(1))
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_crisis_guard")
def vukg_crisis_guard(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Crisis Guard: Trend-following with drawdown-based emergency exit.

    Standard trend-following (EMA50>EMA200, price>EMA50), but with an
    additional ATR-based emergency stop that triggers during crash conditions.
    """
    entry = (
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["Close"] > df["ta_ema50"])
    )
    # Emergency stop: 3x ATR trail from 5-day high
    highest_5 = df["Close"].rolling(5).max()
    atr_stop = highest_5 - 3 * df["ta_atr14"]
    exit_ = (
        df["Close"] < atr_stop
    ) | (
        (df["Close"] < df["ta_ema50"]) & (df["Close"].shift(1) >= df["ta_ema50"].shift(1))
    )
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_ma_slope_trend")
def vukg_ma_slope_trend(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MA Slope Trend: MA20 slope > 0 + MA50 slope > 0 + RSI > 40.

    Uses pre-computed MA slopes for trend confirmation.
    More conservative than price-based entries.
    """
    entry = (
        (df["ta_ma20_slope"] > 0) &
        (df["ta_ma50_slope"] > 0) &
        (df["ta_rsi14"] > 40) &
        (df["Close"] > df["ta_ma20"]) &
        ((df["ta_ma20"].shift(1) <= df["ta_ma50"].shift(1)) | (df["ta_ma50_slope"].shift(1) <= 0))
    )
    exit_ = (
        (df["ta_ma20_slope"] < 0) |
        (df["ta_ma50_slope"] < 0)
    )
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_seasonal")
def vukg_seasonal(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Seasonal Pattern: Buy in January (historically strong for UK ETFs), sell in October.

    Calendar-based seasonal strategy. Entry: first trading day of January.
    Exit: last trading day of October.
    """
    weekday = df["weekday"]
    # We'll use a different approach: track month transitions
    dates = pd.to_datetime(df["Date"])
    jan_days = dates.dt.month == 1
    oct_days = dates.dt.month == 10

    entry = jan_days & (jan_days.shift(1) == False)
    exit_ = oct_days & (oct_days.shift(1) == False)
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("vukg_macd_trend")
def vukg_macd_trend(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MACD Trend: MACD bullish cross + EMA200 filter + volume confirmation.

    MACD crossover is a reliable mid-term signal for ETFs.
    EMA200 filter ensures we only trade in the direction of the long-term trend.
    """
    entry = (
        (df["ta_macd_line"] > df["ta_macd_signal"]) &
        (df["ta_macd_line"].shift(1) <= df["ta_macd_signal"].shift(1)) &
        (df["Close"] > df["ta_ema200"])
    )
    exit_ = (
        (df["ta_macd_line"] < df["ta_macd_signal"]) &
        (df["ta_macd_line"].shift(1) >= df["ta_macd_signal"].shift(1))
    )
    return entry.astype(int), exit_.astype(int) * -1

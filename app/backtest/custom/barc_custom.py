"""Custom strategies optimized for BARC.L (Barclays).

BARC.L characteristics (5-year analysis):
- Cyclical banking stock: +104% total return, 53% bullish trend days
- More mean-reverting than STAN.L: RSI 30-70 range 88% of time
- Higher volatility: 40.49% max drawdown, ATR mean 7.11p
- ADX mean 24.0, 40.2% strong trend days (vs STAN.L's 43.6%)
- Volume surges (1.5× avg): 13.3% of days (vs ~0% for STAN.L)
- RSI<30 signals: 2.7% of time (rare oversold opportunities)
- OBV increasing 52.5% (barely above 50%, weak trend confirmation)

Strategies designed:
1. barc_meanrev_range — Range-bound mean reversion (primary approach)
2. barc_trend_pullback — Trend-following with tighter entries
3. barc_vol_breakout — Volume-surge breakout (exploiting frequent surges)
4. barc_adaptive_score — Adaptive scoring tuned for BARC.L's 53% trend ratio
5. barc_ema_bounce — EMA bounce strategy for range-bound markets
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("barc_meanrev_range")
def barc_meanrev_range(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BARC Mean Reversion Range: Core strategy for BARC.L's range-bound nature.

    BARC.L spends 88% of time in RSI 30-70 range — classic mean-reverting behavior.
    This strategy buys at the lower band and sells at the middle/upper band.

    Entry (all must hold):
    - Close <= BB Lower (statistically cheap)
    - RSI < 35 (oversold but not extreme)
    - Williams %R < -80 (confirming oversold)
    - CMF > -0.05 (no strong selling pressure)

    Exit:
    - Close >= BB Middle (standard target)
    - RSI > 55 (momentum recovered)

    This exploits BARC.L's tendency to revert to the mean rather than trend.
    With 5.9% of days at BB Lower, there are plenty of entries.

    Uses: ta_bband_lower, ta_bband_middle, ta_rsi14, ta_williams_r, ta_cmf
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_williams_r"] < -80) &
        (df["ta_cmf"] > -0.05)
    )

    exit_ = (
        df["Close"] >= df["ta_bband_middle"]
    ) | (df["ta_rsi14"] > 55)

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("barc_trend_pullback")
def barc_trend_pullback(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BARC Trend Pullback: Trend-following with pullback entry.

    BARC.L has only 53% bullish trend days — trend-following must be selective.
    This strategy enters on pullbacks within confirmed uptrend, improving
    risk/reward vs chasing breakouts.

    Entry (all must hold):
    - EMA20 > EMA50 > EMA200 (confirmed uptrend)
    - SuperTrend +1 (trend support)
    - Price within 3% of EMA20 (pullback zone)
    - RSI 40-55 (pullback range, not oversold)
    - MACD > Signal (momentum still positive)

    Exit:
    - Close < EMA50 (trend broken)
    - RSI > 65 (overbought in range-bound market)

    Uses: ta_ema20, ta_ema50, ta_ema200, ta_supertrend_direction,
          ta_rsi14, ta_macd_line, ta_macd_signal
    """
    uptrend = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_supertrend_direction"] == 1)
    )

    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03
    rsi_pullback = (df["ta_rsi14"] >= 40) & (df["ta_rsi14"] <= 55)
    mom_positive = df["ta_macd_line"] > df["ta_macd_signal"]

    entry = uptrend & near_ema20 & rsi_pullback & mom_positive

    exit_ = (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 65)

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("barc_vol_breakout")
def barc_vol_breakout(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BARC Vol Breakout: Volume-surge breakout strategy.

    BARC.L generates 13.3% of days with volume > 1.5× average — much higher
    than STAN.L (~0%). This exploits institutional flow moves.

    Entry (all must hold):
    - Close > 20-day high (Donchian breakout)
    - Volume > 1.5× 20-day average (institutional flow)
    - EMA20 > EMA50 (trend alignment)
    - ROC20 > 0 (positive momentum)

    Exit:
    - Close < 10-day low (breakout failed)
    - Volume drops below average (flow fading)

    Uses: ta_ema20, ta_ema50, Volume, High, Low
    """
    trend_ok = (df["ta_ema20"] > df["ta_ema50"])
    breakout = df["Close"] > df["High"].rolling(20).max()
    vol_surge = df["Volume"] > df["Volume"].rolling(20).mean() * 1.5
    mom_positive = df["ta_roc20"] > 0

    entry = trend_ok & breakout & vol_surge & mom_positive

    donchian_lower = df["Low"].rolling(10).min()
    vol_avg = df["Volume"].rolling(20).mean()
    exit_ = df["Close"] < donchian_lower

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("barc_adaptive_score")
def barc_adaptive_score(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BARC Adaptive Score: Scoring system tuned for 53% trend ratio.

    BARC.L is neither strongly trending nor purely range-bound.
    This adaptive score weights mean-reversion signals more than STAN's config.

    Score breakdown (100 pts):
    - Trend: 25 (EMA alignment + SuperTrend)
    - Momentum: 25 (RSI, MACD, ROC)
    - Mean-reversion: 30 (BB position, RSI extremes)
    - Volume: 20 (CMF, volume trend)

    Entry: Score >= 65 (lower threshold for BARC.L's mixed signals)
    Exit: Score < 45

    Uses: ta_ema20, ta_ema50, ta_ema200, ta_supertrend_direction,
          ta_rsi14, ta_macd_line, ta_macd_signal, ta_roc20, ta_cmf,
          ta_bband_lower, ta_bband_upper, ta_bband_middle
    """
    # Trend score (25 pts)
    trend_score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int) * 10 +
        (df["ta_ema50"] > df["ta_ema200"]).astype(int) * 10 +
        (df["ta_supertrend_direction"] == 1).astype(int) * 5
    )

    # Momentum score (25 pts)
    mom_score = (
        (df["ta_rsi14"] > 50).astype(int) * 8 +
        (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int) * 10 +
        (df["ta_roc20"] > 0).astype(int) * 7
    )

    # Mean-reversion score (30 pts)
    bb_middle = df["ta_bband_middle"]
    bb_width = df["ta_bband_upper"] - df["ta_bband_lower"]
    bb_position = (df["Close"] - df["ta_bband_lower"]) / bb_width
    meanrev_score = (
        (bb_position < 0.2).astype(int) * 15 +  # Near lower band
        (df["ta_rsi14"] < 40).astype(int) * 10 +  # Oversold
        (df["ta_rsi14"] > 60).astype(int) * 5 +   # Slightly overbought (exit)
        (df["ta_williams_r"] < -70).astype(int) * 5  # Oversold confirm
    )

    # Volume score (20 pts)
    vol_score = (
        (df["ta_cmf"] > 0).astype(int) * 10 +
        (df["Volume"] > df["Volume"].rolling(20).mean()).astype(int) * 10
    )

    total_score = trend_score + mom_score + meanrev_score + vol_score

    # Entry: high score (strong signals in either direction)
    # We interpret high score as "good entry" regardless of direction
    entry = total_score >= 65

    # Exit: low score (weak signals)
    exit_ = total_score < 45

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("barc_ema_bounce")
def barc_ema_bounce(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BARC EMA Bounce: Buy bounces off EMA50 in range-bound market.

    BARC.L frequently bounces off key EMAs due to its mean-reverting nature.
    EMA50 acts as dynamic support in sideways markets.

    Entry (all must hold):
    - Price pulls back to within 2% of EMA50
    - RSI 30-45 (pullback zone, not distressed)
    - CMF > 0 (no net selling pressure)
    - Volume below average (selling exhaustion)
    - SuperTrend neutral or +1 (not strongly bearish)

    Exit:
    - Price reaches EMA20 (15% profit target for range)
    - Price breaks below EMA200 (trend break)
    - RSI > 60 (reached mean-reversion target)

    Uses: ta_ema20, ta_ema50, ta_ema200, ta_rsi14, ta_cmf, Volume, ta_supertrend_direction
    """
    near_ema50 = (df["Close"] - df["ta_ema50"]).abs() / df["Close"] < 0.02
    rsi_bounce = (df["ta_rsi14"] >= 30) & (df["ta_rsi14"] <= 45)
    no_selling = df["ta_cmf"] > 0
    vol_exhaustion = df["Volume"] < df["Volume"].rolling(20).mean()
    not_bearish = df["ta_supertrend_direction"] != -1

    entry = near_ema50 & rsi_bounce & no_selling & vol_exhaustion & not_bearish

    # Exit: take profit at EMA20 or mean-reversion target
    take_profit = df["Close"] >= df["ta_ema20"]
    rsi_target = df["ta_rsi14"] > 60
    trend_break = df["Close"] < df["ta_ema200"]

    exit_ = take_profit | rsi_target | trend_break

    return entry.astype(int), exit_.astype(int) * -1

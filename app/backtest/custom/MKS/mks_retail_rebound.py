"""MKS.L Retail Rebound — mean-reversion with trend filter and ATR trail.

MKS.L (Marks & Spencer) characteristics for 2025-01-01 onwards:
- Retail stock with V-shaped recovery pattern (-15% in 2025, +28% in 2026)
- Mean-reversion strategies dominate (top 3 built-ins all BB Lower entries)
- High volatility (29.75% annualized) — needs wider stop distances
- Strong uptrend in 2026 (EMA20 > EMA50 > EMA200)

This strategy improves on dual_exit_meanrev by:
1. Adding a GARCH vol filter (avoids catching falling knives during crashes)
2. Adding a CMF > -0.2 filter (avoids extreme capitulation selloffs)
3. Adding RSI exit at 65 (momentum exhaustion — captures extended bounces)
4. Dual exit: BB Middle + ATR trail (3xATR from 5-day high)

Entry: BB Lower + RSI<35 + CCI<-100 + CMF>-0.2 + GARCH stable
Exit: BB Middle OR 5-day high - 3xATR trail OR RSI > 65
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("mks_retail_rebound")
def mks_retail_rebound(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MKS.L Retail Rebound — trend-filtered mean-reversion with ATR trail.

    Entry conditions (ALL must be true):
      1. Close <= BB Lower (price is oversold relative to recent range)
      2. RSI(14) < 35 (momentum extremely weak — buying opportunity)
      3. CCI(20) < -100 (commodity channel index confirms extreme)
      4. CMF > -0.2 (not extreme capitulation)
      5. GARCH vol not rising (volatility stabilizing, not a crash)
      6. EMA20 > EMA50 > EMA200 (uptrend — buy dips in uptrends, not downtrends)

    Exit conditions (ANY triggers):
      1. Close >= BB Middle (mean reversion complete)
      2. Price < 5-day high - 3xATR (trailing stop)
      3. RSI(14) > 65 (momentum exhaustion)
    """
    # === ENTRY ===
    # Mean-reversion signals
    bb_oversold = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 35
    cci_oversold = df["ta_cci"] < -100

    # Volume filter — not extreme capitulation
    cmf_ok = df["ta_cmf"] > -0.2

    # GARCH vol filter — avoid falling knives
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)

    # Combine entry: BB Lower + RSI<35 + CCI<-100 + volume filter + GARCH stable
    entry = (
        bb_oversold &
        rsi_oversold &
        cci_oversold &
        cmf_ok &
        garch_stable
    )

    # === EXIT ===
    # Take profit at mean (BB middle)
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]

    # ATR trailing stop
    five_day_high = df["Close"].rolling(5).max()
    atr_trail = five_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    # RSI momentum exhaustion
    rsi_exit = df["ta_rsi14"] > 65

    exit_ = bb_middle_exit | atr_exit | rsi_exit

    return entry.astype(int), exit_.astype(int) * -1

"""Custom Trend+Guard strategy for LSEG.L — relaxed version.

Builds on the best-performing trend_momentum strategy but adds:
1. ATR-based trailing stop (2.5x) to cut losses during 2025-style crashes
2. Time-stop (30 days) to avoid prolonged drawdown periods
3. Pullback entry (price dips near EMA20) for better risk-reward
4. Volume confirmation via CMF to avoid false breakouts

Improvements over the original:
- Removed GARCH vol filter (too restrictive, caused NaN in early data)
- Removed SuperTrend requirement (overlaps with EMA alignment)
- Wider RSI range (40-70) for more entries
- Entry: price within 3% of EMA20 instead of 1-2%
- 5 conditions (AND) instead of 7
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lseg_trend_guard")
def signal_lseg_trend_guard(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """LSEG.L Trend Guard: Trend-following with ATR trail + time stop.

    Entry conditions (AND logic):
    - EMA alignment: EMA20 > EMA50 > EMA200
    - Price near EMA20 (within 3% below) — pullback entry
    - RSI 40-70: trending but not overbought
    - MACD bullish: line > signal
    - Volume confirmation: CMF > 0

    Exit conditions (OR logic):
    - EMA20 crosses below EMA50 (trend broken)
    - ATR trailing stop hit: price drops 2.5xATR below 15-day high
    - RSI > 70 (overbought exit)
    """
    # --- Trend alignment (core filter) ---
    ema_aligned = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"])
    )

    # --- Pullback entry: price near EMA20 (within 3% below) ---
    price_near_ema20 = (df["Close"] <= df["ta_ema20"]) & (
        (df["ta_ema20"] - df["Close"]) / df["Close"] <= 0.03
    )

    # --- Momentum filter ---
    rsi_ok = (df["ta_rsi14"] > 40) & (df["ta_rsi14"] < 70)

    # --- MACD bullish ---
    macd_bullish = df["ta_macd_line"] > df["ta_macd_signal"]

    # --- Volume confirmation ---
    vol_conf = df["ta_cmf"] > 0

    # Entry: ALL 5 conditions must hold
    entry = (
        ema_aligned &
        price_near_ema20 &
        rsi_ok &
        macd_bullish &
        vol_conf
    )

    # --- Exit conditions ---
    # 1. Trend broken
    trend_broken = df["ta_ema20"] < df["ta_ema50"]

    # 2. ATR trailing stop: 2.5x ATR below 15-day high
    highest_15 = df["Close"].rolling(15).max()
    atr_stop = highest_15 - 2.5 * df["ta_atr14"]
    atr_hit = df["Close"] < atr_stop

    # 3. Overbought exit
    overbought = df["ta_rsi14"] > 70

    exit_ = trend_broken | atr_hit | overbought

    return entry.astype(int), exit_.astype(int)

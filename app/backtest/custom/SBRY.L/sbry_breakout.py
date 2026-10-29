"""Custom breakout strategies for Sainsbury's (SBRY.L) 2025-2026 uptrend.

Context: SBRY.L rallied +28% from Jan 2025 to Oct 2026. bb_breakout dominated
at +27.36% return, 1.77 Sharpe. Custom strategies here aim to improve on
bb_breakout by adding volume confirmation, ATR trailing exits, and multi-signal
scoring to reduce false breakouts and capture more trend continuation.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("sbry_volume_breakout")
def sbry_volume_breakout(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Volume-confirmed BB Breakout.

    Improves on bb_breakout by requiring:
    - Close > BB Upper (same as baseline)
    - ATR rising (same)
    - HV rising (same)
    - ROC20 > 0 (same)
    + CMF > 0 (money flow must be positive — real buying pressure)
    + Volume > 20-day average (volume surge on breakout)

    Exit: Close < BB Middle OR MACD bearish cross (same as baseline)
    """
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)
    vol_above_avg = df["Volume"] > df["Volume"].rolling(20).mean()
    entry = (
        (df["Close"] > df["ta_bband_upper"]) &
        atr_rising &
        hv_rising &
        (df["ta_roc20"] > 0) &
        (df["ta_cmf"] > 0) &
        vol_above_avg
    )
    exit_ = (
        (df["Close"] < df["ta_bband_middle"]) |
        (df["ta_macd_line"] < df["ta_macd_signal"])
    )
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("sbry_atr_trail_breakout")
def sbry_atr_trail_breakout(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Breakout with ATR trailing stop.

    Same entry as bb_breakout, but replaces the simple BB Middle exit with
    a dynamic ATR trailing stop. This captures more of the trend when
    the breakout continues for multiple days.

    Entry: Close > BB Upper + ATR rising + HV rising + ROC20 > 0
    Exit: Close < BB Middle (early) OR Close < Trail (high_close - 3*ATR)

    The ATR trail allows profits to run while protecting gains.
    """
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)

    entry = (
        (df["Close"] > df["ta_bband_upper"]) &
        atr_rising &
        hv_rising &
        (df["ta_roc20"] > 0)
    )

    # ATR trailing stop from 10-day high (wider window for breakout runs)
    high_close = df["Close"].rolling(10).max()
    atr_stop = high_close - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_stop

    # Original exit conditions
    bb_middle_exit = df["Close"] < df["ta_bband_middle"]
    macd_exit = df["ta_macd_line"] < df["ta_macd_signal"]

    exit_ = atr_exit | bb_middle_exit | macd_exit
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("sbry_multi_breakout")
def sbry_multi_breakout(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Multi-signal breakout scoring.

    Combines trend, momentum, volume, and structure signals into a score.
    Entry requires score >= 70 (out of 100) — a high-bar entry for breakouts.

    Scoring:
      - Trend (30): EMA20>EMA50 (10), EMA50>EMA200 (10), SuperTrend+1 (10)
      - Momentum (25): RSI>55 (8), MACD>Signal (8), ROC20>0 (5), CCI>0 (4)
      - Volume (25): CMF>0 (10), OBV rising (10), Volume>20d avg (5)
      - Structure (20): BB Upper breakout (20)

    Exit: Score drops below 50 OR Close < BB Middle OR MACD bearish cross
    """
    # Trend score (max 30)
    trend_score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int) * 10 +
        (df["ta_ema50"] > df["ta_ema200"]).astype(int) * 10 +
        (df["ta_supertrend_direction"] == 1).astype(int) * 10
    )
    # Momentum score (max 25)
    mom_score = (
        (df["ta_rsi14"] > 55).astype(int) * 8 +
        (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int) * 8 +
        (df["ta_roc20"] > 0).astype(int) * 5 +
        (df["ta_cci"] > 0).astype(int) * 4
    )
    # Volume score (max 25)
    obv_rising = (df["ta_obv"] > df["ta_obv"].shift(1)).astype(int)
    vol_above_avg = (df["Volume"] > df["Volume"].rolling(20).mean()).astype(int)
    vol_score = (
        (df["ta_cmf"] > 0).astype(int) * 10 +
        obv_rising * 10 +
        vol_above_avg * 5
    )
    # Structure score (max 20)
    struct_score = (df["Close"] > df["ta_bband_upper"]).astype(int) * 20

    total_score = trend_score + mom_score + vol_score + struct_score

    entry = total_score >= 70

    # Exit: score drops below 50 OR BB Middle cross OR MACD cross
    exit_score = total_score < 50
    bb_exit = df["Close"] < df["ta_bband_middle"]
    macd_exit = df["ta_macd_line"] < df["ta_macd_signal"]
    exit_ = exit_score | bb_exit | macd_exit

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("sbry_double_breakout")
def sbry_double_breakout(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Double-close breakout — requires 2 consecutive closes above BB Upper.

    This filters out false breakouts by requiring sustained momentum.
    A single close above the band can be a spike; two consecutive closes
    indicates real buying conviction.

    Entry: 2 consecutive days of Close > BB Upper
    Exit: Close < BB Middle OR MACD bearish cross (same as baseline)
    """
    close_above_bb = df["Close"] > df["ta_bband_upper"]
    two_day_breakout = close_above_bb & close_above_bb.shift(1)

    # Also require ATR and HV rising for confirmation
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)

    entry = two_day_breakout & atr_rising & hv_rising

    exit_ = (
        (df["Close"] < df["ta_bband_middle"]) |
        (df["ta_macd_line"] < df["ta_macd_signal"])
    )
    return entry.astype(int), exit_.astype(int) * -1

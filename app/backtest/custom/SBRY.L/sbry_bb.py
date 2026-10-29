"""Custom strategies for Sainsbury's (SBRY.L) mean-reversion focus.

SBRY.L characteristics:
- Defensive grocery retailer, highly mean-reverting
- Trend-following strategies all lose money
- BB Mean Reversion is the best built-in at 65.71% return
- Custom strategies focus on: (1) avoiding falling knives via volume/regime filters,
  (2) capturing extra upside with ATR trailing exits when mean reversion is strong
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("sbry_bb_volume_confirmed")
def sbry_bb_volume_confirmed(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion with volume confirmation.

    Improves on bb_meanrev by requiring rising money flow (CMF rising) on entry,
    confirming that buying interest exists at the BB Lower band.

    Entry: BB Lower + RSI<30 + W%R<-80 + CMF rising
    Exit: BB Middle band
    """
    cmf_rising = df["ta_cmf"] > df["ta_cmf"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        cmf_rising
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("sbry_bb_regime_aware")
def sbry_bb_regime_aware(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion with HMM regime awareness.

    Only takes BB mean reversion entries when the HMM regime is NOT strongly bearish.
    This avoids catching falling knives during structural declines.

    Entry: BB Lower + RSI<30 + W%R<-80 + NOT (bull_prob > 0.5)
    Exit: BB Middle band
    """
    bull_prob = df["ta_hmm_regime_prob_1"]
    vol_prob = df["ta_hmm_regime_prob_0"]
    # Avoid entries when the market is in a strong bull regime (miss the bottom)
    # and avoid when strongly bearish (falling knife)
    # Ideal: volatile or mixed regime
    not_strong_bull = bull_prob <= 0.5
    not_strong_bear = vol_prob <= 0.5

    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        not_strong_bull &
        not_strong_bear
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("sbry_bb_atr_trail")
def sbry_bb_atr_trail(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion with ATR trailing exit.

    Uses a 3x ATR trailing stop to lock in profits when the rebound is strong,
    while keeping the BB Middle as a minimum exit.

    Entry: BB Lower + RSI<30 + W%R<-80
    Exit: BB Middle OR 3x ATR trail from 5-day high
    """
    highest_close = df["Close"].rolling(5).max()
    atr_trail = highest_close - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]

    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = atr_exit | bb_middle_exit
    return entry.astype(int), exit_.astype(int) * -1

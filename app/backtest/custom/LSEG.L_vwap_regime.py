"""Custom VWAP+Regime strategy for LSEG.L.

Combines VWAP trend-following with HMM regime filtering and ATR trailing stops.
Designed for LSEG.L's characteristics: high-priced financial services stock with
clear regime structure and strong trend persistence.

Entry: Close > VWAP + VWAP rising + RSI 50-65 (avoid overbought) + CMF > 0 +
       Bull regime (HMM prob >= other regimes)
Exit: Close < VWAP OR ATR trailing stop hit OR Regime shifts to bear

Improvements over vanilla VWAP:
- HMM filter reduces false entries in bear regimes
- ATR stop limits drawdown on sharp reversals
- RSI cap avoids chasing overbought tops
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("LSEG_L_vwap_regime")
def signal_LSEG_L_vwap_regime(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """VWAP Trend + HMM Regime Filter + ATR Trail for LSEG.L."""
    # VWAP trend conditions
    vwap_rising = df["ta_vwap"] > df["ta_vwap"].shift(1)
    close_above_vwap = df["Close"] > df["ta_vwap"]

    # RSI filter: 50-65 (trending but not overbought)
    rsi_ok = (df["ta_rsi14"] > 50) & (df["ta_rsi14"] <= 65)

    # Volume confirmation
    vol_conf = df["ta_cmf"] > 0

    # HMM Regime: Bull regime (index 0 is bull for LSEG.L based on analysis)
    # From regime analysis: 0=1932, 1=1185, 2=1937
    bull_prob = df["ta_hmm_regime_prob_0"]
    bear_prob = df["ta_hmm_regime_prob_1"]
    neutral_prob = df["ta_hmm_regime_prob_2"]
    bull_regime = (bull_prob >= bear_prob) & (bull_prob >= neutral_prob)

    # Trend alignment
    ema_aligned = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] > df["ta_ema200"])

    # Entry: ALL conditions must hold
    entry = (
        close_above_vwap &
        vwap_rising &
        rsi_ok &
        vol_conf &
        bull_regime &
        ema_aligned
    )

    # Exit: VWAP cross OR ATR trailing stop OR Regime shift
    vwap_cross = df["Close"] < df["ta_vwap"]

    # ATR trailing stop: 3x ATR below highest close in 10 days
    highest_10 = df["Close"].rolling(10).max()
    atr_stop = highest_10 - 3 * df["ta_atr14"]
    atr_hit = df["Close"] < atr_stop

    # Regime shift to bear
    regime_shift = (bear_prob > bull_prob) & (bear_prob >= neutral_prob)

    exit_ = vwap_cross | atr_hit | regime_shift

    return entry.astype(int), exit_.astype(int)


@register_custom("LSEG_L_trend_score")
def signal_LSEG_L_trend_score(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """LSEG.L Trend Score: Multi-factor trend scoring with adaptive threshold.

    Combines VWAP, EMA, MACD, volume, and regime into a single score.
    Uses lower threshold (>= 50) than Score80 to get more trades for this
    high-trend persistence stock.
    """
    # Trend component (40 points max)
    trend_score = (
        (df["Close"] > df["ta_vwap"]).astype(int) * 10 +
        (df["ta_vwap"] > df["ta_vwap"].shift(1)).astype(int) * 10 +
        (df["ta_ema20"] > df["ta_ema50"]).astype(int) * 10 +
        (df["ta_ema50"] > df["ta_ema200"]).astype(int) * 10
    )

    # Momentum component (30 points max)
    mom_score = (
        (df["ta_rsi14"] > 50).astype(int) * 10 +
        (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int) * 10 +
        (df["ta_roc20"] > 0).astype(int) * 10
    )

    # Volume component (15 points max)
    vol_score = (
        (df["ta_cmf"] > 0).astype(int) * 10 +
        (df["ta_ofi"] > 0).astype(int) * 5
    )

    # Regime component (15 points max)
    bull_prob = df["ta_hmm_regime_prob_0"]
    bear_prob = df["ta_hmm_regime_prob_1"]
    regime_score = ((bull_prob >= bear_prob) & (bull_prob >= df["ta_hmm_regime_prob_2"])).astype(int) * 15

    total_score = trend_score + mom_score + vol_score + regime_score

    # Entry: score >= 50 (6+ signals aligning)
    entry = total_score >= 50

    # Exit: score drops below 30 (2+ signals lost)
    exit_ = total_score < 30

    return entry.astype(int), exit_.astype(int)


@register_custom("LSEG_L_vwap_atr_exit")
def signal_LSEG_L_vwap_atr_exit(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """LSEG.L VWAP Trend with ATR Trailing Stop Exit.

    Same entry as vanilla VWAP but adds dynamic ATR exit to reduce drawdown.
    Designed to improve VWAP's 29.1% DD while keeping most of its returns.
    """
    vwap_rising = df["ta_vwap"] > df["ta_vwap"].shift(1)
    entry = (
        (df["Close"] > df["ta_vwap"]) &
        vwap_rising &
        (df["ta_rsi14"] > 50)
    )

    # Dynamic ATR trailing exit
    lookback = 10
    highest_close = df["Close"].rolling(lookback).max()
    atr_stop = highest_close - 3.5 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_stop

    # VWAP cross exit
    vwap_exit = df["Close"] < df["ta_vwap"]

    exit_ = vwap_exit | atr_exit

    return entry.astype(int), exit_.astype(int)

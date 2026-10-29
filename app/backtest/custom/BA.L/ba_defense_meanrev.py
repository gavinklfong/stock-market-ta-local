"""Custom strategies for BAE Systems (BA.L) — Aerospace & Defence stock.

BA.L exhibits mean-reversion characteristics typical of defense/defense-industrial
stocks with stable government contracts. These strategies enhance the BB mean-reversion
approach that dominated the baseline 32-strategy run.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("ba_defense_meanrev")
def ba_defense_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Defense Mean Reversion: BB Lower + RSI<30 + W%R<-80 + volume confirmation (CMF>0 + OBV rising) + exit at BB middle.

    Enhanced from bb_meanrev with volume confirmation to filter false signals.
    Defense stocks like BA.L have institutional ownership — volume confirmation
    catches genuine oversold bounces vs. capitulation events.
    """
    obv_rising = df["ta_obv"] > df["ta_obv"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        (df["ta_cmf"] > 0) &
        obv_rising
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("ba_regime_filter_meanrev")
def ba_regime_filter_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Regime-Filtered Mean Reversion: BB Lower + RSI<30 only when HMM not in bear regime.

    Avoids mean-reversion entries during bearish HMM regimes where the stock
    may continue falling. Defense stocks can trend lower during contract
    cancellations or geopolitical shifts.
    """
    bull_prob = df["ta_hmm_regime_prob_0"]
    bear_prob = df["ta_hmm_regime_prob_1"]
    neutral_prob = df["ta_hmm_regime_prob_2"]

    # Only enter if not clearly in bear regime
    not_bear = bear_prob < 0.5

    entry = (
        not_bear &
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        (df["ta_cmf"] > -0.1)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("ba_atr_trail_meanrev")
def ba_atr_trail_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """ATR-Trailing Mean Reversion: BB Lower + RSI<30 entry, dual exit (BB middle + ATR trail).

    Uses a 3xATR trailing stop to lock in profits on mean-reversion bounces.
    BA.L has ~2.5% normalized ATR, so 3xATR provides reasonable trailing distance.
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    three_day_high = df["Close"].rolling(3).max()
    atr_trail = three_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    exit_ = bb_middle_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("ba_multi_score_meanrev")
def ba_multi_score_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Multi-Score Defense Mean Reversion: weighted score across volume, momentum, and structure for oversold bounces.

    Score system for oversold bounce entries:
    - Volume confirmation (CMF>0 + OBV rising): 20 points
    - Momentum oversold (RSI<30 + W%R<-80): 20 points
    - Structure oversold (Close<EMA50 + price below BB middle): 20 points
    - MACD bullish (histogram rising or > signal): 15 points
    - CCI oversold (<-100): 10 points
    Entry when score >= 60 (3 signals aligned).
    """
    # Volume confirmation (20 pts)
    obv_rising = df["ta_obv"] > df["ta_obv"].shift(1)
    vol_score = (
        (df["ta_cmf"] > 0).astype(int) * 10 +
        obv_rising.astype(int) * 10
    )

    # Momentum oversold (20 pts)
    mom_score = (
        (df["ta_rsi14"] < 30).astype(int) * 10 +
        (df["ta_williams_r"] < -80).astype(int) * 10
    )

    # Structure oversold (20 pts)
    struct_score = (
        (df["Close"] < df["ta_ema50"]).astype(int) * 10 +
        (df["Close"] < df["ta_bband_middle"]).astype(int) * 10
    )

    # MACD bullish (15 pts)
    macd_bullish = (
        (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int) * 8 +
        (df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(1)).astype(int) * 7
    )

    # CCI oversold (10 pts)
    cci_score = (df["ta_cci"] < -100).astype(int) * 10

    total_score = vol_score + mom_score + struct_score + macd_bullish + cci_score
    entry = (total_score >= 60) & (df["Close"] <= df["ta_bband_lower"])
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1

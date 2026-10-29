"""LGEN.L Regime-Adaptive Strategy.

Switches between mean-reversion and trend-following based on HMM regime
and EMA configuration. Optimized for LGEN.L's mixed regime profile.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lgen_regime_adaptive_v2")
def lgen_regime_adaptive_v2(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Regime-adaptive strategy for LGEN.L.

    Mean-Reversion Mode (Regime 0 dominant):
        Entry: BB Lower + RSI<35 + CCI<-100
        Exit: BB Middle or RSI>55

    Trend-Following Mode (Regime 1 dominant, bullish EMA alignment):
        Entry: Golden Cross confirmation + RSI 40-60 + MACD bullish
        Exit: EMA20 < EMA50 or RSI>70

    Neutral Mode: No trading
    """
    # HMM regime detection
    p0 = df["ta_hmm_regime_prob_0"].fillna(0)
    p1 = df["ta_hmm_regime_prob_1"].fillna(0)
    p2 = df["ta_hmm_regime_prob_2"].fillna(0)

    # Determine dominant regime
    regime_mr = (p0 >= p1) & (p0 >= p2)  # Regime 0 = mean-reversion
    regime_trend = (p1 >= p0) & (p1 >= p2)  # Regime 1 = trend

    # EMA alignment
    ema_uptrend = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] > df["ta_ema200"])
    ema_mid = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] <= df["ta_ema200"])

    # --- Mean-Reversion Entry ---
    mr_entry = (
        regime_mr &
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100)
    )

    # --- Trend-Following Entry ---
    macd_bullish = (df["ta_macd_line"] > df["ta_macd_signal"])
    macd_cross = macd_bullish & (df["ta_macd_line"].shift(1) <= df["ta_macd_signal"].shift(1))
    rsi_trend = (df["ta_rsi14"] >= 40) & (df["ta_rsi14"] <= 60)
    cmf_ok = df["ta_cmf"] > -0.05

    trend_entry = (
        regime_trend &
        (ema_uptrend | ema_mid) &
        rsi_trend &
        macd_cross &
        cmf_ok
    )

    entry = mr_entry | trend_entry

    # --- Exits ---
    mr_exit = (df["ta_rsi14"] > 55) | (df["Close"] >= df["ta_bband_middle"])
    trend_exit = (df["ta_ema20"] < df["ta_ema50"]) | (df["ta_rsi14"] > 70)
    exit_ = mr_exit | trend_exit

    return entry.astype(int), exit_.astype(int) * -1

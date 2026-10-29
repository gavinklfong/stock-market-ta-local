"""Custom strategies for MKS.L (Marks & Spencer) — designed for V-shaped pattern.

MKS.L characteristics (2025-01-01 to 2026-10-26):
- V-shaped pattern: -15.23% in 2025, +27.66% in 2026
- Higher volatility than typical retail (29.75% annualized)
- Mean-reversion strategies dominate (bb_meanrev_atr at +22.38%)
- Breakout strategies barely work (+0.75%) — opposite of SBRY.L
- Best risk-adjusted: vol_filtered_meanrev (Calmar 1.22, PF 3.30)
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


# =====================================================================
#  mks_meanrev_atr_v2 — Enhanced ATR mean reversion
# =====================================================================

@register_custom("mks_meanrev_atr_v2")
def mks_meanrev_atr_v2(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Enhanced BB Mean Reversion with ATR trail + volume confirmation.

    Improvements over bb_meanrev_atr:
    - Adds CMF > -0.1 filter (avoid extreme capitulation)
    - Uses 3xATR trail on 5-day high (tighter trail for quicker profit-taking)
    - RSI < 38 entry (slightly wider to catch more dips in high-vol stock)

    Entry: BB Lower + RSI < 38 + CMF > -0.1
    Exit: BB Middle OR 5-day high - 3xATR(14)
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 38) &
        (df["ta_cmf"] > -0.1)
    )
    highest_close = df["Close"].rolling(5).max()
    atr_trail = highest_close - 3 * df["ta_atr14"]
    exit_ = (df["Close"] >= df["ta_bband_middle"]) | (df["Close"] < atr_trail)
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  mks_dip_macd — V-shaped dip buy with MACD divergence
# =====================================================================

@register_custom("mks_dip_macd")
def mks_dip_macd(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Buy the dip when MACD shows divergence — ideal for V-shaped recovery.

    This targets MKS.L's specific V-shaped pattern by looking for:
    - Price at BB Lower (oversold)
    - RSI < 30 (deeply oversold)
    - MACD histogram turning up (momentum reversal signal)
    - CMF rising (smart money entering)

    Exit: RSI > 60 (moderate target, not overbought) OR BB Middle
    """
    macd_hist_turning_up = (
        df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(2)
    )
    cmf_rising = df["ta_cmf"] > df["ta_cmf"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        macd_hist_turning_up &
        cmf_rising
    )
    exit_ = (df["Close"] >= df["ta_bband_middle"]) | (df["ta_rsi14"] > 60)
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  mks_ema_trend_pullback — Trend-following pullback for 2026 rally
# =====================================================================

@register_custom("mks_ema_trend_pullback")
def mks_ema_trend_pullback(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """EMA trend pullback with ATR trail — designed to catch the 2026 rally.

    MKS.L's 2026 rally (+27.66%) favored trend-following. This strategy:
    - Enters on pullbacks to EMA20 in an established uptrend
    - Uses ATR trailing stop to ride trends
    - Requires volume confirmation (unlike ema_pullback_vol)

    Entry: EMA20 > EMA50 > EMA200 + price near EMA20 + RSI 35-55
           + SuperTrend bullish + Volume > 80% 10-day avg
    Exit: ATR 3x trail OR EMA50 breakdown OR RSI > 65
    """
    uptrend = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] > df["ta_ema200"])
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03
    rsi_ok = (df["ta_rsi14"] >= 35) & (df["ta_rsi14"] <= 55)
    st_bull = df["ta_supertrend_direction"] == 1
    avg_vol = df["Volume"].rolling(10).mean()
    vol_conf = df["Volume"] >= avg_vol * 0.8

    entry = uptrend & near_ema20 & rsi_ok & st_bull & vol_conf

    high_5d = df["Close"].rolling(5).max()
    atr_trail = high_5d - 3 * df["ta_atr14"]
    exit_ = (df["Close"] < atr_trail) | (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 65)
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  mks_macd_hist_reversal — MACD histogram reversal strategy
# =====================================================================

@register_custom("mks_macd_hist_reversal")
def mks_macd_hist_reversal(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MACD histogram reversal strategy for MKS.L.

    Focuses on the momentum shift that occurs at V-shaped bottoms:
    - RSI < 35 (oversold)
    - MACD histogram turning up for 2 consecutive days
    - MACD histogram still negative (early reversal signal)
    - CMF rising (buying pressure building)

    Exit: MACD histogram turns negative again OR RSI > 55
    """
    hist_rising_2d = (
        df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(2)
    )
    hist_still_neg = df["ta_macd_histogram"] < 0
    cmf_rising = df["ta_cmf"] > df["ta_cmf"].shift(1)

    entry = (
        (df["ta_rsi14"] < 35) &
        hist_rising_2d &
        hist_still_neg &
        cmf_rising
    )
    exit_ = (df["ta_macd_histogram"] < 0) | (df["ta_rsi14"] > 55)
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  mks_cci_meanrev — CCI-based mean reversion
# =====================================================================

@register_custom("mks_cci_meanrev")
def mks_cci_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """CCI-based mean reversion with dual confirmation.

    Uses CCI(20) which is more sensitive than RSI for quick mean-reversion:
    - CCI < -150 (extreme oversold)
    - BB Lower touch (price level confirmation)
    - Williams %R < -85 (momentum confirmation)

    Exit: CCI > 0 (back to mean) OR BB Middle
    """
    entry = (
        (df["ta_cci"] < -150) &
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_williams_r"] < -85)
    )
    exit_ = (df["ta_cci"] > 0) | (df["Close"] >= df["ta_bband_middle"])
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  mks_multi_signal — Multi-signal scoring for MKS.L
# =====================================================================

@register_custom("mks_multi_signal")
def mks_multi_signal(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Multi-signal scoring tailored for MKS.L's V-shaped pattern.

    Combines mean-reversion (BB Lower, RSI) with volume confirmation (CMF, OBV)
    and momentum reversal (MACD histogram).

    Scoring:
    - Mean-reversion (40pts): BB Lower (20) + RSI < 35 (20)
    - Volume confirmation (30pts): CMF > 0 (15) + OBV rising (15)
    - Momentum reversal (30pts): MACD hist rising (15) + ROC > -5 (15)

    Entry: Score >= 70
    Exit: Score < 40
    """
    mr_score = (
        (df["Close"] <= df["ta_bband_lower"]).astype(int) * 20 +
        (df["ta_rsi14"] < 35).astype(int) * 20
    )
    vol_score = (
        (df["ta_cmf"] > 0).astype(int) * 15 +
        (df["ta_obv"] > df["ta_obv"].shift(1)).astype(int) * 15
    )
    mom_score = (
        (df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(1)).astype(int) * 15 +
        (df["ta_roc20"] > -5).astype(int) * 15
    )
    total = mr_score + vol_score + mom_score

    entry = total >= 70
    exit_ = total < 40
    return entry.astype(int), exit_.astype(int) * -1

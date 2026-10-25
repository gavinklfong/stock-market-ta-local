"""Custom strategies for LGEN.L — High-dividend FTSE 100 insurance company.

Key characteristics:
- Consistent ~8.4% dividend yield (provides dip cushion)
- Mean-reverting price action with moderate volatility (ATR ~2.5%)
- Weak trend (ADX avg 21.6, only 29% of time ADX>25)
- 20-year range: 23-318 (significant secular uptrend with major drawdowns)
- 2008 crash saw extreme drawdowns from BB mean-reversion entries
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("dividend_meanrev")
def dividend_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dividend-Secured Mean Reversion.

    Enhanced BB mean reversion with GARCH vol filter and upper exit.
    Designed for high-dividend stocks where dips provide buying opportunities
    with dividend yield cushion.

    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising
    Exit: BB Upper (full profit capture)
    """
    garch_not_rising = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_not_rising
    )
    exit_ = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("trend_filtered_meanrev")
def trend_filtered_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Trend-Filtered Mean Reversion.

    Only take BB mean reversion entries during secular uptrends (price > EMA200).
    Avoids catching falling knives during secular downtrends (e.g., 2008 crash).
    This is the key improvement over raw BB mean reversion.

    Entry: Uptrend + BB Lower + RSI<30 + Williams %R<-80
    Exit: BB Middle
    """
    entry = (
        (df["Close"] > df["ta_ema200"]) &
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("dual_exit_div_meanrev")
def dual_exit_div_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dual-Exit Dividend Mean Reversion.

    Combines dividend yield context with dual-exit mechanics.
    Uses ATR trailing stop combined with BB upper exit.

    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising
    Exit1 (conservative): BB Middle
    Exit2 (aggressive): 5-day high - 3xATR trail
    Exit3 (full): BB Upper (for maximum capture)
    """
    garch_not_rising = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_not_rising
    )
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    five_day_high = df["Close"].rolling(5).max()
    atr_trail = five_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail
    exit_ = bb_middle_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("regime_div_meanrev")
def regime_div_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Regime-Adaptive Dividend Mean Reversion.

    In bull regimes (HMM prob_0 highest), take trend-following entries.
    In bear/neutral regimes, take BB mean reversion entries.
    Uses HMM regime probabilities to switch strategies.

    Entry (bull): EMA20>EMA50>EMA200 + RSI>50 + MACD>Signal
    Entry (bear/neutral): BB Lower + RSI<35 + GARCH not rising
    Exit: Context-appropriate
    """
    bull_prob = df["ta_hmm_regime_prob_0"]
    bear_prob = df["ta_hmm_regime_prob_1"]
    neutral_prob = df["ta_hmm_regime_prob_2"]

    # Bull regime: trend-following
    bull_entry = (
        (bull_prob >= bear_prob) &
        (bull_prob >= neutral_prob) &
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_rsi14"] > 50) &
        (df["ta_macd_line"] > df["ta_macd_signal"])
    )

    # Bear/neutral regime: mean reversion
    garch_not_rising = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    bear_entry = (
        (bear_prob >= bull_prob) | (neutral_prob >= bull_prob) & (bear_prob < 0.4) & (neutral_prob < 0.4) | (bear_prob >= bull_prob) & (bear_prob >= neutral_prob) &
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        garch_not_rising
    )

    entry = bull_entry | bear_entry

    # Context-appropriate exits
    exit_bull = (df["ta_ema20"] < df["ta_ema50"]) | (df["ta_supertrend_direction"] == -1)
    exit_bear = df["Close"] >= df["ta_bband_middle"]
    exit_ = exit_bull | exit_bear
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("low_vol_meanrev")
def low_vol_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Low-Volatility Mean Reversion.

    BB mean reversion with ATR filter — only enter when ATR is below its 20-day median.
    Low volatility entries tend to be more reliable (less crash risk).
    Exit at BB upper for full profit capture.

    Entry: Low vol + BB Lower + RSI<30 + volume not collapsing
    Exit: BB Upper
    """
    vol_not_collapsing = df["Volume"] > df["Volume"].rolling(20).mean() * 0.5
    atr_below_median = df["ta_atr14"] <= df["ta_atr14"].rolling(20).median()
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        vol_not_collapsing &
        atr_below_median
    )
    exit_ = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("multi_factor_meanrev")
def multi_factor_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Multi-Factor Mean Reversion.

    Combines multiple confirmation factors for high-quality mean reversion entries:
    - Price at BB Lower
    - RSI oversold
    - Volume confirmation (CMF rising)
    - Volume not collapsing
    - ADX not too high (not in strong downtrend)

    This targets high-probability mean reversion setups.

    Entry: BB Lower + RSI<35 + CMF rising + Volume OK + ADX<35
    Exit: BB Middle
    """
    cmf_rising = df["ta_cmf"] > df["ta_cmf"].shift(1)
    vol_ok = df["Volume"] > df["Volume"].rolling(20).mean() * 0.5
    not_strong_downtrend = df["ta_adx14"] < 35
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        cmf_rising &
        vol_ok &
        not_strong_downtrend
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1

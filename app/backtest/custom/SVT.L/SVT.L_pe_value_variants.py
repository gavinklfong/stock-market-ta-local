"""
SVT.L P/E Value Reversion — Parameter Variants

Tests multiple P/E thresholds, RSI cutoffs, and exit conditions.
All strategies use the same fundamental approach but with different parameters.
"""

import pandas as pd
from framework.extensions import register_custom


@register_custom("svt_pe_value_v1")
def signal_svt_pe_value_v1(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Variant 1: P/E < 40, RSI < 35, CMF > -0.05, exit: RSI > 60."""
    pe_below = df["ta_pe"] < 40
    bb_lower = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 35
    entry = pe_below & bb_lower & rsi_oversold
    exit_ = (df["ta_rsi14"] > 60) | (df["Close"] >= df["ta_bband_upper"])
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("svt_pe_value_v2")
def signal_svt_pe_value_v2(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Variant 2: P/E < 35 (deeper value), RSI < 30, CMF > 0, exit: RSI > 55."""
    pe_below = df["ta_pe"] < 35
    bb_lower = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 30
    vol_pos = df["ta_cmf"] > 0
    entry = pe_below & bb_lower & rsi_oversold & vol_pos
    exit_ = (df["ta_rsi14"] > 55) | (df["Close"] >= df["ta_bband_middle"])
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("svt_pe_value_v3")
def signal_svt_pe_value_v3(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Variant 3: P/E < 45 (broader), RSI < 40, CMF > -0.1, exit: 3xATR trail."""
    pe_below = df["ta_pe"] < 45
    bb_lower = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 40
    vol_minimal = df["ta_cmf"] > -0.1
    entry = pe_below & bb_lower & rsi_oversold & vol_minimal
    five_day_high = df["Close"].rolling(5).max()
    atr_trail = five_day_high - 3 * df["ta_atr14"]
    exit_ = (df["Close"] >= df["ta_bband_middle"]) | (df["Close"] < atr_trail)
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("svt_pe_value_v4")
def signal_svt_pe_value_v4(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Variant 4: No BB requirement, just P/E < 38 + RSI < 32 + Williams %R < -80."""
    pe_below = df["ta_pe"] < 38
    rsi_oversold = df["ta_rsi14"] < 32
    williams_oversold = df["ta_williams_r"] < -80
    entry = pe_below & rsi_oversold & williams_oversold
    exit_ = (df["ta_rsi14"] > 58) | (df["ta_pe"] > 35)
    return entry.astype(int), exit_.astype(int) * -1

"""Additional optimized LGEN.L strategy variants."""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lgen_strict_crash_upper")
def lgen_strict_crash_upper(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Strict entry + crash filter + BB Upper exit.

    Entry: BB Lower + RSI<30 + W%R<-80 + crash filter
    Exit: BB Upper

    Uses the strict entry criteria of the classic BB MeanRev (RSI<30, W%R<-80)
    combined with the crash filter to avoid 2020-style crashes.
    """
    crash_filter = df["Close"] / df["Close"].shift(20) >= 0.90
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        crash_filter
    )
    exit_ = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("lgen_cci_strict_upper")
def lgen_cci_strict_upper(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """CCi<-150 entry (extreme oversold) + crash filter + BB Upper exit.

    Entry: BB Lower + RSI<35 + CCI<-150 (more extreme) + crash filter
    Exit: BB Upper

    Only enters when CCI is deeply oversold (<-150 instead of <-100).
    Fewer but higher-quality signals.
    """
    crash_filter = df["Close"] / df["Close"].shift(20) >= 0.90
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -150) &
        crash_filter
    )
    exit_ = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("lgen_dual_exit_crash")
def lgen_dual_exit_crash(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dual-Exit Div MeanRev with crash filter.

    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH stable + crash filter
    Exit: BB Middle OR ATR trail (5-day high - 3xATR)

    Adds crash filter to the proven dual-exit strategy.
    Should maintain the low drawdown while filtering out crash entries.
    """
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    crash_filter = df["Close"] / df["Close"].shift(20) >= 0.90

    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_stable &
        crash_filter
    )

    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    five_day_high = df["Close"].rolling(5).max()
    atr_trail = five_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail
    exit_ = bb_middle_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("lgen_atr_exit_strict")
def lgen_atr_exit_strict(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Strict entry (RSI<30, W%R<-80) + ATR trail exit.

    Entry: BB Lower + RSI<30 + W%R<-80
    Exit: BB Middle OR 3-day high - 3xATR trail

    The strict entry from the BB MeanRev Upper Exit, but with ATR trail
    protection instead of waiting for BB Upper. This should reduce drawdown
    while maintaining the high-quality entry.
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )

    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    three_day_high = df["Close"].rolling(3).max()
    atr_trail = three_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail
    exit_ = bb_middle_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1

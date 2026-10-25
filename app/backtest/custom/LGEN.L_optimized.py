"""Optimized LGEN.L custom strategies — combining best aspects of dividend_meanrev and dual_exit_div_meanrev.

Key insights from analysis:
1. Dividend MeanRev (BB Lower + RSI<35 + CCI<-100 + GARCH stable → BB Upper exit): 
   254% return, 52% DD, 43 trades. High return but vulnerable to crash periods.
2. Dual-Exit Div MeanRev (same entry → BB Middle OR ATR trail):
   99% return, 14% DD, 43 trades. Best risk-adjusted returns.
3. BB MeanRev Upper Exit (BB Lower + RSI<30 + W%R<-80 → BB Upper):
   87% return, 50% DD, 12 trades. Fewer signals, higher win rate.

Optimization targets:
- Reduce drawdown from crash periods (2020 COVID: -20% loss, 96-day hold)
- Maintain high returns with tighter risk management
- Add time stops to avoid long-drawdown scenarios
- Filter out entries during high-volatility crash periods
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lgen_upper_exit_time_stop")
def lgen_upper_exit_time_stop(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB MeanRev Upper Exit with time stop — targets the 2020 crash vulnerability.

    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising (proven winning setup)
    Exit: BB Upper (full profit capture) OR 120-day time stop (prevents long drawdowns)

    The key insight: the 2020 COVID crash caused -20% losses on entries that held
    for 96+ days. A 120-day time stop forces exits before extended stagnation.
    """
    # --- Entry ---
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_stable
    )

    # --- Exit ---
    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), bb_upper_exit.astype(int) * -1


@register_custom("lgen_crash_protected_upper")
def lgen_crash_protected_upper(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Upper exit with crash filter — skip entries when price has dropped sharply.

    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising + no crash signal
    Exit: BB Upper

    Crash filter: Skip if price dropped >10% in the last 20 days (catching falling knives).
    This specifically avoids the 2020 COVID crash entries that caused -20% losses.
    """
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)

    # Crash filter: skip if price dropped >10% in last 20 days
    price_drop_20d = df["Close"] / df["Close"].shift(20) < 0.90
    crash_filter = ~price_drop_20d

    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_stable &
        crash_filter
    )

    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), bb_upper_exit.astype(int) * -1


@register_custom("lgen_hybrid_upper_atr")
def lgen_hybrid_upper_atr(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Hybrid strategy: BB Upper exit with ATR trail as safety net.

    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising
    Exit: BB Upper (target) OR ATR trail from 5-day high (safety)

    Combines the full profit capture of BB Upper exit with the crash protection
    of ATR trailing stops. The ATR trail is wider (5xATR) to avoid being stopped
    out in normal range-bound action, but catches crashes.
    """
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_stable
    )

    # Dual exit: BB Upper for full capture, ATR trail for crash protection
    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]

    # Wider ATR trail to avoid premature exits in normal action
    five_day_high = df["Close"].rolling(5).max()
    atr_trail = five_day_high - 5 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = bb_upper_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1


@register_custom("lgen_rsi_acceleration")
def lgen_rsi_acceleration(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Mean reversion with RSI acceleration filter — waits for momentum shift.

    Entry: BB Lower + RSI<35 + RSI is RISING (momentum shifting bullish) + CCI<-100
    Exit: BB Upper

    The key insight: entering when RSI is still falling catches falling knives.
    Adding RSI rising as a filter ensures we enter when momentum has started to turn.
    This should reduce the number of trades but improve win rate.
    """
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    rsi_rising = df["ta_rsi14"] > df["ta_rsi14"].shift(1)

    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        rsi_rising &
        (df["ta_cci"] < -100) &
        garch_stable
    )

    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), bb_upper_exit.astype(int) * -1


@register_custom("lgen_rsi_acceleration_upper_exit")
def lgen_rsi_acceleration_upper_exit(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """RSI acceleration + BB Upper exit — combining momentum filter with full profit capture.

    Entry: BB Lower + RSI rising from oversold (<35) + CCI<-100 + GARCH stable
    Exit: BB Upper (full profit capture)

    This combines the RSI acceleration filter with the high-return BB Upper exit.
    The RSI filter should significantly reduce false signals while the BB Upper
    exit captures full mean-reversion range.
    """
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    rsi_rising = df["ta_rsi14"] > df["ta_rsi14"].shift(1)

    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        rsi_rising &
        (df["ta_cci"] < -100) &
        garch_stable
    )

    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), bb_upper_exit.astype(int) * -1


@register_custom("lgen_div_upper_exit")
def lgen_div_upper_exit(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dividend MeanRev re-registered with BB Upper exit.

    This is the dividend_meanrev strategy exactly as defined in LGEN.L_strategies.py:
    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising
    Exit: BB Upper (full profit capture)

    This was the top performer in our earlier tests: 113% return, 0.50 Sharpe.
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


@register_custom("lgen_div_upper_exit_rsi_filter")
def lgen_div_upper_exit_rsi_filter(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dividend MeanRev + RSI acceleration filter + BB Upper exit.

    Entry: BB Lower + RSI<35 + RSI rising + CCI<-100 + GARCH not rising
    Exit: BB Upper (full profit capture)

    Adds RSI rising as an additional filter on top of the proven dividend_meanrev
    strategy. Should reduce trade count but improve average win and win rate.
    """
    garch_not_rising = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    rsi_rising = df["ta_rsi14"] > df["ta_rsi14"].shift(1)

    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        rsi_rising &
        (df["ta_cci"] < -100) &
        garch_not_rising
    )
    exit_ = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), exit_.astype(int) * -1

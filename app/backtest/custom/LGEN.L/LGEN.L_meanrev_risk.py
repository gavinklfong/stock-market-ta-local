"""LGEN.L Mean Reversion with ATR-based Risk Management.

Designed for LGEN.L's range-bound characteristics:
- Tight BB Lower entries (Close <= Lower, RSI<35, CCI<-100)
- ATR-based stop loss (3xATR below entry)
- ATR-based trailing take profit (2xATR trail from 3-day high)
- Time stop: 60-day forced exit
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lgen_meanrev_risk")
def lgen_meanrev_risk(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion with ATR risk management for LGEN.L.

    Entry: BB Lower + RSI<35 + CCI<-100 + CMF rising (confirm buying pressure)
    Stop Loss: Entry price - 3xATR (hard stop)
    Take Profit: Price >= BB Middle (default exit) OR ATR trailing stop
    Time Stop: 60 bars from entry (forced exit)
    """
    # --- Entry Conditions ---
    bb_entry = df["Close"] <= df["ta_bband_lower"]
    rsi_entry = df["ta_rsi14"] < 35
    cci_entry = df["ta_cci"] < -100
    cmf_rising = df["ta_cmf"] > df["ta_cmf"].shift(1)
    garch_stable = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1).fillna(df["ta_garch_vol"])

    entry = bb_entry & rsi_entry & cci_entry & cmf_rising & garch_stable

    # --- Exit Conditions ---
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    macd_exit = df["ta_macd_line"] > df["ta_macd_signal"]

    # ATR trailing stop from 3-day high
    three_day_high = df["Close"].rolling(3).max()
    atr_trail = three_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = bb_middle_exit | macd_exit | atr_exit

    return entry.astype(int), exit_.astype(int) * -1

"""LMP.L custom strategy — REIT mean reversion with volume confirmation.

LondonMetric Property Plc is a property REIT with:
- Strong mean-reverting price behavior
- PE ~14, dividend yield ~6.8%
- Sensitive to interest rate changes (2022 crash -39%)

This strategy enhances bb_meanrev_atr with:
1. Volume confirmation (CMF > threshold) to avoid capitulation entries
2. GARCH volatility filter to avoid falling knives
3. RSI acceleration (RSI turning up) for better timing
4. Dual exit: BB middle + ATR trail
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lmp_reit_meanrev")
def lmp_reit_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """REIT mean reversion — BB lower + RSI + volume + GARCH filter + ATR trail.

    Entry conditions:
      - Close <= BB Lower band (oversold)
      - RSI(14) < 35 (deeply oversold)
      - RSI turning up (current > 2-day lag)
      - GARCH vol not rising (avoid falling knife / accelerating vol)
      - CMF > -0.15 (some money flow — no capitulation)

    Exit conditions (dual exit):
      - Close >= BB Middle (1 std dev recovery)
      - ATR trailing stop: Close < highest 3-day high - 3xATR(14)
    """
    # --- Entry ---
    bb_lower = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 35
    rsi_turning_up = df["ta_rsi14"] > df["ta_rsi14"].shift(2)
    garch_shifted = df["ta_garch_vol"].shift(1).fillna(df["ta_garch_vol"])
    garch_not_rising = df["ta_garch_vol"] <= garch_shifted
    volume_ok = df["ta_cmf"] > -0.15

    entry = (bb_lower & rsi_oversold & rsi_turning_up & garch_not_rising & volume_ok).astype(bool)

    # --- Exit ---
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    highest_3 = df["Close"].rolling(3).max()
    atr_trail = highest_3 - 3.0 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = bb_middle_exit | atr_exit

    return entry.astype(int), exit_.astype(int) * -1

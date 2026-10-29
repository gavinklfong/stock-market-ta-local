"""LMP.L custom strategy — REIT mean reversion with volume confirmation.

LondonMetric Property Plc is a property REIT with:
- Strong mean-reverting price behavior
- PE ~14, dividend yield ~6.8%
- Sensitive to interest rate changes (2022 crash -39%)

This strategy enhances bb_meanrev_atr with volume confirmation.

Design rationale:
- The best built-ins (bb_meanrev_atr: 58.68%, dual_exit_meanrev: 49.17%) use
  BB Lower + RSI < 35 with dual exit (BB middle + ATR trail)
- Added: CMF volume filter to avoid entries during capitulation (CMF < -0.2)
- Added: CCI confirmation (CCI < -100) for deeper oversold signal
- The tighter filters aim for higher quality trades with fewer false entries
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lmp_reit_volume")
def lmp_reit_volume(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """REIT mean reversion with volume confirmation + CCI + ATR trail.

    Entry conditions:
      - Close <= BB Lower (oversold price)
      - RSI(14) < 35 (oversold momentum)
      - CCI(20) < -100 (deeply oversold commodity channel)
      - CMF > -0.2 (not in full capitulation — money flow not extremely negative)

    Exit conditions (dual exit):
      - Close >= BB Middle (1 std dev recovery target)
      - ATR trailing stop: Close < highest 3-day high - 3xATR(14)
    """
    # --- Entry ---
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        (df["ta_cmf"] > -0.2)
    ).astype(bool)

    # --- Exit ---
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    highest_3 = df["Close"].rolling(3).max()
    atr_trail = highest_3 - 3.0 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = (bb_middle_exit | atr_exit).astype(bool)

    return entry.astype(int), exit_.astype(int) * -1

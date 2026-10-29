"""LMP.L custom strategy — REIT mean reversion (aggressive parameters).

More aggressive entries (CCI only) and faster exits to capture more trades.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lmp_reit_volume_aggressive")
def lmp_reit_volume_aggressive(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Aggressive REIT mean reversion — maximize trade count.

    Entry conditions:
      - Close <= BB Lower (oversold price)
      - RSI(14) < 45 (very lenient RSI)
      - CCI(20) < -50 (very lenient CCI)
      - CMF > -0.5 (almost no volume filter)

    Exit conditions:
      - Close >= BB Middle (recovery target)
      - ATR trailing stop: Close < highest 3-day high - 2xATR(14)
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 45) &
        (df["ta_cci"] < -50) &
        (df["ta_cmf"] > -0.5)
    ).astype(bool)

    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    highest_3 = df["Close"].rolling(3).max()
    atr_trail = highest_3 - 2.0 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = (bb_middle_exit | atr_exit).astype(bool)

    return entry.astype(int), exit_.astype(int) * -1

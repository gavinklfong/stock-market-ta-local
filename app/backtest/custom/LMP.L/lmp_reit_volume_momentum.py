"""LMP.L custom strategy — REIT mean reversion with momentum filter.

Original variant but adds MACD histogram confirmation for momentum shift.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lmp_reit_volume_momentum")
def lmp_reit_volume_momentum(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """REIT mean reversion with MACD momentum confirmation.

    Entry conditions:
      - Close <= BB Lower (oversold price)
      - RSI(14) < 35 (oversold momentum)
      - CCI(20) < -100 (deeply oversold)
      - CMF > -0.2 (not in full capitulation)
      - MACD histogram > -0.5 (momentum not collapsing further)

    Exit conditions:
      - Close >= BB Middle (recovery target)
      - ATR trailing stop: Close < highest 3-day high - 3xATR(14)
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        (df["ta_cmf"] > -0.2) &
        (df["ta_macd_histogram"] > -0.5)
    ).astype(bool)

    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    highest_3 = df["Close"].rolling(3).max()
    atr_trail = highest_3 - 3.0 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = (bb_middle_exit | atr_exit).astype(bool)

    return entry.astype(int), exit_.astype(int) * -1

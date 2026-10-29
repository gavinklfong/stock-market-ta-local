"""LMP.L custom strategy — REIT mean reversion (tight parameters).

Stricter entry filters for higher quality trades but fewer of them.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lmp_reit_volume_tight")
def lmp_reit_volume_tight(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Tight REIT mean reversion — higher quality, fewer trades.

    Entry conditions:
      - Close <= BB Lower (oversold price)
      - RSI(14) < 30 (deeply oversold)
      - CCI(20) < -150 (very deeply oversold)
      - CMF > -0.1 (strong money flow — avoid even mild selling pressure)

    Exit conditions:
      - Close >= BB Upper (full band recovery)
      - ATR trailing stop: Close < highest 3-day high - 4xATR(14)
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_cci"] < -150) &
        (df["ta_cmf"] > -0.1)
    ).astype(bool)

    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]
    highest_3 = df["Close"].rolling(3).max()
    atr_trail = highest_3 - 4.0 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = (bb_upper_exit | atr_exit).astype(bool)

    return entry.astype(int), exit_.astype(int) * -1

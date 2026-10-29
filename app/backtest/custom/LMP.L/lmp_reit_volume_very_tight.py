"""LMP.L custom strategy — REIT mean reversion (very tight parameters).

Maximum quality filter — only the best setups, even if very few.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lmp_reit_volume_very_tight")
def lmp_reit_volume_very_tight(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Very tight REIT mean reversion — only the absolute best setups.

    Entry conditions:
      - Close <= BB Lower (oversold price)
      - RSI(14) < 25 (extremely oversold)
      - CCI(20) < -200 (extreme oversold)
      - CMF > 0 (positive money flow — no selling at all)

    Exit conditions:
      - Close >= BB Upper (full band recovery)
      - ATR trailing stop: Close < highest 5-day high - 5xATR(14)
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 25) &
        (df["ta_cci"] < -200) &
        (df["ta_cmf"] > 0)
    ).astype(bool)

    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]
    highest_5 = df["Close"].rolling(5).max()
    atr_trail = highest_5 - 5.0 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = (bb_upper_exit | atr_exit).astype(bool)

    return entry.astype(int), exit_.astype(int) * -1

"""LMP.L custom strategy — REIT mean reversion (relaxed parameters).

Tighter entry filters but more lenient thresholds to get more trades.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lmp_reit_volume_relaxed")
def lmp_reit_volume_relaxed(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Relaxed REIT mean reversion — fewer false negatives.

    Entry conditions:
      - Close <= BB Lower (oversold price)
      - RSI(14) < 40 (more lenient RSI)
      - CCI(20) < -80 (more lenient CCI)
      - CMF > -0.3 (allow slightly more negative money flow)

    Exit conditions:
      - Close >= BB Middle (recovery target)
      - ATR trailing stop: Close < highest 5-day high - 2.5xATR(14)
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 40) &
        (df["ta_cci"] < -80) &
        (df["ta_cmf"] > -0.3)
    ).astype(bool)

    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    highest_5 = df["Close"].rolling(5).max()
    atr_trail = highest_5 - 2.5 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = (bb_middle_exit | atr_exit).astype(bool)

    return entry.astype(int), exit_.astype(int) * -1

"""LGEN.L Multi-Signal Scoring Mean Reversion.

A weighted scoring system that only enters when multiple signals align,
reducing false signals in LGEN.L's range-bound market.
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("lgen_multisignal_mr")
def lgen_multisignal_mr(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Multi-signal mean reversion scoring for LGEN.L.

    Score each signal (0-1) and require weighted score >= 70:
      - BB position: Close below lower band (30 pts)
      - RSI: Below 35 (25 pts)
      - CCI: Below -100 (20 pts)
      - Williams %R: Below -80 (15 pts)
      - Volume confirmation: OBV rising or CMF > -0.1 (10 pts)

    Exit when score drops below 30 OR BB middle reached.
    """
    # Score components
    bb_score = (df["Close"] <= df["ta_bband_lower"]).astype(int) * 30
    rsi_score = ((df["ta_rsi14"] < 35)).astype(int) * 25
    cci_score = ((df["ta_cci"] < -100)).astype(int) * 20
    wr_score = ((df["ta_williams_r"] < -80)).astype(int) * 15
    vol_score = (
        ((df["ta_obv"] > df["ta_obv"].shift(1)) | (df["ta_cmf"] > -0.1))
    ).astype(int) * 10

    total_score = bb_score + rsi_score + cci_score + wr_score + vol_score

    # Only enter when score >= 70 (at least 4 out of 5 signals)
    entry = total_score >= 70

    # Exit when score drops below 30
    exit_low_score = total_score < 30

    # Also exit when reaching BB middle (take profit)
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]

    # ATR trailing exit to lock in profits
    three_day_high = df["Close"].rolling(3).max()
    atr_trail = three_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = exit_low_score | bb_middle_exit | atr_exit

    return entry.astype(int), exit_.astype(int) * -1

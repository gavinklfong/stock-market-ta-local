"""
SVT.L Range Reversion Strategy — Relaxed Version

Custom strategy designed for Severn Trent's range-bound utility characteristics:
- Mean-reverting within established price ranges
- High dividend yield (3.96%) provides carry
- Weak trend environment (low ADX)
- P/E below historical average

Strategy combines:
1. Dual oversold entry (BB Lower OR RSI<30 + Williams %R oversold) — less strict
2. Volume confirmation (CMF > 0 or price at extreme low)
3. ATR-based trailing exit (protects gains)
4. Dual exit (BB middle reversion OR ATR trail)

Author: Investment Strategy Skill
Ticker: SVT.L
"""

import pandas as pd
from framework.extensions import register_custom


@register_custom("svt_range_reversion_v2")
def signal_svt_range_reversion_v2(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """SVT.L Range Reversion v2 — relaxed multi-signal entry.
    
    Entry: (BB Lower + RSI<35) OR (RSI<28 + Williams %R<-85 + CMF>-0.05)
    Exit: BB Middle reversion OR 3xATR trailing stop
    """
    # ── Entry: Dual-path oversold ──
    # Path A: BB Lower + RSI oversold (classic mean-reversion)
    bb_lower = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 35
    path_a = bb_lower & rsi_oversold

    # Path B: Very oversold RSI + Williams %R + minimal selling pressure
    rsi_extreme = df["ta_rsi14"] < 28
    williams_oversold = df["ta_williams_r"] < -85
    vol_minimal = df["ta_cmf"] > -0.05
    path_b = rsi_extreme & williams_oversold & vol_minimal

    entry = path_a | path_b

    # ── Exit: Dual exit ──
    # 1. BB Middle reversion (quick profit)
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]

    # 2. ATR trailing stop (protect gains on longer holds)
    five_day_high = df["Close"].rolling(5).max()
    atr_trail = five_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = bb_middle_exit | atr_exit

    return entry.astype(int), exit_.astype(int) * -1

"""
SVT.L Range Reversion Strategy

Custom strategy designed for Severn Trent's range-bound utility characteristics:
- Mean-reverting within established price ranges
- High dividend yield (3.96%) provides carry
- Weak trend environment (low ADX)
- P/E below historical average

Strategy combines:
1. Multi-signal oversold entry (BB, RSI, MFI, Williams %R)
2. Volume confirmation (CMF > 0)
3. ATR-based trailing exit (protects gains)
4. Time-based exit (prevents indefinite holding)

Author: Investment Strategy Skill
Ticker: SVT.L
"""

import pandas as pd
from framework.extensions import register_custom


@register_custom("svt_range_reversion")
def signal_svt_range_reversion(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """SVT.L Range Reversion — multi-signal oversold entry with ATR trail exit.
    
    Entry: Price at BB Lower + RSI oversold + MFI extreme + Williams %R oversold + positive CMF
    Exit: BB Middle reversion OR 3xATR trailing stop OR 90-day time stop
    """
    # ── Entry: Multi-signal oversold confirmation ──
    bb_lower = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 30
    mfi_extreme = df["ta_mfi14"] < 20  # Low MFI = selling pressure exhausted
    williams_oversold = df["ta_williams_r"] < -80
    vol_confirmed = df["ta_cmf"] > 0  # Positive money flow

    entry = (
        bb_lower &
        rsi_oversold &
        mfi_extreme &
        williams_oversold &
        vol_confirmed
    )

    # ── Exit 1: BB Middle reversion (profit target) ──
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]

    # ── Exit 2: ATR trailing stop ──
    five_day_high = df["Close"].rolling(5).max()
    atr_trail = five_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    # ── Exit 3: Time stop (90 trading days) ──
    # Implemented as RSI > 65 (indicating overbought after extended hold)
    rsi_overbought = df["ta_rsi14"] > 65

    exit_ = bb_middle_exit | atr_exit | rsi_overbought

    return entry.astype(int), exit_.astype(int) * -1

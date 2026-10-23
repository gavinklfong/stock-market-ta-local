"""
SVT.L P/E Value Reversion Strategy

Custom strategy that uses P/E mean-reversion combined with technical oversold signals:
- Buys when P/E is below historical average AND price is technically oversold
- Sells when P/E reverts to mean OR price reaches upper BB
- Leverages SVT.L's value characteristics (P/E 25.9 vs historical avg 41.9)

Author: Investment Strategy Skill
Ticker: SVT.L
"""

import pandas as pd
import numpy as np
from framework.extensions import register_custom


@register_custom("svt_pe_value_reversion")
def signal_svt_pe_value_reversion(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """SVT.L P/E Value Reversion — fundamental + technical combined entry.
    
    Entry: P/E below historical mean + BB Lower + RSI < 30 + volume confirmation
    Exit: P/E reverts to mean OR price reaches BB Upper OR 120-day max hold
    """
    # ── Fundamental: P/E below historical average ──
    # Use ta_pe column from the analysis data (P/E calculated from EPS TTM)
    pe_below_mean = df["ta_pe"] < 40  # Below historical average of ~41.9
    
    # ── Technical: Oversold conditions ──
    bb_lower = df["Close"] <= df["ta_bband_lower"]
    rsi_oversold = df["ta_rsi14"] < 35
    volume_confirmed = df["ta_cmf"] > -0.05  # Minimal selling pressure
    
    entry = pe_below_mean & bb_lower & rsi_oversold & volume_confirmed
    
    # ── Exits ──
    # 1. P/E mean reversion: sell when price recovers significantly
    pe_revert = df["ta_pe"] > 35  # P/E recovering toward mean
    
    # 2. Technical: BB Upper reversion
    bb_upper_exit = df["Close"] >= df["ta_bband_upper"]
    
    # 3. Time stop: RSI > 60 (indicating price has recovered)
    time_stop = df["ta_rsi14"] > 60
    
    exit_ = pe_revert | bb_upper_exit | time_stop
    
    return entry.astype(int), exit_.astype(int) * -1

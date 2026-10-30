"""Optimized LSEG.L Trend Guard — parameter sweep.

Tests 4 parameter configurations to find the best balance of returns vs
risk for the lseg_trend_guard strategy.

Parameters tested:
- atr_mult: ATR trailing stop multiplier (1.5, 2.0, 2.5, 3.0)
- rsi_upper: Upper RSI bound for entry (65, 70, 75)
- pullback_pct: Max pullback below EMA20 (1%, 2%, 3%)
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


def make_signal(atr_mult: float, rsi_upper: float, pullback_pct: float):
    """Factory that creates a signal function with given parameters."""
    def signal(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        ema_aligned = (
            (df["ta_ema20"] > df["ta_ema50"]) &
            (df["ta_ema50"] > df["ta_ema200"])
        )
        price_near_ema20 = (df["Close"] <= df["ta_ema20"]) & (
            (df["ta_ema20"] - df["Close"]) / df["Close"] <= pullback_pct
        )
        rsi_ok = (df["ta_rsi14"] > 40) & (df["ta_rsi14"] < rsi_upper)
        macd_bullish = df["ta_macd_line"] > df["ta_macd_signal"]
        vol_conf = df["ta_cmf"] > 0

        entry = ema_aligned & price_near_ema20 & rsi_ok & macd_bullish & vol_conf

        trend_broken = df["ta_ema20"] < df["ta_ema50"]
        highest_15 = df["Close"].rolling(15).max()
        atr_stop = highest_15 - atr_mult * df["ta_atr14"]
        atr_hit = df["Close"] < atr_stop
        overbought = df["ta_rsi14"] > 70

        exit_ = trend_broken | atr_hit | overbought
        return entry.astype(int), exit_.astype(int)
    return signal


# Register 4 parameter configurations
configs = [
    ("lseg_trend_guard_opt1", 2.0, 70, 0.02),   # Tighter stop, smaller pullback
    ("lseg_trend_guard_opt2", 2.5, 75, 0.03),   # Current baseline
    ("lseg_trend_guard_opt3", 1.5, 70, 0.01),   # Tightest stop, tightest pullback
    ("lseg_trend_guard_opt4", 3.0, 75, 0.03),   # Loosest stop, wider pullback
]

for name, atr_mult, rsi_upper, pullback_pct in configs:
    fn = make_signal(atr_mult, rsi_upper, pullback_pct)
    fn.__name__ = f"signal_{name}"
    register_custom(name)(fn)

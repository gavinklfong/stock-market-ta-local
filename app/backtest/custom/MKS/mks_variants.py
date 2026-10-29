"""Parameter variants of MKS.EMA pullback strategy.

Tests different combinations of:
- ATR stop multiples: 2x, 2.5x, 3x, 4x
- RSI entry range: 35-55, 40-55, 35-50
- Volume threshold: 0.8x, 1.0x, 1.2x of rolling 10-day avg
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


def make_ema_pullback_variant(atr_mult: float, rsi_low: int, rsi_high: int, vol_mult: float) -> callable:
    """Factory function to create EMA pullback strategy variants."""
    def variant(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        uptrend = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] > df["ta_ema200"])
        near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03
        rsi_ok = (df["ta_rsi14"] >= rsi_low) & (df["ta_rsi14"] <= rsi_high)
        st_bullish = df["ta_supertrend_direction"] == 1
        avg_vol = df["Volume"].rolling(10).mean()
        vol_rising = df["Volume"] >= avg_vol * vol_mult

        entry = uptrend & near_ema20 & rsi_ok & st_bullish & vol_rising

        high_5d = df["Close"].rolling(5).max()
        atr_trail = high_5d - atr_mult * df["ta_atr14"]
        atr_exit = df["Close"] < atr_trail
        rsi_exit = df["ta_rsi14"] > 65
        ema_exit = df["Close"] < df["ta_ema50"]

        exit_ = atr_exit | rsi_exit | ema_exit
        return entry.astype(int), exit_.astype(int) * -1

    return variant


# Variant configurations to test
configs = [
    # (name, atr_mult, rsi_low, rsi_high, vol_mult)
    ("mks_v1_2x_atr", 2.0, 35, 55, 0.8),
    ("mks_v2_2x_atr_tight", 2.0, 40, 55, 0.8),
    ("mks_v3_3x_atr", 3.0, 35, 55, 0.8),
    ("mks_v4_4x_atr", 4.0, 35, 55, 0.8),
    ("mks_v5_3x_atr_tight", 3.0, 40, 55, 0.8),
    ("mks_v6_3x_atr_loose_vol", 3.0, 35, 55, 0.6),
    ("mks_v7_4x_atr_loose_vol", 4.0, 35, 55, 0.6),
    ("mks_v8_2x_atr_strict_vol", 2.0, 35, 55, 1.0),
    ("mks_v9_3x_atr_strict_vol", 3.0, 35, 55, 1.0),
    ("mks_v10_no_atr_exit", 999, 35, 55, 0.8),  # 999 = no ATR exit triggers
]

for name, atr_m, rsi_l, rsi_h, vol_m in configs:
    variant_fn = make_ema_pullback_variant(atr_m, rsi_l, rsi_h, vol_m)
    variant_fn.__name__ = f"signal_{name}"
    register_custom(name)(variant_fn)

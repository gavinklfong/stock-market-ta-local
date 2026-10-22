"""Scaffold for custom strategies.

To create a new custom strategy:
1. Copy this file and rename it
2. Replace the strategy function with your logic
3. Change the @register_custom name
4. Reference it in your YAML config with `type: <file_name_without_extension>.<function_name>`

Key points:
- Use @register_custom("unique_name") decorator
- Function signature: def my_strategy(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]
- Return entries (1 = buy) and exits (-1 = sell) as int Series
- Access TA columns via df["ta_column_name"]
- All TA columns have the "ta_" prefix (see app/calculate-ta/README.md for column list)
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("my_strategy")
def my_strategy(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Example custom strategy.

    Replace this docstring and logic with your own strategy.
    Reference TA columns like:
      - df["ta_rsi14"]       — RSI(14)
      - df["ta_macd_line"]   — MACD line
      - df["ta_ema20"]       — 20-day EMA
      - df["ta_bband_lower"] — Lower Bollinger Band
      - df["ta_supertrend_direction"] — SuperTrend direction (+1/-1)
      - df["ta_hmm_regime_prob_1"] — HMM regime probabilities
      - df["ta_atr14"]       — 14-day ATR
      - df["ta_cmf"]         — Chaikin Money Flow
      - df["ta_ofi"]         — Order Flow Imbalance
      ... and many more
    """
    # Example: Simple EMA crossover strategy
    entry = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema20"].shift(1) <= df["ta_ema50"].shift(1))
    exit_ = (df["ta_ema20"] < df["ta_ema50"]) & (df["ta_ema20"].shift(1) >= df["ta_ema50"].shift(1))

    return entry.astype(int), exit_.astype(int) * -1

"""Improved EMA Pullback strategy for MKS.L — custom strategies.

Builds on the best-performing built-in (ema_pullback_vol) with:
1. ATR-based trailing stop for dynamic exit
2. GARCH volatility filter to avoid catching falling knives
3. Multi-exit system (ATR trail + RSI + EMA breakdown)
"""

from __future__ import annotations

import pandas as pd

from framework.extensions import register_custom


@register_custom("mks_ema_pullback_improved")
def mks_ema_pullback_improved(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """EMA Pullback + Volume + ATR trail + GARCH filter.

    Improvements over ema_pullback_vol:
    - GARCH volatility filter: avoid entries when GARCH vol is rising (falling knife)
    - ATR-based trailing stop: exit when price drops 2.5xATR below recent high
    - Multi-exit: ATR trail OR RSI > 65 OR Close < EMA50

    Entry conditions:
      1. EMA20 > EMA50 > EMA200 (strong uptrend)
      2. Price within 3% of EMA20 (pullback)
      3. RSI 40-55 (healthy dip, not panic)
      4. SuperTrend bullish (trend filter)
      5. Volume rising (>= 80% of 10-day avg)
      6. GARCH vol NOT rising (not a crash)

    Exit conditions (any):
      1. ATR trailing stop: price < 2.5xATR below 5-day high
      2. RSI > 65 (approaching overbought)
      3. EMA50 breakdown (trend broken)
    """
    # Trend filter
    uptrend = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] > df["ta_ema200"])

    # Pullback to EMA20
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03

    # RSI in healthy range
    rsi_ok = (df["ta_rsi14"] >= 40) & (df["ta_rsi14"] <= 55)

    # SuperTrend bullish
    st_bullish = df["ta_supertrend_direction"] == 1

    # Volume confirmation
    avg_vol = df["Volume"].rolling(10).mean()
    vol_rising = df["Volume"] >= avg_vol * 0.8

    # GARCH volatility filter — avoid rising vol (crash/falling knife)
    garch_safe = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)

    # Combine all entry conditions
    entry = (
        uptrend & near_ema20 & rsi_ok & st_bullish & vol_rising & garch_safe
    )

    # ATR-based trailing stop: exit if price < 5-day high - 2.5xATR
    high_5d = df["Close"].rolling(5).max()
    atr_trail = high_5d - 2.5 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    # RSI exit
    rsi_exit = df["ta_rsi14"] > 65

    # EMA breakdown exit
    ema_exit = df["Close"] < df["ta_ema50"]

    # Any exit triggers
    exit_ = atr_exit | rsi_exit | ema_exit

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("mks_ema_pullback_atr_stop")
def mks_ema_pullback_atr_stop(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """EMA Pullback + Volume + ATR stop loss (3xATR).

    Variant with wider ATR stop (3x instead of 2.5x) and RSI-based exit at 70.
    Designed for slightly more volatile pullbacks — gives the trade more room.

    Entry: Same as improved version but WITHOUT GARCH filter
    Exit: ATR 3x trail OR RSI > 70 OR Close < EMA50
    """
    # Trend filter
    uptrend = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] > df["ta_ema200"])

    # Pullback to EMA20
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03

    # RSI in range
    rsi_ok = (df["ta_rsi14"] >= 35) & (df["ta_rsi14"] <= 55)

    # SuperTrend bullish
    st_bullish = df["ta_supertrend_direction"] == 1

    # Volume confirmation
    avg_vol = df["Volume"].rolling(10).mean()
    vol_rising = df["Volume"] >= avg_vol * 0.8

    # Combine entry conditions (no GARCH filter — more trades)
    entry = (
        uptrend & near_ema20 & rsi_ok & st_bullish & vol_rising
    )

    # ATR-based trailing stop: 3xATR (wider)
    high_5d = df["Close"].rolling(5).max()
    atr_trail = high_5d - 3.0 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    # RSI exit (more generous)
    rsi_exit = df["ta_rsi14"] > 70

    # EMA breakdown exit
    ema_exit = df["Close"] < df["ta_ema50"]

    # Any exit triggers
    exit_ = atr_exit | rsi_exit | ema_exit

    return entry.astype(int), exit_.astype(int) * -1


@register_custom("mks_regime_ema")
def mks_regime_ema(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Regime-aware EMA Pullback.

    Uses HMM regime to only trade in bull regime. Combines the best aspects:
    - HMM bull regime confirmation (>60% bull probability)
    - EMA pullback entry with volume
    - ATR-based trailing stop

    This is a hybrid of hmm_regime + ema_pullback_vol — regime-filtered pullbacks.
    """
    # Trend filter
    uptrend = (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_ema50"] > df["ta_ema200"])

    # Pullback to EMA20
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03

    # RSI in range
    rsi_ok = (df["ta_rsi14"] >= 40) & (df["ta_rsi14"] <= 55)

    # SuperTrend bullish
    st_bullish = df["ta_supertrend_direction"] == 1

    # Volume confirmation
    avg_vol = df["Volume"].rolling(10).mean()
    vol_rising = df["Volume"] >= avg_vol * 0.8

    # HMM bull regime (>60% bull probability)
    bull_prob = df["ta_hmm_regime_prob_1"]
    is_bull = bull_prob > 0.60

    # Combine: all conditions including HMM regime
    entry = (
        uptrend & near_ema20 & rsi_ok & st_bullish & vol_rising & is_bull
    )

    # ATR-based trailing stop
    high_5d = df["Close"].rolling(5).max()
    atr_trail = high_5d - 2.5 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    # RSI exit
    rsi_exit = df["ta_rsi14"] > 65

    # EMA breakdown exit
    ema_exit = df["Close"] < df["ta_ema50"]

    # Any exit triggers
    exit_ = atr_exit | rsi_exit | ema_exit

    return entry.astype(int), exit_.astype(int) * -1

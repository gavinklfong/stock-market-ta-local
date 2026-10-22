"""Built-in strategies extracted from backtest_ng.py.

Each strategy is a function: ``signal_<name>(df) -> (entries, exits)``
where both are pandas Series of int (1 = entry, -1 = exit, 0 = neutral).

All strategies reference columns by the ``ta_`` prefix convention used in
the analysis-data CSVs.  They are **ticker-agnostic** — any CSV with the
same columns will work.
"""

from __future__ import annotations

import pandas as pd

# ======================================================================
#  Individual Strategies (from investment_strategy.md)
# ======================================================================


def signal_goldencross(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Golden Cross: EMA20>EMA50>EMA200, MA20 slope>0, SuperTrend+1, RSI>50, MACD>Signal."""
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_ma20_slope"] > 0) &
        (df["ta_supertrend_direction"] == 1) &
        (df["ta_rsi14"] > 50) &
        (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    exit_ = (
        (df["ta_ema20"] < df["ta_ema50"]) |
        (df["ta_supertrend_direction"] == -1) |
        (df["ta_rsi14"] < 45)
    )
    return entry.astype(int), exit_.astype(int) * -1


def signal_emapullback(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """EMA Pullback: EMA20>EMA50>EMA200, price near EMA20, RSI 40-55, SuperTrend+1."""
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        near_ema20 &
        (df["ta_rsi14"] >= 40) &
        (df["ta_rsi14"] <= 55) &
        (df["ta_supertrend_direction"] == 1)
    )
    exit_ = (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 70)
    return entry.astype(int), exit_.astype(int) * -1


def signal_supertrend_plus(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """SuperTrend flip with RSI>50 and MACD>Signal confirmation."""
    direction = df["ta_supertrend_direction"]
    base_flip = (direction == 1) & (direction.shift(1) == -1)
    entry = base_flip & (df["ta_rsi14"] > 50) & (df["ta_macd_line"] > df["ta_macd_signal"])
    exit_ = (direction == -1) & (direction.shift(1) == 1)
    return entry.astype(int), exit_.astype(int) * -1


def signal_donchian(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Donchian Breakout: Close > Donchian Upper, OFI>0, OBV rising."""
    obv_rising = df["ta_obv"] > df["ta_obv"].shift(1)
    entry = (
        (df["Close"] > df["ta_donchian_upper"]) &
        (df["ta_ofi"] > 0) &
        obv_rising
    )
    exit_ = df["Close"] < df["ta_donchian_lower"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_bb_breakout(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Breakout: Close > BB Upper, ATR rising, HV rising, ROC20>0."""
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)
    entry = (
        (df["Close"] > df["ta_bband_upper"]) &
        atr_rising &
        hv_rising &
        (df["ta_roc20"] > 0)
    )
    exit_ = (df["Close"] < df["ta_bband_middle"]) | (df["ta_macd_line"] < df["ta_macd_signal"])
    return entry.astype(int), exit_.astype(int) * -1


def signal_bb_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion: Close <= BB Lower, RSI<30, Williams %R<-80."""
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_rsi_macd_rev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """RSI+MACD Reversal: RSI<30 + MACD bullish cross + histogram rising + CMF>0."""
    macd_cross = (df["ta_macd_line"] > df["ta_macd_signal"]) & (
        df["ta_macd_line"].shift(1) <= df["ta_macd_signal"].shift(1)
    )
    hist_rising = df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(1)
    entry = (
        (df["ta_rsi14"] < 30) &
        macd_cross &
        hist_rising &
        (df["ta_cmf"] > 0)
    )
    exit_ = (df["ta_rsi14"] > 70) | (df["ta_macd_line"] < df["ta_macd_signal"])
    return entry.astype(int), exit_.astype(int) * -1


def signal_institutional(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Institutional: CMF>0, OBV rising, ADL rising, MFI>50, Close>EMA50."""
    obv_rising = df["ta_obv"] > df["ta_obv"].shift(1)
    adl_rising = df["ta_adl"] > df["ta_adl"].shift(1)
    entry = (
        (df["ta_cmf"] > 0) &
        obv_rising &
        adl_rising &
        (df["ta_mfi14"] > 50) &
        (df["Close"] > df["ta_ema50"])
    )
    exit_ = (df["ta_cmf"] < 0) | (df["ta_obv"] < df["ta_obv"].shift(1))
    return entry.astype(int), exit_.astype(int) * -1


def signal_vwap(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """VWAP Trend: Close > VWAP, VWAP rising, RSI>50."""
    vwap_rising = df["ta_vwap"] > df["ta_vwap"].shift(1)
    entry = (
        (df["Close"] > df["ta_vwap"]) &
        vwap_rising &
        (df["ta_rsi14"] > 50)
    )
    exit_ = df["Close"] < df["ta_vwap"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_ofi(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """OFI Momentum: OFI>0.3, OFI rising, CMF>0, SuperTrend+1."""
    entry = (
        (df["ta_ofi"] > 0.3) &
        (df["ta_ofi"] > df["ta_ofi"].shift(1)) &
        (df["ta_cmf"] > 0) &
        (df["ta_supertrend_direction"] == 1)
    )
    exit_ = df["ta_ofi"] < 0
    return entry.astype(int), exit_.astype(int) * -1


def signal_marketstruct(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Market Structure: HH+HL+BOS+Trend, exit on LH or LL."""
    entry = (
        (df["ta_hh"].fillna(0).astype(int) == 1) &
        (df["ta_hl"].fillna(0).astype(int) == 1) &
        (df["ta_trend"].fillna(0).astype(int) == 1) &
        (df["ta_bos"].fillna(0).astype(int) == 1)
    )
    exit_ = (
        (df["ta_lh"].fillna(0).astype(int) == 1) |
        (df["ta_ll"].fillna(0).astype(int) == 1)
    )
    return entry.astype(int), exit_.astype(int) * -1


def signal_bos(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BOS Breakout: BOS=1, Close>Resistance, CMF>0 or OFI>0."""
    entry = (
        (df["ta_bos"].fillna(0).astype(int) == 1) &
        (df["Close"] > df["ta_nearest_resistance"]) &
        ((df["ta_cmf"] > 0) | (df["ta_ofi"] > 0))
    )
    exit_ = df["Close"] < df["ta_nearest_resistance"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_choch(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """CHoCH Reversal: CHoCH=1, RSI rising, MACD bullish cross."""
    rsi_rising = df["ta_rsi14"] > df["ta_rsi14"].shift(1)
    macd_cross = (df["ta_macd_line"] > df["ta_macd_signal"]) & (
        df["ta_macd_line"].shift(1) <= df["ta_macd_signal"].shift(1)
    )
    entry = (
        (df["ta_choch"].fillna(0).astype(int) == 1) &
        rsi_rising &
        macd_cross
    )
    exit_ = (
        (df["ta_ll"].fillna(0).astype(int) == 1) |
        (df["ta_supertrend_direction"] == -1)
    )
    return entry.astype(int), exit_.astype(int) * -1


def signal_volatility_expansion(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Volatility Expansion: ATR+Hvol+GARCH rising, direction from EMA20."""
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)
    garch_rising = df["ta_garch_vol"] > df["ta_garch_vol"].shift(1)
    vol_rising = atr_rising & hv_rising & garch_rising

    entry_long = vol_rising & (df["Close"] > df["ta_ema20"])
    entry_short = vol_rising & (df["Close"] < df["ta_ema20"])
    entry = entry_long
    exit_ = entry_short | (~atr_rising) | (~hv_rising)
    return entry.astype(int), exit_.astype(int) * -1


def signal_hmm_regime(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """HMM Regime: Bull prob>60% + EMA20>EMA50>EMA200."""
    bull_prob = df["ta_hmm_regime_prob_1"]
    entry = (
        (bull_prob > 0.60) &
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"])
    )
    exit_ = df["ta_ema20"] < df["ta_ema50"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_momentum_comp(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Momentum Composite: RSI>55, MACD>Signal, ROC20>0, W%R>-50, CMF>0, EMA20>EMA50."""
    entry = (
        (df["ta_rsi14"] > 55) &
        (df["ta_macd_line"] > df["ta_macd_signal"]) &
        (df["ta_roc20"] > 0) &
        (df["ta_williams_r"] > -50) &
        (df["ta_cmf"] > 0) &
        (df["ta_ema20"] > df["ta_ema50"])
    )
    exit_ = (df["ta_rsi14"] < 50) & (df["ta_macd_line"] < df["ta_macd_signal"])
    return entry.astype(int), exit_.astype(int) * -1


def signal_highprob_multi(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """High-Prob Multi: Full checklist — EMA, RSI, MACD, CMF, OFI, BOS, HMM."""
    bull_prob = df["ta_hmm_regime_prob_1"]
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_rsi14"] > 55) &
        (df["ta_macd_line"] > df["ta_macd_signal"]) &
        (df["ta_cmf"] > 0) &
        (df["ta_ofi"] > 0) &
        (df["ta_bos"].fillna(0).astype(int) == 1) &
        (bull_prob > 0.60)
    )
    exit_ = (
        (df["ta_supertrend_direction"] == -1) |
        (df["ta_rsi14"] < 50) |
        (df["Close"] < df["ta_ema50"])
    )
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  Combination Strategies
# =====================================================================


def signal_trend_momentum(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Trend+Momentum: Golden Cross AND Momentum Composite conditions must both hold."""
    gc = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_ma20_slope"] > 0) &
        (df["ta_supertrend_direction"] == 1) &
        (df["ta_rsi14"] > 50) &
        (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    mom = (
        (df["ta_rsi14"] > 55) &
        (df["ta_macd_line"] > df["ta_macd_signal"]) &
        (df["ta_roc20"] > 0) &
        (df["ta_williams_r"] > -50) &
        (df["ta_cmf"] > 0) &
        (df["ta_ema20"] > df["ta_ema50"])
    )
    entry = gc & mom
    exit_ = (df["ta_ema20"] < df["ta_ema50"]) | (df["ta_rsi14"] < 50)
    return entry.astype(int), exit_.astype(int) * -1


def signal_vol_structure(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Vol+Structure: BB Breakout signals AND bullish structure confirmation."""
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)
    bb_bo = (
        (df["Close"] > df["ta_bband_upper"]) &
        atr_rising &
        hv_rising &
        (df["ta_roc20"] > 0)
    )
    struct = (
        (df["ta_hh"].fillna(0).astype(int) == 1) |
        (df["ta_hl"].fillna(0).astype(int) == 1)
    )
    entry = bb_bo & struct
    exit_ = (df["Close"] < df["ta_bband_middle"]) | (df["ta_ll"].fillna(0).astype(int) == 1)
    return entry.astype(int), exit_.astype(int) * -1


def signal_score80(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Signal Scoring 80+: Weighted score >= 80 (trend 30 + mom 25 + vol 20 + struct 15 + regime 10)."""
    trend_score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int) * 10 +
        (df["ta_ema50"] > df["ta_ema200"]).astype(int) * 10 +
        (df["ta_supertrend_direction"] == 1).astype(int) * 10
    )
    mom_score = (
        (df["ta_rsi14"] > 55).astype(int) * 8 +
        (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int) * 8 +
        (df["ta_roc20"] > 0).astype(int) * 5 +
        (df["ta_williams_r"] > -50).astype(int) * 4
    )
    vol_score = (
        (df["ta_cmf"] > 0).astype(int) * 10 +
        (df["ta_ofi"] > 0).astype(int) * 10
    )
    struct_score = (
        (df["ta_bos"].fillna(0).astype(int) == 1).astype(int) * 10 +
        ((df["ta_hh"].fillna(0).astype(int) == 1) | (df["ta_hl"].fillna(0).astype(int) == 1)).astype(int) * 5
    )
    regime_score = (df["ta_hmm_regime_prob_1"] > 0.60).astype(int) * 10
    total_score = trend_score + mom_score + vol_score + struct_score + regime_score
    entry = total_score >= 80
    exit_ = total_score < 60
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  Improved Strategies (optimized from baseline analysis)
# =====================================================================


def signal_bb_meanrev_upper(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion: Entry = BB Lower + RSI<30 + W%R<-80, Exit = BB Upper."""
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = df["Close"] >= df["ta_bband_upper"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_bb_meanrev_atr(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion: Entry = BB Lower + RSI<35, Exit = BB Middle OR 4xATR trail."""
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35)
    )
    highest_close = df["Close"].rolling(5).max()
    atr_stop = highest_close - 4 * df["ta_atr14"]
    stop_hit = df["Close"] < atr_stop
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    exit_ = stop_hit | bb_middle_exit
    return entry.astype(int), exit_.astype(int) * -1


def signal_vol_filtered_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion filtered by low GARCH vol (avoid catching falling knives)."""
    garch_not_rising = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_not_rising
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_regime_adaptive(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Regime-adaptive: Bull regime → trend-following; Bear regime → mean-reversion."""
    bull_prob = df["ta_hmm_regime_prob_0"]
    bear_prob = df["ta_hmm_regime_prob_1"]
    neutral_prob = df["ta_hmm_regime_prob_2"]
    bull_entry = (
        (bull_prob >= bear_prob) &
        (bull_prob >= neutral_prob) &
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_rsi14"] > 50) &
        (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    bear_entry = (
        (bear_prob >= bull_prob) &
        (bear_prob >= neutral_prob) &
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    entry = bull_entry | bear_entry
    exit_bull = (df["ta_ema20"] < df["ta_ema50"]) | (df["ta_supertrend_direction"] == -1)
    exit_bear = df["Close"] >= df["ta_bband_middle"]
    exit_ = exit_bull | exit_bear
    return entry.astype(int), exit_.astype(int) * -1


def signal_short_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Short-term mean reversion (5-day hold): RSI<30 + Close<EMA50 + volume conf."""
    vol_conf = (df["ta_cmf"] > -0.1) & (df["ta_ofi"] > -0.05)
    entry = (
        (df["ta_rsi14"] < 30) &
        (df["Close"] < df["ta_ema50"]) &
        vol_conf
    )
    exit_ = df["ta_rsi14"] > 50
    return entry.astype(int), exit_.astype(int) * -1


def signal_vol_breakout_rev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Volume-confirmed breakout reversal: 20-day Donchian + OFI top quartile + MACD."""
    donchian_upper_20 = df["Close"].rolling(20).max()
    donchian_lower_20 = df["Close"].rolling(20).min()
    ofi_top_q = df["ta_ofi"] > df["ta_ofi"].quantile(0.75)
    entry = (
        (df["Close"] > donchian_upper_20) &
        ofi_top_q &
        (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    exit_ = df["Close"] < donchian_lower_20
    return entry.astype(int), exit_.astype(int) * -1


def signal_ema_pullback_vol(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """EMA Pullback + volume: Uptrend + pullback to EMA20 + rising vol + RSI 35-55."""
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03
    vol_rising = df["Volume"] > df["Volume"].rolling(10).mean() * 0.8
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        near_ema20 &
        (df["ta_rsi14"] >= 35) &
        (df["ta_rsi14"] <= 55) &
        (df["ta_supertrend_direction"] == 1) &
        vol_rising
    )
    exit_ = (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 65)
    return entry.astype(int), exit_.astype(int) * -1


def signal_multiscore60(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Multi-factor scoring with relaxed threshold (>= 60 instead of 80)."""
    trend_score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int) * 10 +
        (df["ta_ema50"] > df["ta_ema200"]).astype(int) * 10 +
        (df["ta_supertrend_direction"] == 1).astype(int) * 10
    )
    mom_score = (
        (df["ta_rsi14"] > 50).astype(int) * 8 +
        (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int) * 8 +
        (df["ta_roc20"] > 0).astype(int) * 5 +
        (df["ta_williams_r"] > -50).astype(int) * 4
    )
    vol_score = (
        (df["ta_cmf"] > 0).astype(int) * 10 +
        (df["ta_ofi"] > 0).astype(int) * 10
    )
    struct_score = (
        (df["ta_bos"].fillna(0).astype(int) == 1).astype(int) * 10 +
        ((df["ta_hh"].fillna(0).astype(int) == 1) | (df["ta_hl"].fillna(0).astype(int) == 1)).astype(int) * 5
    )
    bp = df["ta_hmm_regime_prob_1"]
    regime_score = ((bp >= df["ta_hmm_regime_prob_0"]) & (bp >= df["ta_hmm_regime_prob_2"])).astype(int) * 10
    total_score = trend_score + mom_score + vol_score + struct_score + regime_score
    entry = total_score >= 60
    exit_ = total_score < 40
    return entry.astype(int), exit_.astype(int) * -1


def signal_dual_exit_meanrev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion with dual exit: BB Middle + ATR trail."""
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100)
    )
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    three_day_high = df["Close"].rolling(3).max()
    atr_trail = three_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail
    exit_ = bb_middle_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1


def signal_macd_divergence_rev(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """MACD divergence mean reversion: RSI<35 + histogram turning up + CMF turning."""
    hist_turning_up = (
        (df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(2)) &
        (df["ta_macd_histogram"] < df["ta_macd_histogram"].shift(1))
    )
    cmf_turning = df["ta_cmf"] > df["ta_cmf"].shift(1)
    entry = (df["ta_rsi14"] < 35) & hist_turning_up & cmf_turning
    exit_ = (df["ta_rsi14"] > 55) | (df["ta_macd_histogram"] < 0)
    return entry.astype(int), exit_.astype(int) * -1


# =====================================================================
#  NG.L Optimized (Config 1 & 2)
# =====================================================================


def signal_bb_meanrev_optimized(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion Optimized — Config 1: Baseline entry, BB Middle exit.

    Documented (not enforced in vectorbt signal):
      - Profit target: 5% from entry
      - Forced exit: 120 days from entry
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


def signal_bb_meanrev_entry2(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """BB Mean Reversion with Entry2 filter — Config 2: High-quality setups only.

    Entry: BB Lower + RSI<30 + W%R<-80 + BBW>=10% + ATR>=15
    Exit: BB Middle Band
    """
    bb_width = (df["ta_bband_upper"] - df["ta_bband_lower"]) / df["ta_bband_middle"]
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        (bb_width >= 0.10) &
        (df["ta_atr14"] >= 15)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


# ---------------------------------------------------------------------------
# Strategy registry
# ---------------------------------------------------------------------------

STRATEGIES: dict[str, Callable] = {
    # Individual strategies
    "golden_cross": signal_goldencross,
    "ema_pullback": signal_emapullback,
    "supertrend_plus": signal_supertrend_plus,
    "donchian": signal_donchian,
    "bb_breakout": signal_bb_breakout,
    "bb_meanrev": signal_bb_meanrev,
    "rsi_macd_rev": signal_rsi_macd_rev,
    "institutional": signal_institutional,
    "vwap": signal_vwap,
    "ofi": signal_ofi,
    "marketstruct": signal_marketstruct,
    "bos_breakout": signal_bos,
    "choch": signal_choch,
    "vol_expansion": signal_volatility_expansion,
    "hmm_regime": signal_hmm_regime,
    "momentum_comp": signal_momentum_comp,
    "highprob_multi": signal_highprob_multi,
    # Combination strategies
    "trend_momentum": signal_trend_momentum,
    "vol_structure": signal_vol_structure,
    "score80": signal_score80,
    # Improved strategies
    "bb_meanrev_upper": signal_bb_meanrev_upper,
    "bb_meanrev_atr": signal_bb_meanrev_atr,
    "vol_filtered_meanrev": signal_vol_filtered_meanrev,
    "regime_adaptive": signal_regime_adaptive,
    "short_meanrev": signal_short_meanrev,
    "vol_breakout_rev": signal_vol_breakout_rev,
    "ema_pullback_vol": signal_ema_pullback_vol,
    "multiscore60": signal_multiscore60,
    "dual_exit_meanrev": signal_dual_exit_meanrev,
    "macd_divergence_rev": signal_macd_divergence_rev,
    # NG.L Optimized
    "bb_meanrev_optimized": signal_bb_meanrev_optimized,
    "bb_meanrev_entry2": signal_bb_meanrev_entry2,
}

STRATEGY_LABELS: dict[str, str] = {
    "golden_cross": "Golden Cross Trend",
    "ema_pullback": "EMA Pullback",
    "supertrend_plus": "SuperTrend+",
    "donchian": "Donchian Breakout",
    "bb_breakout": "BB Breakout",
    "bb_meanrev": "BB Mean Reversion",
    "rsi_macd_rev": "RSI+MACD Reversal",
    "institutional": "Institutional Accum",
    "vwap": "VWAP Trend",
    "ofi": "OFI Momentum",
    "marketstruct": "Market Structure",
    "bos_breakout": "BOS Breakout",
    "choch": "CHoCH Reversal",
    "vol_expansion": "Volatility Expansion",
    "hmm_regime": "HMM Regime",
    "momentum_comp": "Momentum Composite",
    "highprob_multi": "High-Prob Multi-Factor",
    "trend_momentum": "Trend+Momentum Combo",
    "vol_structure": "Vol+Structure Combo",
    "score80": "Score 80+",
    "bb_meanrev_upper": "BB MeanRev (Upper Exit)",
    "bb_meanrev_atr": "BB MeanRev (ATR Trail)",
    "vol_filtered_meanrev": "Vol-Filtered MeanRev",
    "regime_adaptive": "Regime-Adaptive",
    "short_meanrev": "Short-Term MeanRev",
    "vol_breakout_rev": "Vol Breakout Rev",
    "ema_pullback_vol": "EMA Pullback + Vol",
    "multiscore60": "MultiScore 60+",
    "dual_exit_meanrev": "Dual-Exit MeanRev",
    "macd_divergence_rev": "MACD Div Rev",
    "bb_meanrev_optimized": "BB MeanRev Opt. (Config 1)",
    "bb_meanrev_entry2": "BB MeanRev Entry2 (Config 2)",
}

STRATEGY_GROUPS: dict[str, list[str]] = {
    "Individual": [
        "golden_cross", "ema_pullback", "supertrend_plus", "donchian",
        "bb_breakout", "bb_meanrev", "rsi_macd_rev", "institutional",
        "vwap", "ofi", "marketstruct", "bos_breakout", "choch",
        "vol_expansion", "hmm_regime", "momentum_comp", "highprob_multi",
    ],
    "Combinations": [
        "trend_momentum", "vol_structure", "score80",
    ],
    "Improved": [
        "bb_meanrev_upper", "bb_meanrev_atr", "vol_filtered_meanrev",
        "regime_adaptive", "short_meanrev", "vol_breakout_rev",
        "ema_pullback_vol", "multiscore60", "dual_exit_meanrev",
        "macd_divergence_rev",
    ],
    "NG.L Optimized": [
        "bb_meanrev_optimized", "bb_meanrev_entry2",
    ],
}

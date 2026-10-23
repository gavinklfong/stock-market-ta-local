"""
NG.L Backtest - Multi-strategy evaluation with vectorbt.

Strategies tested on data/analysis-data/NG.L.csv (OHLCV + all TA + P/E):

  --- Individual Strategies (from investment_strategy.md) ---
  1. GoldenCross    - EMA20>EMA50>EMA200, MA20 slope>0, SuperTrend+1, RSI>50, MACD>Signal
  2. EMAPullback    - EMA20>EMA50>EMA200, price near EMA20, RSI 40-55, SuperTrend+1
  3. SuperTrend+    - SuperTrend flip with RSI>50 and MACD>Signal filter
  4. Donchian       - Close > Donchian Upper, OFI>0, OBV rising
  5. BBBreakout     - Close > BB Upper, ATR rising, HV rising, ROC20>0
  6. BBMeanRev      - Close <= BB Lower, RSI<30, Williams %R<-80
  7. RSI_MACD_Rev   - RSI<30 + MACD bullish cross + hist rising + CMF>0
  8. Institutional  - CMF>0, OBV rising, ADL rising, MFI>50, Close>EMA50
  9. VWAPTrend      - Close > VWAP, VWAP rising, RSI>50
 10. OFIMomentum    - OFI>0.3, OFI rising, CMF>0, SuperTrend+1
 11. MarketStruct   - HH+HL+BOS+Trend1, exit on LH or LL
 12. BOSBreakout    - BOS=1, Close>Resistance, CMF>0 or OFI>0
 13. CHoCHRev       - CHoCH=1, RSI rising, MACD bullish cross
 14. VolExp         - ATR+Hvol+GARCH rising, direction from EMA20
 15. HMMRegime      - Bull prob>60% + EMA20>EMA50>EMA200
 16. MomentumComp   - RSI>55, MACD>Signal, ROC20>0, W%R>-50, CMF>0, EMA20>EMA50
 17. HighProbMulti  - Full checklist: EMA, RSI, MACD, CMF, OFI, BOS, HMM

  --- Combinations ---
 18. TrendMomentum  - Golden Cross + Momentum Composite (both confirm)
 19. VolStructure   - BB Breakout + Market Structure (breakout with structure)
 20. Score80        - Signal scoring: trend 30% + mom 25% + vol 20% + struct 15% + regime 10%

   --- Improved Strategies (baseline optimizations) ---
 21. BBMeanRevUpper - BB MeanRev with Upper Band exit (not middle)
 22. BBMeanRevATR   - BB MeanRev with 4xATR trailing stop approximation
 23. VolFilteredMR  - BB MeanRev filtered by low GARCH vol
 24. RegimeAdapt    - HMM regime: bull=trend, bear=meanrev
 25. ShortMeanRev   - 5-day mean reversion (RSI<30 + EMA50 + vol)
 26. VolBreakoutRev - 20-day Donchian breakout + OFI + MACD
 27. EMAPullbackVol - EMA pullback with volume confirmation
 28. MultiScore60   - Relaxed scoring (>=60 instead of 80)
 29. DualExitMR     - BB MeanRev with BB Mid + ATR trail dual exit
 30. MACDDivRev     - MACD histogram turning up + RSI<35 + CMF rising

   --- NG.L Optimized (Config 1 & 2) ---
 31. BBMeanRevOpt   - Baseline entry + 5%PT + BB Mid exit + 120d forced
                       (16t, 93.8% WR, +210.7%, PF 7.92)
 32. BBMeanRevEntry2 - BBW>=10%+ATR>=15 filter + same exits
                       (9t, 100% WR, +175.8%, PF INF)

Outputs:
  - Console: per-strategy metrics + comparison table
  - app/backtest/quantstats/{strategy}.html - individual tearsheets
  - app/backtest/quantstats/comparison.html - multi-strategy comparison
  - app/backtest/equity_curves.html - Plotly equity curve plots
  - app/backtest/backtest_results.csv - raw comparison table

Usage:
  python app/backtest/backtest_ng.py              # run all strategies
  python app/backtest/backtest_ng.py --strategy supertrend  # single strategy
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import quantstats as qs
import vectorbt as vbt
from vectorbt.portfolio.enums import SizeType

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent  # stock-market-ta-local
DATA_PATH = ROOT / "data" / "analysis-data" / "NG.L.csv"
CUTOFF_DATE = pd.Timestamp("2016-10-15")  # ~10 years


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load analysis-data CSV (OHLCV + TA + P/E) and return a clean DataFrame."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    df.index = df["Date"]

    # Filter to last 10 years
    df = df[df["Date"] >= CUTOFF_DATE].reset_index(drop=True)
    df.index = df["Date"]
    return df


# ---------------------------------------------------------------------------
# Strategy signal generators (from investment_strategy.md)
# ---------------------------------------------------------------------------

# --- 1. Golden Cross Trend Following ---

def signal_goldencross(df):
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


# --- 2. EMA Pullback Continuation ---

def signal_emapullback(df):
    """EMA Pullback: EMA20>EMA50>EMA200, price near EMA20, RSI 40-55, SuperTrend+1."""
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03  # within 3%
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (near_ema20) &
        (df["ta_rsi14"] >= 40) &
        (df["ta_rsi14"] <= 55) &
        (df["ta_supertrend_direction"] == 1)
    )
    exit_ = (
        (df["Close"] < df["ta_ema50"]) |
        (df["ta_rsi14"] > 70)
    )
    return entry.astype(int), exit_.astype(int) * -1


# --- 3. SuperTrend+ (Enhanced) ---

def signal_supertrend_plus(df):
    """SuperTrend flip with RSI>50 and MACD>Signal confirmation."""
    direction = df["ta_supertrend_direction"]
    base_flip = (direction == 1) & (direction.shift(1) == -1)
    entry = base_flip & (df["ta_rsi14"] > 50) & (df["ta_macd_line"] > df["ta_macd_signal"])
    exit_ = (direction == -1) & (direction.shift(1) == 1)
    return entry.astype(int), exit_.astype(int) * -1


# --- 4. Donchian Breakout ---

def signal_donchian(df):
    """Donchian Breakout: Close > Donchian Upper, OFI>0, OBV rising."""
    obv = df["ta_obv"]
    obv_rising = obv > obv.shift(1)
    entry = (
        (df["Close"] > df["ta_donchian_upper"]) &
        (df["ta_ofi"] > 0) &
        (obv_rising)
    )
    exit_ = df["Close"] < df["ta_donchian_lower"]
    return entry.astype(int), exit_.astype(int) * -1


# --- 5. Bollinger Band Breakout ---

def signal_bb_breakout(df):
    """BB Breakout: Close > BB Upper, ATR rising, HV rising, ROC20>0."""
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)
    entry = (
        (df["Close"] > df["ta_bband_upper"]) &
        (atr_rising) &
        (hv_rising) &
        (df["ta_roc20"] > 0)
    )
    exit_ = (df["Close"] < df["ta_bband_middle"]) | (df["ta_macd_line"] < df["ta_macd_signal"])
    return entry.astype(int), exit_.astype(int) * -1


# --- 6. Bollinger Mean Reversion ---

def signal_bb_meanrev(df):
    """BB Mean Reversion: Close <= BB Lower, RSI<30, Williams %R<-80."""
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


# --- 7. RSI + MACD Reversal ---

def signal_rsi_macd_rev(df):
    """RSI+MACD Reversal: RSI<30 + MACD bullish cross + histogram rising + CMF>0."""
    macd_cross = (df["ta_macd_line"] > df["ta_macd_signal"]) & (df["ta_macd_line"].shift(1) <= df["ta_macd_signal"].shift(1))
    hist_rising = df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(1)
    entry = (
        (df["ta_rsi14"] < 30) &
        (macd_cross) &
        (hist_rising) &
        (df["ta_cmf"] > 0)
    )
    exit_ = (df["ta_rsi14"] > 70) | (df["ta_macd_line"] < df["ta_macd_signal"])
    return entry.astype(int), exit_.astype(int) * -1


# --- 8. Institutional Accumulation ---

def signal_institutional(df):
    """Institutional: CMF>0, OBV rising, ADL rising, MFI>50, Close>EMA50."""
    obv_rising = df["ta_obv"] > df["ta_obv"].shift(1)
    adl_rising = df["ta_adl"] > df["ta_adl"].shift(1)
    entry = (
        (df["ta_cmf"] > 0) &
        (obv_rising) &
        (adl_rising) &
        (df["ta_mfi14"] > 50) &
        (df["Close"] > df["ta_ema50"])
    )
    exit_ = (df["ta_cmf"] < 0) | (df["ta_obv"] < df["ta_obv"].shift(1))
    return entry.astype(int), exit_.astype(int) * -1


# --- 9. VWAP Trend ---

def signal_vwap(df):
    """VWAP Trend: Close > VWAP, VWAP rising, RSI>50."""
    vwap_rising = df["ta_vwap"] > df["ta_vwap"].shift(1)
    entry = (
        (df["Close"] > df["ta_vwap"]) &
        (vwap_rising) &
        (df["ta_rsi14"] > 50)
    )
    exit_ = df["Close"] < df["ta_vwap"]
    return entry.astype(int), exit_.astype(int) * -1


# --- 10. OFI Momentum ---

def signal_ofi(df):
    """OFI Momentum: OFI>0.3, OFI rising, CMF>0, SuperTrend+1."""
    entry = (
        (df["ta_ofi"] > 0.3) &
        (df["ta_ofi"] > df["ta_ofi"].shift(1)) &
        (df["ta_cmf"] > 0) &
        (df["ta_supertrend_direction"] == 1)
    )
    exit_ = df["ta_ofi"] < 0
    return entry.astype(int), exit_.astype(int) * -1


# --- 11. Market Structure Trend ---

def signal_marketstruct(df):
    """Market Structure: HH+HL+BOS+Trend, exit on LH or LL."""
    entry = (
        ((df["ta_hh"].fillna(0).astype(int)) == 1) &
        ((df["ta_hl"].fillna(0).astype(int)) == 1) &
        ((df["ta_trend"].fillna(0).astype(int)) == 1) &
        ((df["ta_bos"].fillna(0).astype(int)) == 1)
    )
    exit_ = (
        ((df["ta_lh"].fillna(0).astype(int)) == 1) |
        ((df["ta_ll"].fillna(0).astype(int)) == 1)
    )
    return entry.astype(int), exit_.astype(int) * -1


# --- 12. BOS Breakout ---

def signal_bos(df):
    """BOS Breakout: BOS=1, Close>Resistance, CMF>0 or OFI>0."""
    entry = (
        ((df["ta_bos"].fillna(0).astype(int)) == 1) &
        (df["Close"] > df["ta_nearest_resistance"]) &
        ((df["ta_cmf"] > 0) | (df["ta_ofi"] > 0))
    )
    exit_ = df["Close"] < df["ta_nearest_resistance"]
    return entry.astype(int), exit_.astype(int) * -1


# --- 13. CHoCH Reversal ---

def signal_choch(df):
    """CHoCH Reversal: CHoCH=1, RSI rising, MACD bullish cross."""
    rsi_rising = df["ta_rsi14"] > df["ta_rsi14"].shift(1)
    macd_cross = (df["ta_macd_line"] > df["ta_macd_signal"]) & (df["ta_macd_line"].shift(1) <= df["ta_macd_signal"].shift(1))
    entry = (
        ((df["ta_choch"].fillna(0).astype(int)) == 1) &
        (rsi_rising) &
        (macd_cross)
    )
    exit_ = (
        ((df["ta_ll"].fillna(0).astype(int)) == 1) |
        (df["ta_supertrend_direction"] == -1)
    )
    return entry.astype(int), exit_.astype(int) * -1


# --- 14. Volatility Expansion ---

def signal_volatility_expansion(df):
    """Volatility Expansion: ATR+Hvol+GARCH rising, direction from EMA20."""
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)
    garch_rising = df["ta_garch_vol"] > df["ta_garch_vol"].shift(1)
    vol_rising = atr_rising & hv_rising & garch_rising

    entry_long = vol_rising & (df["Close"] > df["ta_ema20"])
    entry_short = vol_rising & (df["Close"] < df["ta_ema20"])

    entry = entry_long
    exit_ = entry_short  # exit long when direction flips (simplified)

    # Also exit when volatility contracts
    vol_contract = (~atr_rising) | (~hv_rising)
    exit_ = exit_ | vol_contract

    return entry.astype(int), exit_.astype(int) * -1


# --- 15. HMM Regime Adaptive ---

def signal_hmm_regime(df):
    """HMM Regime: Bull prob>60% + EMA20>EMA50>EMA200."""
    bull_prob = df["ta_hmm_regime_prob_1"]  # regime 1 = bull
    entry = (
        (bull_prob > 0.60) &
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"])
    )
    exit_ = df["ta_ema20"] < df["ta_ema50"]
    return entry.astype(int), exit_.astype(int) * -1


# --- 16. Momentum Composite ---

def signal_momentum_comp(df):
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


# --- 17. High-Probability Multi-Factor ---

def signal_highprob_multi(df):
    """High-Prob Multi: EMA20>EMA50>EMA200, RSI>55, MACD>Signal, CMF>0, OFI>0, BOS=1, Bull HMM>60%."""
    bull_prob = df["ta_hmm_regime_prob_1"]
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_rsi14"] > 55) &
        (df["ta_macd_line"] > df["ta_macd_signal"]) &
        (df["ta_cmf"] > 0) &
        (df["ta_ofi"] > 0) &
        ((df["ta_bos"].fillna(0).astype(int)) == 1) &
        (bull_prob > 0.60)
    )
    exit_ = (
        (df["ta_supertrend_direction"] == -1) |
        (df["ta_rsi14"] < 50) |
        (df["Close"] < df["ta_ema50"])
    )
    return entry.astype(int), exit_.astype(int) * -1


# ---------------------------------------------------------------------------
# Combination strategies
# ---------------------------------------------------------------------------

# --- 18. Trend + Momentum (Golden Cross AND Momentum Composite) ---

def signal_trend_momentum(df):
    """Trend+Momentum: Both Golden Cross conditions AND Momentum Composite conditions must hold."""
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


# --- 19. Volatility + Structure (BB Breakout AND Market Structure) ---

def signal_vol_structure(df):
    """Vol+Structure: BB Breakout signals AND bullish structure confirmation."""
    atr_rising = df["ta_atr14"] > df["ta_atr14"].shift(1)
    hv_rising = df["ta_hvol20"] > df["ta_hvol20"].shift(1)
    bb_bo = (
        (df["Close"] > df["ta_bband_upper"]) &
        (atr_rising) &
        (hv_rising) &
        (df["ta_roc20"] > 0)
    )
    struct = (
        ((df["ta_hh"].fillna(0).astype(int)) == 1) |
        ((df["ta_hl"].fillna(0).astype(int)) == 1)
    )
    entry = bb_bo & struct
    exit_ = (df["Close"] < df["ta_bband_middle"]) | ((df["ta_ll"].fillna(0).astype(int)) == 1)
    return entry.astype(int), exit_.astype(int) * -1


# --- 20. Score 80+ (Weighted Signal Scoring) ---

def signal_score80(df):
    """Signal Scoring 80+: Weighted score >= 80 (trend 30% + mom 25% + vol 20% + struct 15% + regime 10%)."""
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
        ((df["ta_bos"].fillna(0).astype(int)) == 1).astype(int) * 10 +
        (((df["ta_hh"].fillna(0).astype(int)) == 1) | ((df["ta_hl"].fillna(0).astype(int)) == 1)).astype(int) * 5
    )
    regime_score = (df["ta_hmm_regime_prob_1"] > 0.60).astype(int) * 10

    total_score = trend_score + mom_score + vol_score + struct_score + regime_score
    entry = total_score >= 80
    exit_ = total_score < 60
    return entry.astype(int), exit_.astype(int) * -1


# ---------------------------------------------------------------------------
# NEW IMPROVED STRATEGIES (optimized based on baseline analysis)
# ---------------------------------------------------------------------------

# --- 21. BB Mean Reversion with Upper Band Exit ---

def signal_bb_meanrev_upper(df):
    """BB Mean Reversion: Entry = BB Lower + RSI<30 + W%R<-80, Exit = BB Upper (not middle).
    Baseline: BB Mean Rev hit BB Middle 100% of time but slowly. BB Upper hit 94.9% of time.
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = df["Close"] >= df["ta_bband_upper"]  # Exit at UPPER band instead of middle
    return entry.astype(int), exit_.astype(int) * -1


# --- 22. BB Mean Reversion with ATR Trailing Stop ---

def signal_bb_meanrev_atr(df):
    """BB Mean Reversion: Entry = BB Lower + RSI<35, Exit = BB Middle OR 4xATR trailing stop from peak.
    Uses a 4xATR trailing stop to capture larger reversions while limiting downside.
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35)
    )
    # Compute trailing stop: 4xATR below highest close since entry
    # Vectorbt doesn't support custom trailing stops natively, so we approximate:
    # Exit when price drops 4xATR below its recent high (5-day lookback)
    highest_close = df["Close"].rolling(5).max()
    atr_stop = highest_close - 4 * df["ta_atr14"]
    stop_hit = df["Close"] < atr_stop

    # Exit when price reaches BB middle (quick exit) or ATR stop hits
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    exit_ = stop_hit | bb_middle_exit
    return entry.astype(int), exit_.astype(int) * -1


# --- 23. Vol-Filtered Mean Reversion ---

def signal_vol_filtered_meanrev(df):
    """BB Mean Reversion filtered by low GARCH volatility (avoid catching falling knives).
    Entry: BB Lower + RSI<35 + CCI<-100 + GARCH not rising (vol contraction = base forming).
    Exit: BB Middle.
    """
    garch_not_rising = df["ta_garch_vol"] <= df["ta_garch_vol"].shift(1)
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100) &
        garch_not_rising
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


# --- 24. Regime-Adaptive Strategy ---

def signal_regime_adaptive(df):
    """Regime-adaptive strategy:
    - Bull regime (regime 0): Trend-following (Golden Cross + RSI>50)
    - Bear regime (regime 1): Mean reversion (BB Lower + RSI<30)
    - Neutral regime: Hold cash (no signals)
    Uses HMM regime to flip between strategies.
    """
    bull_prob = df["ta_hmm_regime_prob_0"]  # Regime 0 = slightly bullish
    bear_prob = df["ta_hmm_regime_prob_1"]  # Regime 1 = bearish
    neutral_prob = df["ta_hmm_regime_prob_2"]  # Regime 2 = neutral

    # Bull trend-following signals
    bull_entry = (
        (bull_prob >= bear_prob) &
        (bull_prob >= neutral_prob) &
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        (df["ta_rsi14"] > 50) &
        (df["ta_macd_line"] > df["ta_macd_signal"])
    )

    # Bear mean-reversion signals
    bear_entry = (
        (bear_prob >= bull_prob) &
        (bear_prob >= neutral_prob) &
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )

    entry = bull_entry | bear_entry
    # Exit bull when golden cross breaks, exit bear when BB middle hit
    exit_bull = (df["ta_ema20"] < df["ta_ema50"]) | (df["ta_supertrend_direction"] == -1)
    exit_bear = df["Close"] >= df["ta_bband_middle"]
    exit_ = exit_bull | exit_bear
    return entry.astype(int), exit_.astype(int) * -1


# --- 25. Short-Term Mean Reversion (5-day hold) ---

def signal_short_meanrev(df):
    """Short-term mean reversion optimized for 5-day holding period.
    Entry: RSI<30 + Close below EMA50 + volume confirmation.
    Exit: RSI>50 or 5-day time stop (use simple RSI exit as proxy).
    Designed for NG.L's mean-reverting short-term behavior.
    """
    vol_confirmation = (df["ta_cmf"] > -0.1) & (df["ta_ofi"] > -0.05)  # Loose volume filter
    entry = (
        (df["ta_rsi14"] < 30) &
        (df["Close"] < df["ta_ema50"]) &
        vol_confirmation
    )
    # Exit: RSI recovers to bullish zone
    exit_ = df["ta_rsi14"] > 50
    return entry.astype(int), exit_.astype(int) * -1


# --- 26. Volume-Confirmed Breakout Reversal ---

def signal_vol_breakout_rev(df):
    """Volume-confirmed breakout reversal:
    Entry: Donchian breakout (Close > Upper) + OFI surge (top quartile) + MACD>Signal.
    Since Close>Donchian Upper is 0% in baseline, use 20-day instead of full lookback.
    Exit: Close < 20-day Donchian Lower.
    """
    # Use rolling 20-day Donchian (shorter lookback)
    donchian_upper_20 = df["Close"].rolling(20).max()
    donchian_lower_20 = df["Close"].rolling(20).min()
    ofi_top_quartile = df["ta_ofi"] > df["ta_ofi"].quantile(0.75)

    entry = (
        (df["Close"] > donchian_upper_20) &
        (ofi_top_quartile) &
        (df["ta_macd_line"] > df["ta_macd_signal"])
    )
    exit_ = df["Close"] < donchian_lower_20
    return entry.astype(int), exit_.astype(int) * -1


# --- 27. EMA Pullback with Volume Confirmation ---

def signal_ema_pullback_vol(df):
    """EMA Pullback with volume confirmation:
    Entry: Uptrend (EMA20>EMA50>EMA200) + Price pullback to EMA20 + Rising volume + RSI 35-55.
    Exit: Close below EMA50 or RSI>65.
    Combines the best of EMA pullback with volume filter to avoid false pullbacks.
    """
    near_ema20 = (df["Close"] - df["ta_ema20"]).abs() / df["Close"] < 0.03
    volume_rising = df["Volume"] > df["Volume"].rolling(10).mean() * 0.8  # Volume not collapsing
    entry = (
        (df["ta_ema20"] > df["ta_ema50"]) &
        (df["ta_ema50"] > df["ta_ema200"]) &
        near_ema20 &
        (df["ta_rsi14"] >= 35) &
        (df["ta_rsi14"] <= 55) &
        (df["ta_supertrend_direction"] == 1) &
        volume_rising
    )
    exit_ = (df["Close"] < df["ta_ema50"]) | (df["ta_rsi14"] > 65)
    return entry.astype(int), exit_.astype(int) * -1


# --- 28. Multi-Indicator Score (Relaxed 60+) ---

def signal_multiscore60(df):
    """Multi-factor scoring with relaxed threshold (>= 60 instead of 80).
    Trend (0-30): EMA20>EMA50(10), EMA50>EMA200(10), SuperTrend+1(10)
    Momentum (0-25): RSI>50(8), MACD>Signal(8), ROC20>0(5), W%R>-50(4)
    Volume (0-20): CMF>0(10), OFI>0(10)
    Structure (0-15): BOS=1(10), HH or HL(5)
    Regime (0-10): Bull prob highest (10)
    Exit: Score drops below 40.
    More signals than Score80 while maintaining quality.
    """
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
        ((df["ta_bos"].fillna(0).astype(int)) == 1).astype(int) * 10 +
        (((df["ta_hh"].fillna(0).astype(int)) == 1) | ((df["ta_hl"].fillna(0).astype(int)) == 1)).astype(int) * 5
    )
    bull_prob = df["ta_hmm_regime_prob_1"]
    regime_score = (bull_prob >= df["ta_hmm_regime_prob_0"]) & (bull_prob >= df["ta_hmm_regime_prob_2"])
    regime_score = regime_score.astype(int) * 10

    total_score = trend_score + mom_score + vol_score + struct_score + regime_score
    entry = total_score >= 60
    exit_ = total_score < 40
    return entry.astype(int), exit_.astype(int) * -1


# --- 29. Dual-Exit Mean Reversion ---

def signal_dual_exit_meanrev(df):
    """BB Mean Reversion with dual exit strategy:
    - Partial profit at BB Middle (mark as exit for simplicity)
    - ATR-based trailing stop to capture full reversal
    Entry: BB Lower + RSI<35 + CCI<-100.
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 35) &
        (df["ta_cci"] < -100)
    )
    # Dual exit: quick profit at BB middle, or trail with ATR
    bb_middle_exit = df["Close"] >= df["ta_bband_middle"]
    # ATR trailing: exit if price drops 3xATR from 3-day high
    three_day_high = df["Close"].rolling(3).max()
    atr_trail = three_day_high - 3 * df["ta_atr14"]
    atr_exit = df["Close"] < atr_trail

    exit_ = bb_middle_exit | atr_exit
    return entry.astype(int), exit_.astype(int) * -1


# --- 30. MACD Divergence Mean Reversion ---

def signal_macd_divergence_rev(df):
    """MACD divergence-based mean reversion:
    Entry: RSI<35 + MACD histogram turning up (was falling, now rising) + CMF turning positive.
    Exit: MACD histogram peaks and starts falling, or RSI>55.
    Captures momentum shifts rather than just oversold levels.
    """
    hist_turning_up = (df["ta_macd_histogram"] > df["ta_macd_histogram"].shift(2)) & (df["ta_macd_histogram"] < df["ta_macd_histogram"].shift(1))
    cmf_turning = df["ta_cmf"] > df["ta_cmf"].shift(1)
    entry = (
        (df["ta_rsi14"] < 35) &
        hist_turning_up &
        cmf_turning
    )
    exit_ = (df["ta_rsi14"] > 55) | (df["ta_macd_histogram"] < 0)
    return entry.astype(int), exit_.astype(int) * -1


# ---------------------------------------------------------------------------
# Optimized NG.L Mean-Reversion Strategies
# Derived from extensive backtesting optimization (Oct 2026).
#
# Key findings for NG.L (commodity, range-bound +2.8%, mean-reverting):
#   - ATR trailing kills performance (commodity whipsaws)
#   - BB Lower breach exit hurts (markets dip below BB Lower before bouncing)
#   - BB Middle exit > BB Upper > ATR Trail
#   - 120d forced exit is optimal (gives mean-reversion time, caps rare losses)
#   - Entry2 (BBW≥10% + ATR≥15) selects high-quality setups
#
# Config 1 (Baseline + PT 5% + BB Mid + 120d): 16t, 93.8% WR, +210.7%, PF 7.92
# Config 2 (Entry2 + PT 5% + BB Mid + 120d):   9t,  100% WR, +175.8%, PF INF
# Config 3 (Baseline + PT 5% + BB Mid + 45d):  17t, 82.4% WR, +185.3%, PF 13.20
#
# NOTE: vectorbt `from_signals` only supports simple entry/exit signals.
# Profit target (5%) and forced exit (45d/120d) are documented for manual
# implementation or custom simulation. The BB Middle exit captures most
# profit-target hits (>94% overlap).
# ---------------------------------------------------------------------------


# --- 31. BB Mean Reversion Optimized (Config 1) ---

def signal_bb_meanrev_optimized(df):
    """BB Mean Reversion Optimized — Config 1: Baseline entry with enhanced exits.
    
    Entry: Close <= BB Lower, RSI < 30, Williams %R < -80
    Exit: Close >= BB Middle Band
    
    Documented (not enforced in vectorbt signal):
      - Profit target: 5% from entry (hits in 94% of BB Middle exits)
      - Forced exit: 120 days from entry (caps rare losses)
    
    Backtested: 16 trades, 93.8% WR, +210.7% total return, PF 7.92
    """
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


# --- 32. BB Mean Reversion Entry2 Filter (Config 2) ---

def signal_bb_meanrev_entry2(df):
    """BB Mean Reversion with Entry2 filter — Config 2: High-quality setups only.
    
    Entry: Close <= BB Lower, RSI < 30, Williams %R < -80,
           BB Width >= 10%, ATR >= 15
    Exit: Close >= BB Middle Band
    
    Documented (not enforced in vectorbt signal):
      - Profit target: 5% from entry
      - Forced exit: 120 days from entry
    
    Backtested: 9 trades, 100% WR, +175.8% total return, PF INF
    BBW >= 10% + ATR >= 15 filters out low-quality mean-reversion setups.
    
    NOTE: BB Width is computed as (upper - lower) / middle.
    """
    bb_width = (df["ta_bband_upper"] - df["ta_bband_lower"]) / df["ta_bband_middle"]
    entry = (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80) &
        (bb_width >= 0.10) &  # BB Width >= 10%
        (df["ta_atr14"] >= 15)  # ATR >= 15 (sufficient volatility)
    )
    exit_ = df["Close"] >= df["ta_bband_middle"]
    return entry.astype(int), exit_.astype(int) * -1


# ---------------------------------------------------------------------------
# Strategy registry
# ---------------------------------------------------------------------------
STRATEGIES = {
    # Individual strategies from investment_strategy.md
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
    # Improved strategies (optimized from baseline analysis)
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
    # Optimized NG.L mean-reversion (Config 1 & 2)
    "bb_meanrev_optimized": signal_bb_meanrev_optimized,
    "bb_meanrev_entry2": signal_bb_meanrev_entry2,
}

# Labels for display
STRATEGY_LABELS = {
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
    # Improved strategies
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
    # Optimized NG.L mean-reversion
    "bb_meanrev_optimized": "BB MeanRev Opt. (Config 1)",
    "bb_meanrev_entry2": "BB MeanRev Entry2 (Config 2)",
}

# Group labels for organized output
STRATEGY_GROUPS = {
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


# ---------------------------------------------------------------------------
# Backtest runner
# ---------------------------------------------------------------------------
def run_backtest(
    df: pd.DataFrame,
    strategy_name: str,
    init_cash: float = 100_000,
    commission: float = 0.001,
    slippage: float = 0.0,
    use_trailing_stop: bool = False,
    trailing_pct: float = 0.05,
) -> vbt.Portfolio:
    """Run a single backtest and return a vectorbt Portfolio object.

    If use_trailing_stop is True, exits are overridden with a percentage-based
    trailing stop from the highest close since entry.
    """
    signals = STRATEGIES[strategy_name](df)
    entries, exits = signals

    if use_trailing_stop:
        # Use trailing stop: exit when price drops trailing_pct from highest close
        trailing = vbt.TrailingStopPortfolio.from_signals(
            close=df["Close"],
            entries=entries,
            exits=exits,
            init_cash=init_cash,
            freq="1D",
            slippage=slippage,
            size=1.0,
            size_type=SizeType.Percent,
            fees=commission,
            trailing_pct=trailing_pct,
        )
        return trailing
    else:
        pf = vbt.Portfolio.from_signals(
            close=df["Close"],
            entries=entries,
            exits=exits,
            init_cash=init_cash,
            freq="1D",
            slippage=slippage,
            size=1.0,
            size_type=SizeType.Percent,
            fees=commission,
        )
        return pf


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def print_summary(pf: vbt.Portfolio, name: str, label: str | None = None):
    """Print a formatted summary for one strategy."""
    if label is None:
        label = STRATEGY_LABELS.get(name, name)

    stats_df = pf.stats()
    total_return = stats_df.get("Total Return [%]", 0)
    total_trades = stats_df.get("Total Trades", 0)
    win_rate = stats_df.get("Win Rate [%]", 0)
    profit_factor = stats_df.get("Profit Factor", 0)
    max_dd = stats_df.get("Max Drawdown [%]", 0)
    final_value = pf.final_value()
    avg_drawdown = stats_df.get("Average Drawdown [%]", 0)
    sharpe = stats_df.get("Sharpe Ratio", 0)
    calmar = stats_df.get("Calmar Ratio", 0)

    print(f"\n  {label}")
    print(f"  {'─'*40}")
    print(f"    Total Return:       {total_return:9.2f}%")
    print(f"    Sharpe Ratio:       {sharpe:9.2f}")
    print(f"    Calmar Ratio:       {calmar:9.2f}")
    print(f"    Total Trades:       {total_trades:6d}")
    print(f"    Win Rate:           {win_rate:8.1f}%")
    print(f"    Profit Factor:      {profit_factor:9.3f}")
    print(f"    Max Drawdown:       {max_dd:9.2f}%")
    print(f"    Avg Drawdown:       {avg_drawdown:9.2f}%")
    print(f"    Final Net Value:    GBP {final_value:>12,.0f}")


def print_group_header(group_name: str):
    """Print a group section header."""
    print(f"\n{'═'*60}")
    print(f"  {group_name}")
    print(f"{'═'*60}")


def compare_all(df: pd.DataFrame, strategies: list[str] | None = None):
    """Run all strategies and print a comparison table, grouped by category."""
    if strategies is None:
        strategies = list(STRATEGIES.keys())

    results = []
    for name in strategies:
        print(f"Running strategy: {name} ...")
        pf = run_backtest(df, name)
        print_summary(pf, name)

        stats_df = pf.stats()
        results.append({
            "Strategy": STRATEGY_LABELS.get(name, name),
            "Category": _get_category(name),
            "Total Return (%)": round(stats_df.get("Total Return [%]", 0), 2),
            "Sharpe Ratio": round(stats_df.get("Sharpe Ratio", 0), 2),
            "Calmar Ratio": round(stats_df.get("Calmar Ratio", 0), 2),
            "Total Trades": int(stats_df.get("Total Trades", 0)),
            "Win Rate (%)": round(stats_df.get("Win Rate [%]", 0), 1),
            "Profit Factor": round(stats_df.get("Profit Factor", 0), 3),
            "Max Drawdown (%)": round(stats_df.get("Max Drawdown [%]", 0), 2),
            "Avg Drawdown (%)": round(stats_df.get("Average Drawdown [%]", 0), 2),
            "Final Net Value": round(pf.final_value(), 0),
        })

    table = pd.DataFrame(results).set_index("Strategy")

    # Print grouped comparison
    for group_name in STRATEGY_GROUPS:
        group_keys = [k for k in STRATEGY_GROUPS[group_name] if k in strategies]
        if not group_keys:
            continue
        subset = table.loc[[STRATEGY_LABELS.get(k, k) for k in group_keys]]
        print(f"\n{group_name}:")
        print(subset.to_string())

    # Full comparison
    print(f"\n{'═'*80}")
    print("  FULL COMPARISON (sorted by Total Return)")
    print(f"{'═'*80}")
    sorted_table = table.sort_values("Total Return (%)", ascending=False)
    print(sorted_table.to_string())

    return table


def _get_category(name: str) -> str:
    """Return the category for a strategy name."""
    for group, keys in STRATEGY_GROUPS.items():
        if name in keys:
            return group
    return "Other"


# ---------------------------------------------------------------------------
# Quantstats reports
# ---------------------------------------------------------------------------
def _extract_returns(
    pf: vbt.Portfolio, df: pd.DataFrame
) -> tuple[pd.Series, pd.Series]:
    """Extract strategy daily returns and benchmark (buy-and-hold) returns."""
    strategy_ret = pf.daily_returns().dropna()
    benchmark_ret = df["Close"].pct_change().dropna()
    common_idx = strategy_ret.index.intersection(benchmark_ret.index)
    return strategy_ret.loc[common_idx], benchmark_ret.loc[common_idx]


def generate_quantstats_report(
    pf: vbt.Portfolio, df: pd.DataFrame, name: str
) -> Path:
    """Generate an HTML tearsheet for a single strategy."""
    strategy_ret, benchmark_ret = _extract_returns(pf, df)

    out_path = ROOT / "app" / "backtest" / "quantstats" / f"{name}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    qs.reports.html(
        strategy_ret,
        benchmark=benchmark_ret,
        title=f"NG.L - {STRATEGY_LABELS.get(name, name)}",
        output=str(out_path),
        figsize=(1200, 800),
    )
    print(f"  Tearsheet saved: {out_path}")
    return out_path


def generate_quantstats_comparison(
    df: pd.DataFrame, strategies: list[str] | None = None
) -> Path:
    """Generate a multi-strategy comparison tearsheet (top 10 by return only).

    quantstats has a limited color palette; when too many strategies are
    passed it runs out of colours.  We therefore limit to the top-10
    strategies (sorted by total return) which already gives a useful
    comparison.
    """
    if strategies is None:
        strategies = list(STRATEGIES.keys())

    # Rank strategies by total return
    results: dict[str, float] = {}
    for name in strategies:
        pf = run_backtest(df, name)
        results[name] = pf.total_return()

    ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)
    top = [name for name, _ in ranked[:10]]  # limit to 10

    benchmark_ret = df["Close"].pct_change().dropna()

    returns_df = pd.DataFrame(columns=top, index=benchmark_ret.index)
    for name in top:
        pf = run_backtest(df, name)
        strat_ret, _ = _extract_returns(pf, df)
        returns_df[name] = strat_ret

    out_path = ROOT / "app" / "backtest" / "quantstats" / "comparison.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    qs.reports.html(
        returns_df,
        benchmark=benchmark_ret,
        title="NG.L - Multi-Strategy Comparison (Top 10)",
        output=str(out_path),
        figsize=(1200, 800),
    )
    print(f"  Comparison tearsheet saved: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Drawdown & equity curves
# ---------------------------------------------------------------------------
def plot_comparison(df: pd.DataFrame, strategies: list[str] | None = None):
    """Plot equity curves using plotly directly."""
    if strategies is None:
        strategies = list(STRATEGIES.keys())

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=["Cumulative Returns", "Drawdown"],
    )

    colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]

    for i, name in enumerate(strategies):
        pf = run_backtest(df, name)
        cum_ret = pf.cumulative_returns()
        fig.add_trace(
            go.Scatter(
                x=cum_ret.index, y=cum_ret.values,
                name=STRATEGY_LABELS.get(name, name),
                line=dict(width=1.5, color=colors[i % len(colors)]),
            ),
            row=1, col=1,
        )
        dd = pf.drawdown()
        fig.add_trace(
            go.Scatter(
                x=dd.index, y=dd.values,
                name=f"{STRATEGY_LABELS.get(name, name)} DD",
                line=dict(width=1, color=colors[i % len(colors)]),
                opacity=0.6,
            ),
            row=2, col=1,
        )

    fig.update_layout(
        title="NG.L Strategy Comparison",
        height=800,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )

    out_path = ROOT / "app" / "backtest" / "equity_curves.html"
    fig.write_html(str(out_path))
    print(f"\nEquity curves saved to: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Parse args
    args = sys.argv[1:]
    if "--strategy" in args:
        selected = []
        i = 0
        while i < len(args):
            if args[i] == "--strategy" and i + 1 < len(args):
                i += 1
                # Collect all positional args until next flag
                while i < len(args) and not args[i].startswith("--"):
                    selected.append(args[i])
                    i += 1
            else:
                i += 1
    else:
        selected = None

    # Load data
    print(f"Loading data from {DATA_PATH} ...")
    df = load_data()
    print(f"  {len(df)} rows, {df.index.min().date()} to {df.index.max().date()}")
    print(f"  Close range: GBP{df['Close'].min():.2f} to GBP{df['Close'].max():.2f}")

    # Determine which strategies to run
    if selected:
        invalid = [s for s in selected if s not in STRATEGIES]
        if invalid:
            print(f"Error: unknown strategies: {invalid}")
            print(f"Available: {', '.join(STRATEGIES.keys())}")
            sys.exit(1)
    else:
        selected = list(STRATEGIES.keys())

    # Run backtests and get comparison table
    table = compare_all(df, selected)

    # --- Quantstats tearsheets ---
    print(f"\n{'='*60}")
    print("  Generating Quantstats Tearsheets ...")
    print(f"{'='*60}")

    for name in selected:
        pf = run_backtest(df, name)
        generate_quantstats_report(pf, df, name)

    generate_quantstats_comparison(df, selected)

    # Plot (non-interactive mode - writes HTML)
    plot_comparison(df, selected)

    # Save raw results
    table_path = ROOT / "app" / "backtest" / "backtest_results.csv"
    table.to_csv(table_path)
    print(f"\nResults saved to: {table_path}")


if __name__ == "__main__":
    main()



import os
import math
import pandas as pd

from common import main, read_yfinance_csv


def compute_ema(values, period):
    """Incremental EMA: returns a list where each element is the EMA up to that index."""
    k = 2.0 / (period + 1)
    result = [None] * len(values)
    if len(values) < period:
        return result
    # Seed with SMA of first `period` values
    ema = sum(float(v) for v in values[:period]) / period
    for i in range(period - 1, len(values)):
        result[i] = ema
        if i < len(values) - 1:
            ema = float(values[i + 1]) * k + ema * (1 - k)
    return result


def compute_atr(highs, lows, closes, period=14):
    """Compute Wilder's ATR. Returns list aligned with input."""
    if len(highs) < period + 1:
        return [None] * len(highs)

    true_ranges = [None] * len(highs)
    for i in range(len(highs)):
        if i == 0:
            true_ranges[i] = highs[i] - lows[i]
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges[i] = tr

    atr_values = [None] * len(highs)
    # Seed ATR at index `period` using first `period` true ranges (indices 0..period-1)
    initial_atr = sum(true_ranges[i] for i in range(period)) / period
    atr_values[period] = initial_atr

    k = 2.0 / (period + 1)
    for i in range(period + 1, len(highs)):
        if true_ranges[i] is not None:
            prev_atr = atr_values[i - 1]
            if prev_atr is not None:
                atr_values[i] = true_ranges[i] * k + prev_atr * (1 - k)

    return atr_values


def compute_ma(closes, period):
    """Compute Simple Moving Average (SMA) for each candle."""
    ma_values = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1: i + 1]
        ma_values[i] = sum(window) / period
    return ma_values


def compute_ma_slope(closes, period, lookback=10):
    """Compute slope of MA over `lookback` periods.

    slope = (MA_at_current - MA_at_current_lookback) / lookback
    """
    ma_values = compute_ma(closes, period)
    slope_values = [None] * len(closes)
    for i in range(period - 1 + lookback, len(closes)):
        if ma_values[i] is not None and ma_values[i - lookback] is not None:
            slope_values[i] = (ma_values[i] - ma_values[i - lookback]) / lookback
    return slope_values


def compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0):
    """Compute SuperTrend indicator.
    
    Returns dict with:
      - supertrend: list of SuperTrend line values
      - direction: +1 for uptrend (price above ST), -1 for downtrend (price below ST)
      - upper_band: the upper band line (used when in downtrend)
      - lower_band: the lower band line (used when in uptrend)
    """
    atr = compute_atr(highs, lows, closes, atr_period)
    n = len(highs)
    
    # Mid point
    mid = [(highs[i] + lows[i]) / 2.0 for i in range(n)]
    
    # Raw bands
    upper_band_raw = [None] * n
    lower_band_raw = [None] * n
    for i in range(n):
        if atr[i] is not None:
            upper_band_raw[i] = mid[i] + multiplier * atr[i]
            lower_band_raw[i] = mid[i] - multiplier * atr[i]
    
    # Smooth bands: upper band only goes up, lower band only goes down
    upper_band = [None] * n
    lower_band = [None] * n
    
    for i in range(n):
        if upper_band_raw[i] is None or lower_band_raw[i] is None:
            continue
        if i == 0:
            upper_band[i] = upper_band_raw[i]
            lower_band[i] = lower_band_raw[i]
        else:
            # Upper band: only decrease if current raw < previous, else keep previous
            if upper_band[i - 1] is not None:
                upper_band[i] = min(upper_band_raw[i], upper_band[i - 1])
            else:
                upper_band[i] = upper_band_raw[i]
            # Lower band: only increase if current raw > previous, else keep previous
            if lower_band[i - 1] is not None:
                lower_band[i] = max(lower_band_raw[i], lower_band[i - 1])
            else:
                lower_band[i] = lower_band_raw[i]
    
    # Direction: +1 = uptrend, -1 = downtrend
    direction = [0] * n
    supertrend = [None] * n
    
    for i in range(n):
        if upper_band[i] is None or lower_band[i] is None:
            continue
        
        if i == 0:
            if closes[i] > lower_band[i]:
                direction[i] = 1
                supertrend[i] = lower_band[i]
            else:
                direction[i] = -1
                supertrend[i] = upper_band[i]
            continue
        
        if direction[i - 1] == 1:
            # Was in uptrend: stay up if close > lower_band, flip to down if close < lower_band
            if closes[i] <= lower_band[i]:
                direction[i] = -1
                supertrend[i] = upper_band[i]
            else:
                direction[i] = 1
                supertrend[i] = lower_band[i]
        else:
            # Was in downtrend: stay down if close < upper_band, flip to up if close > upper_band
            if closes[i] >= upper_band[i]:
                direction[i] = 1
                supertrend[i] = lower_band[i]
            else:
                direction[i] = -1
                supertrend[i] = upper_band[i]
    
    return {
        "supertrend": supertrend,
        "direction": direction,
        "upper_band": upper_band,
        "lower_band": lower_band,
    }


def compute_trend_columns(highs, lows, closes, n):
    """Compute all trend indicator columns for a single ticker's data."""
    ta_ema20 = compute_ema(closes, 20) if n >= 20 else [None] * n
    ta_ema50 = compute_ema(closes, 50) if n >= 50 else [None] * n
    ta_ema200 = compute_ema(closes, 200) if n >= 200 else [None] * n
    st = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)
    ta_ma20 = compute_ma(closes, 20)
    ta_ma50 = compute_ma(closes, 50)
    ta_sma10 = compute_ma(closes, 10)
    ta_ma20_slope = compute_ma_slope(closes, 20, lookback=10)
    ta_ma50_slope = compute_ma_slope(closes, 50, lookback=10)
    ta_price_ma20_ratio = [None] * n
    for i in range(n):
        if ta_ma20[i] is not None and ta_ma20[i] != 0:
            ta_price_ma20_ratio[i] = closes[i] / ta_ma20[i]

    return {
        "ta_ema20": ta_ema20,
        "ta_ema50": ta_ema50,
        "ta_ema200": ta_ema200,
        "ta_supertrend": st["supertrend"],
        "ta_supertrend_direction": st["direction"],
        "ta_supertrend_upper": st["upper_band"],
        "ta_supertrend_lower": st["lower_band"],
        "ta_ma20": ta_ma20,
        "ta_ma50": ta_ma50,
        "ta_sma10": ta_sma10,
        "ta_ma20_slope": ta_ma20_slope,
        "ta_ma50_slope": ta_ma50_slope,
        "ta_price_ma20_ratio": ta_price_ma20_ratio,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()

    # Use market data as the source of truth
    file_total = len(raw_df)

    # Start from market data, merge existing TA columns onto it
    df = raw_df.copy()
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        existing_df["Date"] = pd.to_datetime(existing_df["Date"])
        # Only merge TA-prefixed columns (skip market data columns to avoid duplicates)
        ta_cols = [c for c in existing_df.columns if c.startswith("ta_")]
        if ta_cols:
            existing_ta = existing_df[["Date"] + ta_cols]
            df = df.merge(existing_ta, on="Date", how="left")

    trend_cols = compute_trend_columns(highs, lows, closes, file_total)
    for col, values in trend_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_trend",
    description="trend indicators: EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA ratio",
    process_csv_fn=process_csv,
)

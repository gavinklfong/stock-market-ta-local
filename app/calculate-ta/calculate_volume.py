import math
import os
import pandas as pd

from common import main, read_yfinance_csv


def compute_ofi(open_prices, highs, lows, closes):
    if len(open_prices) < 2:
        return [None] * len(open_prices)

    ofi_values = [None] * len(open_prices)
    for i in range(len(open_prices)):
        high_low_range = highs[i] - lows[i]
        if high_low_range == 0:
            ofi_values[i] = 0.0
        else:
            ofi_values[i] = (closes[i] - open_prices[i]) / high_low_range

    return ofi_values


def compute_obv(closes, volumes):
    """Compute On-Balance Volume. Returns a list aligned with input."""
    n = len(closes)
    result = [0.0] * n
    if n < 1:
        return result

    result[0] = float(volumes[0])
    for i in range(1, n):
        if float(closes[i]) > float(closes[i - 1]):
            result[i] = result[i - 1] + float(volumes[i])
        elif float(closes[i]) < float(closes[i - 1]):
            result[i] = result[i - 1] - float(volumes[i])
        else:
            result[i] = result[i - 1]

    return result


def compute_cmf(highs, lows, closes, volumes, period=20):
    """Compute Chaikin Money Flow. Returns a list aligned with input."""
    n = len(highs)
    result = [None] * n
    if n < period:
        return result

    mfv_sums = [0.0] * period
    vol_sums = [0.0] * period

    for i in range(period):
        high_i = float(highs[i])
        low_i = float(lows[i])
        vol_i = float(volumes[i])
        if high_i != low_i:
            mfv = ((float(closes[i]) - low_i) - (high_i - float(closes[i]))) / (high_i - low_i)
        else:
            mfv = 0.0
        mfv_sums[i] = mfv * vol_i
        vol_sums[i] = vol_i

    for i in range(period - 1, n):
        if vol_sums[i % period] != 0:
            result[i] = mfv_sums[i % period] / vol_sums[i % period]
        else:
            result[i] = 0.0

    # Slide window
    for i in range(period, n):
        idx = i % period
        high_i = float(highs[i])
        low_i = float(lows[i])
        vol_i = float(volumes[i])
        if high_i != low_i:
            mfv = ((float(closes[i]) - low_i) - (high_i - float(closes[i]))) / (high_i - low_i)
        else:
            mfv = 0.0
        mfv_sums[idx] = mfv * vol_i
        vol_sums[idx] = vol_i

        rolling_mfv_sum = sum(mfv_sums)
        rolling_vol_sum = sum(vol_sums)

        if rolling_vol_sum != 0:
            result[i] = rolling_mfv_sum / rolling_vol_sum
        else:
            result[i] = 0.0

    return result


def compute_vwap(highs, lows, closes, volumes, period=20):
    """Compute rolling Volume-Weighted Average Price over a lookback window."""
    n = len(highs)
    result = [None] * n
    if n < period:
        return result

    cumulative_tp_vol = 0.0
    cumulative_vol = 0.0

    # Initialize first window
    for i in range(period):
        typical_price = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        vol = float(volumes[i])
        cumulative_tp_vol += typical_price * vol
        cumulative_vol += vol
    if cumulative_vol > 0:
        result[period - 1] = cumulative_tp_vol / cumulative_vol

    # Slide window
    for i in range(period, n):
        # Remove oldest element from window
        old_tp = (float(highs[i - period]) + float(lows[i - period]) + float(closes[i - period])) / 3.0
        old_vol = float(volumes[i - period])
        cumulative_tp_vol -= old_tp * old_vol
        cumulative_vol -= old_vol

        # Add new element
        new_tp = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        new_vol = float(volumes[i])
        cumulative_tp_vol += new_tp * new_vol
        cumulative_vol += new_vol

        if cumulative_vol > 0:
            result[i] = cumulative_tp_vol / cumulative_vol

    return result


def compute_adl(highs, lows, closes, volumes):
    """Compute Accumulation Distribution Line. Returns a list aligned with input."""
    n = len(highs)
    result = [0.0] * n

    for i in range(n):
        high_i = float(highs[i])
        low_i = float(lows[i])
        close_i = float(closes[i])
        vol_i = float(volumes[i])

        if high_i != low_i:
            clv = ((close_i - low_i) - (high_i - close_i)) / (high_i - low_i)
        else:
            clv = 0.0

        if i == 0:
            result[i] = clv * vol_i
        else:
            result[i] = result[i - 1] + clv * vol_i

    return result


def compute_mfi(highs, lows, closes, volumes, period=14):
    """Compute Money Flow Index. Returns a list aligned with input."""
    n = len(highs)
    result = [None] * n
    if n < period + 1:
        return result

    pos_sum = 0.0
    neg_sum = 0.0

    # Compute first window
    for i in range(period):
        typical_price = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        raw_mf = typical_price * float(volumes[i])
        if i > 0:
            prev_tp = (float(highs[i - 1]) + float(lows[i - 1]) + float(closes[i - 1])) / 3.0
            if typical_price > prev_tp:
                pos_sum += raw_mf
            elif typical_price < prev_tp:
                neg_sum += raw_mf

    if neg_sum == 0 and pos_sum == 0:
        result[period - 1] = 50.0
    elif neg_sum == 0:
        result[period - 1] = 100.0
    else:
        mf_ratio = pos_sum / neg_sum
        result[period - 1] = 100.0 - (100.0 / (1.0 + mf_ratio))

    # Slide window
    for i in range(period, n):
        typical_price = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        raw_mf = typical_price * float(volumes[i])

        prev_tp = (float(highs[i - 1]) + float(lows[i - 1]) + float(closes[i - 1])) / 3.0
        prev_raw_mf = prev_tp * float(volumes[i - 1])

        if typical_price > prev_tp:
            pos_sum += raw_mf - prev_raw_mf
        elif typical_price < prev_tp:
            neg_sum += raw_mf - prev_raw_mf

        if neg_sum == 0 and pos_sum == 0:
            result[i] = 50.0
        elif neg_sum == 0:
            result[i] = 100.0
        else:
            mf_ratio = pos_sum / neg_sum
            result[i] = 100.0 - (100.0 / (1.0 + mf_ratio))

    return result


def compute_emv(highs, lows, volumes, period=14):
    """Compute Ease of Movement. Returns a list aligned with input."""
    n = len(highs)
    result = [None] * n
    if n < 2:
        return result

    emv_raw = [0.0] * n

    for i in range(n):
        high_i = float(highs[i])
        low_i = float(lows[i])
        vol_i = float(volumes[i])

        # Midpoint = (High + Low) / 2
        midpoint = (high_i + low_i) / 2.0

        # Distance Moved
        if i > 0:
            prev_midpoint = (float(highs[i - 1]) + float(lows[i - 1])) / 2.0
            distance_moved = midpoint - prev_midpoint
        else:
            distance_moved = 0.0

        # Box Ratio = Volume / (High - Low), 0 when High == Low
        high_low_range = high_i - low_i
        if high_low_range != 0 and vol_i != 0:
            box_ratio = vol_i / high_low_range
        else:
            box_ratio = 0.0

        # EMV raw = Distance Moved / Box Ratio, 0 when Box Ratio is 0
        if box_ratio != 0:
            emv_raw[i] = distance_moved / box_ratio
        else:
            emv_raw[i] = 0.0

    # Compute SMA of EMV raw values
    if n < period:
        return result

    # First window
    window_sum = 0.0
    for i in range(period):
        window_sum += emv_raw[i]
    result[period - 1] = window_sum / period

    # Slide window
    for i in range(period, n):
        window_sum += emv_raw[i] - emv_raw[i - period]
        result[i] = window_sum / period

    return result


def compute_volume_oscillator(volumes, period_fast=14, period_slow=28):
    """Compute Volume Oscillator (fast EMA - slow EMA of volume). Returns a list aligned with input."""
    n = len(volumes)
    result = [None] * n
    if n < period_slow:
        return result

    # Compute fast EMA
    fast_ema = [0.0] * n
    multiplier_fast = 2.0 / (period_fast + 1)
    fast_ema[period_fast - 1] = sum(float(v) for v in volumes[:period_fast]) / period_fast
    for i in range(period_fast, n):
        fast_ema[i] = (float(volumes[i]) - fast_ema[i - 1]) * multiplier_fast + fast_ema[i - 1]

    # Compute slow EMA
    slow_ema = [0.0] * n
    multiplier_slow = 2.0 / (period_slow + 1)
    slow_ema[period_slow - 1] = sum(float(v) for v in volumes[:period_slow]) / period_slow
    for i in range(period_slow, n):
        slow_ema[i] = (float(volumes[i]) - slow_ema[i - 1]) * multiplier_slow + slow_ema[i - 1]

    # Volume Oscillator = Fast EMA - Slow EMA (first valid at period_slow - 1)
    for i in range(period_slow - 1, n):
        result[i] = fast_ema[i] - slow_ema[i]

    return result


def compute_volume_zscore(volumes, window=20):
    """Compute Z-score of volume over a rolling window.

    Volume Z-score = (volume - mean(volume_window)) / std(volume_window)

    This tells us how unusual the current volume is relative to its recent
    distribution. A Z-score of +2 means volume is 2 standard deviations
    above its rolling mean — a potential breakout signal.

    Parameters
    ----------
    volumes : list[float]
        Volume for each bar.
    window : int
        Rolling window for Z-score calculation (default 20).

    Returns
    -------
    list[float | None]
        Z-score values aligned with input; None before warmup.
    """
    n = len(volumes)
    result = [None] * n

    if n < window:
        return result

    for i in range(window - 1, n):
        window_vols = [float(volumes[j]) for j in range(i - window + 1, i + 1)]

        mean_vol = sum(window_vols) / window
        variance = sum((v - mean_vol) ** 2 for v in window_vols) / window
        std_vol = variance ** 0.5

        if std_vol > 0:
            result[i] = (float(volumes[i]) - mean_vol) / std_vol

    return result


def compute_volume_columns(highs, lows, closes, volumes, n, opens=None):
    """Compute all volume indicator columns for a single ticker's data."""
    ta_obv = compute_obv(closes, volumes)
    ta_cmf = compute_cmf(highs, lows, closes, volumes) if n >= 20 else [None] * n
    ta_vwap = compute_vwap(highs, lows, closes, volumes)
    ta_ofi = compute_ofi(opens, highs, lows, closes) if opens is not None else [None] * n
    ta_log_volume = [math.log(v) if v > 0 else None for v in volumes]
    ta_adl = compute_adl(highs, lows, closes, volumes)
    ta_mfi14 = compute_mfi(highs, lows, closes, volumes) if n >= 14 else [None] * n
    ta_emv14 = compute_emv(highs, lows, volumes) if n >= 14 else [None] * n
    ta_volume_osc = compute_volume_oscillator(volumes) if n >= 28 else [None] * n
    ta_volume_zscore = compute_volume_zscore(volumes) if n >= 20 else [None] * n

    return {
        "ta_obv": ta_obv,
        "ta_cmf": ta_cmf,
        "ta_vwap": ta_vwap,
        "ta_ofi": ta_ofi,
        "ta_log_volume": ta_log_volume,
        "ta_adl": ta_adl,
        "ta_mfi14": ta_mfi14,
        "ta_emv14": ta_emv14,
        "ta_volume_osc": ta_volume_osc,
        "ta_volume_zscore": ta_volume_zscore,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()
    volumes = raw_df["Volume"].tolist()
    opens = raw_df["Open"].tolist()

    # Compute this module's TA columns only
    volume_cols = compute_volume_columns(highs, lows, closes, volumes, file_total, opens=opens)

    # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in volume_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_volume",
    description="volume indicators: OBV, CMF(20), VWAP(20), OFI, log volume, ADL, MFI(14), EMV(14), Volume Oscillator(14,28), Volume Z-Score(20)",
    process_csv_fn=process_csv,
)

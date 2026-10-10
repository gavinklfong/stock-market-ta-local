import math
import os
import pandas as pd

from common import main


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


def compute_vwap(highs, lows, closes, volumes):
    """Compute cumulative Volume-Weighted Average Price. Returns a list aligned with input."""
    n = len(highs)
    result = [None] * n
    if n < 1:
        return result

    cumulative_tp_vol = 0.0
    cumulative_vol = 0.0

    for i in range(n):
        typical_price = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        vol = float(volumes[i])
        cumulative_tp_vol += typical_price * vol
        cumulative_vol += vol
        if cumulative_vol > 0:
            result[i] = cumulative_tp_vol / cumulative_vol

    return result


def compute_volume_columns(highs, lows, closes, volumes, n, opens=None):
    """Compute all volume indicator columns for a single ticker's data."""
    ta_obv = compute_obv(closes, volumes)
    ta_cmf = compute_cmf(highs, lows, closes, volumes) if n >= 20 else [None] * n
    ta_vwap = compute_vwap(highs, lows, closes, volumes)
    ta_ofi = compute_ofi(opens, highs, lows, closes) if opens is not None else [None] * n
    ta_log_volume = [math.log(v) if v > 0 else None for v in volumes]

    return {
        "ta_obv": ta_obv,
        "ta_cmf": ta_cmf,
        "ta_vwap": ta_vwap,
        "ta_ofi": ta_ofi,
        "ta_log_volume": ta_log_volume,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = pd.read_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()
    volumes = raw_df["Volume"].tolist()
    opens = raw_df["Open"].tolist()

    # Merge with existing TA data if available (preserves columns from prior modules)
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        highs = raw_df["High"].tolist()
        lows = raw_df["Low"].tolist()
        closes = raw_df["Close"].tolist()
        volumes = raw_df["Volume"].tolist()
        opens = raw_df["Open"].tolist()
    else:
        df = raw_df.copy()

    volume_cols = compute_volume_columns(highs, lows, closes, volumes, file_total, opens=opens)
    for col, values in volume_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_volume",
    description="volume indicators: OBV, CMF(20), VWAP, OFI, log volume",
    process_csv_fn=process_csv,
)

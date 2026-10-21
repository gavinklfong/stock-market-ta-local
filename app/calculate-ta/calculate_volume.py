import json
import math
import os
import pandas as pd

from common import main, read_yfinance_csv


# =============================================================================
# State file helpers
# =============================================================================


def _save_state(state, state_path):
    """Persist computation state to a JSON file."""
    with open(state_path, "w") as f:
        json.dump(state, f)


def _load_state(state_path):
    """Load computation state from a JSON file.

    Returns None if the file does not exist or is corrupted.
    """
    if not os.path.exists(state_path):
        return None
    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


# =============================================================================
# Helpers to extract state from full computation
# =============================================================================


def _get_obv_state(closes, volumes):
    """Compute OBV and return state values for state persistence.

    Returns a dict with:
      - last_obv: OBV value at the last row
    """
    n = len(closes)
    obv = 0.0
    if n >= 1:
        obv = float(volumes[0])
        for i in range(1, n):
            if float(closes[i]) > float(closes[i - 1]):
                obv += float(volumes[i])
            elif float(closes[i]) < float(closes[i - 1]):
                obv -= float(volumes[i])

    return {"last_obv": obv}


def _get_adl_state(highs, lows, closes, volumes):
    """Compute ADL and return state values for state persistence.

    Returns a dict with:
      - last_adl: ADL value at the last row
    """
    n = len(highs)
    result = 0.0
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
            result = clv * vol_i
        else:
            result = result + clv * vol_i

    return {"last_adl": result}


def _get_volume_oscillator_state(volumes, period_fast=14, period_slow=28):
    """Compute Volume Oscillator EMA state and return values for state persistence.

    Returns a dict with:
      - last_fast_ema: fast EMA value at the last row
      - last_slow_ema: slow EMA value at the last row
    """
    n = len(volumes)
    if n < period_slow:
        return {"last_fast_ema": None, "last_slow_ema": None}

    # Compute fast EMA
    multiplier_fast = 2.0 / (period_fast + 1)
    fast_ema = 0.0
    if n >= period_fast:
        fast_ema = sum(float(v) for v in volumes[:period_fast]) / period_fast
        for i in range(period_fast, n):
            fast_ema = (float(volumes[i]) - fast_ema) * multiplier_fast + fast_ema

    # Compute slow EMA
    multiplier_slow = 2.0 / (period_slow + 1)
    slow_ema = 0.0
    if n >= period_slow:
        slow_ema = sum(float(v) for v in volumes[:period_slow]) / period_slow
        for i in range(period_slow, n):
            slow_ema = (float(volumes[i]) - slow_ema) * multiplier_slow + slow_ema

    return {
        "last_fast_ema": fast_ema if n >= period_fast else None,
        "last_slow_ema": slow_ema if n >= period_slow else None,
    }


# =============================================================================
# Incremental EMA helper
# =============================================================================


def compute_ema_from_state(values, period, last_ema, last_idx):
    """Compute EMA continuing from a previous state.

    Parameters
    ----------
    values : list
        All values from the beginning (needed for initial SMA seed).
    period : int
        EMA period.
    last_ema : float
        EMA value at the last index of the previous run.
    last_idx : int
        The index in `values` that `last_ema` corresponds to.

    Returns
    -------
    list
        EMA values for indices last_idx+1 onwards (None for earlier indices).
    """
    k = 2.0 / (period + 1)
    n = len(values)
    result = [None] * n

    # Continue from last known EMA
    current_ema = last_ema
    for i in range(last_idx + 1, n):
        current_ema = float(values[i]) * k + current_ema * (1 - k)
        result[i] = current_ema

    return result


def compute_ofi(open_prices, highs, lows, closes, period=1):
    """Compute Order Flow Intensity. Returns a list aligned with input.

    Parameters
    ----------
    period : int
        Used for consistency with other function signatures; ignored.
    """
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


def compute_ofi_from_state(opens, highs, lows, closes, boundary_start):
    """Compute OFI for all indices (independent per row, no state needed)."""
    n = len(opens)
    result = [None] * n
    for i in range(n):
        high_low_range = highs[i] - lows[i]
        if high_low_range == 0:
            result[i] = 0.0
        else:
            result[i] = (closes[i] - opens[i]) / high_low_range
    return result


def compute_cmf_from_state(highs, lows, closes, volumes, period, boundary_start):
    """Compute CMF for all indices using the same algorithm as compute_cmf.

    boundary_start is retained for API consistency but does not filter
    output — the full algorithm runs from scratch so the incremental
    output matches the full output exactly.
    """
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


def compute_vwap_from_state(highs, lows, closes, volumes, period, boundary_start):
    """Compute rolling VWAP for all indices using the original algorithm.

    boundary_start is retained for API consistency but does not filter
    output — the full algorithm runs from scratch so the incremental
    output matches the full output exactly.
    """
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
        # Remove oldest element
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


def compute_mfi_from_state(highs, lows, closes, volumes, period, boundary_start):
    """Compute MFI for all indices using the original algorithm.

    MFI's pos_sum/neg_sum depends on all price changes from the beginning,
    so we run the original algorithm from scratch. boundary_start is
    retained for API consistency but does not filter output.
    """
    n = len(highs)
    result = [None] * n
    if n < period + 1:
        return result

    pos_sum = 0.0
    neg_sum = 0.0

    # Compute first window
    for i in range(period):
        tp = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        raw_mf = tp * float(volumes[i])
        if i > 0:
            prev_tp = (float(highs[i - 1]) + float(lows[i - 1]) + float(closes[i - 1])) / 3.0
            if tp > prev_tp:
                pos_sum += raw_mf
            elif tp < prev_tp:
                neg_sum += raw_mf

    # Store result
    if period - 1 < n:
        if neg_sum == 0 and pos_sum == 0:
            result[period - 1] = 50.0
        elif neg_sum == 0:
            result[period - 1] = 100.0
        else:
            mf_ratio = pos_sum / neg_sum
            result[period - 1] = 100.0 - (100.0 / (1.0 + mf_ratio))

    # Slide window
    for i in range(period, n):
        tp = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        raw_mf = tp * float(volumes[i])
        prev_tp = (float(highs[i - 1]) + float(lows[i - 1]) + float(closes[i - 1])) / 3.0
        prev_raw_mf = prev_tp * float(volumes[i - 1])

        if tp > prev_tp:
            pos_sum += raw_mf - prev_raw_mf
        elif tp < prev_tp:
            neg_sum += raw_mf - prev_raw_mf

        if neg_sum == 0 and pos_sum == 0:
            result[i] = 50.0
        elif neg_sum == 0:
            result[i] = 100.0
        else:
            mf_ratio = pos_sum / neg_sum
            result[i] = 100.0 - (100.0 / (1.0 + mf_ratio))

    return result


def compute_emv_from_state(highs, lows, volumes, period, boundary_start):
    """Compute EMV for all indices using the original algorithm.

    boundary_start is retained for API consistency but does not filter
    output — the full algorithm runs from scratch so the incremental
    output matches the full output exactly.
    """
    n = len(highs)
    result = [None] * n
    if n < 2:
        return result

    emv_raw = [0.0] * n

    for i in range(n):
        high_i = float(highs[i])
        low_i = float(lows[i])
        vol_i = float(volumes[i])

        midpoint = (high_i + low_i) / 2.0
        if i > 0:
            prev_midpoint = (float(highs[i - 1]) + float(lows[i - 1])) / 2.0
            distance_moved = midpoint - prev_midpoint
        else:
            distance_moved = 0.0

        high_low_range = high_i - low_i
        if high_low_range != 0 and vol_i != 0:
            box_ratio = vol_i / high_low_range
        else:
            box_ratio = 0.0

        if box_ratio != 0:
            emv_raw[i] = distance_moved / box_ratio
        else:
            emv_raw[i] = 0.0

    if n < period:
        return result

    window_sum = 0.0
    for i in range(period):
        window_sum += emv_raw[i]

    result[period - 1] = window_sum / period

    for i in range(period, n):
        window_sum += emv_raw[i] - emv_raw[i - period]
        result[i] = window_sum / period

    return result


def compute_volume_zscore_from_state(volumes, window, boundary_start):
    """Compute Volume Z-Score for all indices using the original algorithm.

    boundary_start is retained for API consistency but does not filter
    output — the full algorithm runs from scratch so the incremental
    output matches the full output exactly.
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


def compute_volume_percentile_from_state(volumes, window, boundary_start):
    """Compute Volume Percentile for all indices using the original algorithm.

    boundary_start is retained for API consistency but does not filter
    output — the full algorithm runs from scratch so the incremental
    output matches the full output exactly.
    """
    n = len(volumes)
    result = [None] * n
    if n < window:
        return result

    for i in range(window - 1, n):
        window_vols = [float(volumes[j]) for j in range(i - window + 1, i + 1)]
        current_vol = float(volumes[i])
        below_count = sum(1 for v in window_vols if v < current_vol)
        result[i] = (below_count / window) * 100.0

    return result


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


def compute_obv_from_state(closes, volumes, last_obv, last_idx):
    """Compute OBV continuing from a previous state.

    Parameters
    ----------
    closes : list
        All close prices (needed for price change comparison).
    volumes : list
        All volumes.
    last_obv : float
        OBV value at the last index of the previous run.
    last_idx : int
        The index that `last_obv` corresponds to.

    Returns
    -------
    list
        OBV values for all indices; full recomputation for indices <= last_idx,
        then incremental for indices > last_idx.
    """
    n = len(closes)
    result = [0.0] * n

    # Recompute OBV up to and including last_idx to ensure consistency
    # (closes/volumes may have changed for historical rows)
    if n >= 1:
        result[0] = float(volumes[0])
        for i in range(1, n):
            if float(closes[i]) > float(closes[i - 1]):
                result[i] = result[i - 1] + float(volumes[i])
            elif float(closes[i]) < float(closes[i - 1]):
                result[i] = result[i - 1] - float(volumes[i])
            else:
                result[i] = result[i - 1]

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


def compute_adl_from_state(highs, lows, closes, volumes, last_adl, last_idx):
    """Compute ADL continuing from a previous state.

    Parameters
    ----------
    highs, lows, closes, volumes : list
        All data (historical rows may have changed).
    last_adl : float
        ADL value at the last index of the previous run.
    last_idx : int
        The index that `last_adl` corresponds to.

    Returns
    -------
    list
        ADL values for all indices.
    """
    n = len(highs)
    result = [0.0] * n

    # Recompute ADL from scratch to ensure consistency with any historical changes
    cumulative = 0.0
    for i in range(n):
        high_i = float(highs[i])
        low_i = float(lows[i])
        close_i = float(closes[i])
        vol_i = float(volumes[i])

        if high_i != low_i:
            clv = ((close_i - low_i) - (high_i - close_i)) / (high_i - low_i)
        else:
            clv = 0.0

        cumulative = cumulative + clv * vol_i
        result[i] = cumulative

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


def compute_volume_oscillator_from_state(volumes, last_fast_ema, last_slow_ema, last_idx,
                                          period_fast=14, period_slow=28):
    """Compute Volume Oscillator continuing from previous EMA state.

    Parameters
    ----------
    volumes : list
        All volume values (needed for initial SMA seed).
    last_fast_ema : float
        Fast EMA value at the last index of the previous run.
    last_slow_ema : float
        Slow EMA value at the last index of the previous run.
    last_idx : int
        The index that the EMA values correspond to.
    period_fast, period_slow : int
        EMA periods.

    Returns
    -------
    list
        Volume Oscillator values for all indices.
    """
    n = len(volumes)
    result = [None] * n

    # Recompute fast EMA from scratch (historical data may have changed)
    fast_ema = [0.0] * n
    multiplier_fast = 2.0 / (period_fast + 1)
    if n >= period_fast:
        fast_ema[period_fast - 1] = sum(float(v) for v in volumes[:period_fast]) / period_fast
        for i in range(period_fast, n):
            fast_ema[i] = (float(volumes[i]) - fast_ema[i - 1]) * multiplier_fast + fast_ema[i - 1]

    # Recompute slow EMA from scratch
    slow_ema = [0.0] * n
    multiplier_slow = 2.0 / (period_slow + 1)
    if n >= period_slow:
        slow_ema[period_slow - 1] = sum(float(v) for v in volumes[:period_slow]) / period_slow
        for i in range(period_slow, n):
            slow_ema[i] = (float(volumes[i]) - slow_ema[i - 1]) * multiplier_slow + slow_ema[i - 1]

    # Volume Oscillator = Fast EMA - Slow EMA
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


def compute_volume_percentile(volumes, window=20):
    """Compute rolling percentile rank of volume.

    Volume percentile = percentage of values in the rolling window
    that are less than the current volume.

    This tells us where the current volume ranks relative to its recent
    distribution. A percentile of 90 means volume is higher than 90% of
    the past 20 bars — a potential breakout signal.

    Parameters
    ----------
    volumes : list[float]
        Volume for each bar.
    window : int
        Rolling window for percentile calculation (default 20).

    Returns
    -------
    list[float | None]
        Percentile values (0–100) aligned with input; None before warmup.
    """
    n = len(volumes)
    result = [None] * n

    if n < window:
        return result

    for i in range(window - 1, n):
        window_vols = [float(volumes[j]) for j in range(i - window + 1, i + 1)]
        current_vol = float(volumes[i])

        # Count values strictly below current volume
        below_count = sum(1 for v in window_vols if v < current_vol)
        result[i] = (below_count / window) * 100.0

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
    ta_volume_percentile = compute_volume_percentile(volumes) if n >= 20 else [None] * n

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
        "ta_volume_percentile": ta_volume_percentile,
    }


def compute_volume_columns_incremental(highs, lows, closes, volumes, n, opens=None,
                                        state=None, prev_row_count=0):
    """Compute all volume indicator columns, using incremental computation when possible.

    Parameters
    ----------
    state : dict or None
        Previously saved computation state. If None or incomplete, falls back to full
        recomputation for all indicators.
    prev_row_count : int
        Number of rows from the previous run.

    Returns
    -------
    dict
        All volume indicator columns as full-length lists.
    """
    # Determine boundary: max lookback period is 28 (Volume Oscillator slow period)
    # Add a small buffer for sliding window reconstruction
    buffer = 50
    boundary_start = max(0, prev_row_count - buffer)
    has_state = state is not None and "last_obv" in state

    if has_state:
        # ---- OBV (incremental) ----
        ta_obv = compute_obv_from_state(
            closes, volumes,
            state["last_obv"], state.get("last_obv_idx", prev_row_count - 1)
        )

        # ---- ADL (incremental) ----
        ta_adl = compute_adl_from_state(
            highs, lows, closes, volumes,
            state["last_adl"], state.get("last_adl_idx", prev_row_count - 1)
        )

        # ---- CMF (boundary window) ----
        ta_cmf = compute_cmf_from_state(
            highs, lows, closes, volumes, 20, boundary_start
        ) if n >= 20 else [None] * n

        # ---- VWAP (boundary window) ----
        ta_vwap = compute_vwap_from_state(
            highs, lows, closes, volumes, 20, boundary_start
        )

        # ---- OFI (per-row, no lookback) ----
        ta_ofi = compute_ofi_from_state(opens, highs, lows, closes, boundary_start) \
            if opens is not None else [None] * n

        # ---- log_volume (per-row, no lookback) ----
        ta_log_volume = [math.log(v) if v > 0 else None for v in volumes]

        # ---- MFI (boundary window) ----
        ta_mfi14 = compute_mfi_from_state(
            highs, lows, closes, volumes, 14, boundary_start
        ) if n >= 14 else [None] * n

        # ---- EMV (boundary window) ----
        ta_emv14 = compute_emv_from_state(
            highs, lows, volumes, 14, boundary_start
        ) if n >= 14 else [None] * n

        # ---- Volume Oscillator (incremental EMA) ----
        if n >= 28:
            ta_volume_osc = compute_volume_oscillator_from_state(
                volumes,
                state.get("last_fast_ema"),
                state.get("last_slow_ema"),
                state.get("last_osc_idx", prev_row_count - 1),
            )
        else:
            ta_volume_osc = [None] * n

        # ---- Volume Z-Score (boundary window) ----
        ta_volume_zscore = compute_volume_zscore_from_state(
            volumes, 20, boundary_start
        ) if n >= 20 else [None] * n

        # ---- Volume Percentile (boundary window) ----
        ta_volume_percentile = compute_volume_percentile_from_state(
            volumes, 20, boundary_start
        ) if n >= 20 else [None] * n

    else:
        # Full recomputation
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
        ta_volume_percentile = compute_volume_percentile(volumes) if n >= 20 else [None] * n

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
        "ta_volume_percentile": ta_volume_percentile,
    }


def process_csv(input_or_df, output_path, total_files, current_file, _lock=None):
    """Process a single ticker's OHLCV data into volume indicator output.

    Accepts either a pre-parsed DataFrame (from run_calculation.py shared cache)
    or a file path string (when called standalone via main()).

    Parameters
    ----------
    input_or_df : str or pd.DataFrame
        File path or pre-parsed DataFrame.
    output_path : str
        Path to write the volume indicator CSV.
    total_files : int
        Total number of files in the batch (for progress reporting).
    current_file : int
        1-based index of this file in the batch.
    _lock : threading.Lock, optional
        Unused lock (kept for API compatibility).

    Returns
    -------
    int
        Total number of rows written to the output CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if isinstance(input_or_df, pd.DataFrame):
        raw_df = input_or_df.copy()
    else:
        raw_df = read_yfinance_csv(input_or_df)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    # ---- State detection (state files live in state/ subdirectory) ----
    base = output_path.rsplit(".", 1)[0]
    state_dir = os.path.join(os.path.dirname(output_path), "state")
    os.makedirs(state_dir, exist_ok=True)
    state_path = os.path.join(state_dir, os.path.basename(base) + "_state.json")
    state = _load_state(state_path)

    # Detect today's date: if the last row's date matches today and there's
    # existing output, force full recomputation so today's indicators are
    # always up to date even without new rows.
    today = pd.Timestamp(pd.Timestamp.now().date())
    last_date = raw_df["Date"].iloc[-1] if file_total > 0 else None
    overwrite_today = (
        last_date is not None
        and (last_date.date() == today.date() if hasattr(last_date, "date") else str(last_date) == str(today.date()))
        and os.path.exists(output_path)
        and file_total > 0
    )

    use_incremental = (
        not overwrite_today
        and state is not None
        and state.get("_version") == 1
        and file_total > state.get("prev_row_count", 0)
    )

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()
    volumes = raw_df["Volume"].tolist()
    opens = raw_df["Open"].tolist()

    if use_incremental:
        prev_row_count = state.get("prev_row_count", 0)
        volume_cols = compute_volume_columns_incremental(
            highs, lows, closes, volumes, file_total,
            opens=opens, state=state, prev_row_count=prev_row_count
        )
    else:
        volume_cols = compute_volume_columns(highs, lows, closes, volumes, file_total, opens=opens)

    # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in volume_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)

    # ---- Save state for next incremental run ----
    if use_incremental or file_total > 0:
        new_state = {
            "_version": 1,
            "prev_row_count": file_total,
            "last_date": str(raw_df["Date"].iloc[-1]) if file_total > 0 else None,
            "last_obv": volume_cols["ta_obv"][-1] if file_total > 0 else None,
            "last_obv_idx": file_total - 1 if file_total > 0 else None,
            "last_adl": volume_cols["ta_adl"][-1] if file_total > 0 else None,
            "last_adl_idx": file_total - 1 if file_total > 0 else None,
        }
        if file_total >= 28:
            # Extract Volume Oscillator EMA state
            vol_osc_state = _get_volume_oscillator_state(volumes)
            new_state["last_fast_ema"] = vol_osc_state["last_fast_ema"]
            new_state["last_slow_ema"] = vol_osc_state["last_slow_ema"]
            new_state["last_osc_idx"] = file_total - 1
        _save_state(new_state, state_path)

    return len(df)


main(
    module_name="calculate_volume",
    description="volume indicators: OBV, CMF(20), VWAP(20), OFI, log volume, ADL, MFI(14), EMV(14), Volume Oscillator(14,28), Volume Z-Score(20), Volume Percentile(20)",
    process_csv_fn=process_csv,
)

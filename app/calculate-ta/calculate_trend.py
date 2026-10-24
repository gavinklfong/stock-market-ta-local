import math
import os

import numpy as np
import pandas as pd

from common import compute_ema, load_state, main, read_yfinance_csv, save_state


# =============================================================================
# Helpers to extract state from full computation
# =============================================================================


def _get_adx_di_state(highs, lows, closes, period=14):
    """Compute ADX/DI and return smoothed state values for state persistence.

    Returns a dict with keys suitable for saving to the state file:
      - last_smoothed_tr: smoothed TR at the last row
      - last_smoothed_plus_dm: smoothed +DM at the last row
      - last_smoothed_minus_dm: smoothed -DM at the last row
      - last_adx: ADX value at the last row (or None)
    """
    n = len(highs)
    if n < period + 1:
        return {
            "last_smoothed_tr": 0.0,
            "last_smoothed_plus_dm": 0.0,
            "last_smoothed_minus_dm": 0.0,
            "last_adx": None,
        }

    k = 1.0 / period

    # Directional movement
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move

    # True range
    true_range = [0.0] * n
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_range[i] = tr

    # Wilder's smoothing (recursive sum)
    def _wilder_sum(values, start, end, period):
        s = sum(values[i] for i in range(start, end))
        out = [0.0] * len(values)
        out[end - 1] = s
        for i in range(end, len(values)):
            out[i] = out[i - 1] - out[i - 1] * k + values[i]
        return out

    smoothed_tr = _wilder_sum(true_range, 1, period + 1, period)
    smoothed_plus_dm = _wilder_sum(plus_dm, 1, period + 1, period)
    smoothed_minus_dm = _wilder_sum(minus_dm, 1, period + 1, period)

    # +DI / -DI
    plus_di = [None] * n
    minus_di = [None] * n
    for i in range(period, n):
        st = smoothed_tr[i]
        if st == 0:
            continue
        plus_di[i] = (smoothed_plus_dm[i] / st) * 100
        minus_di[i] = (smoothed_minus_dm[i] / st) * 100

    # DX
    dx_values = {}
    for i in range(period + 1, n):
        pdi = plus_di[i]
        mdi = minus_di[i]
        if pdi is None or mdi is None:
            continue
        di_sum = pdi + mdi
        if di_sum == 0:
            continue
        dx_values[i] = (abs(pdi - mdi) / di_sum) * 100

    # ADX
    adx = [None] * n
    init_dx_start = period + 1
    init_dx_end = period + 15
    init_idx = init_dx_end - 1

    for i in range(period + 1, n):
        if i not in dx_values:
            continue
        dx = dx_values[i]
        if i == init_idx:
            sum_dx = sum(dx_values[j] for j in range(init_dx_start, init_dx_end) if j in dx_values)
            count = sum(1 for j in range(init_dx_start, init_dx_end) if j in dx_values)
            if count > 0:
                adx[i] = sum_dx / count
        else:
            prev_adx = adx[i - 1]
            if prev_adx is not None:
                adx[i] = prev_adx * (1 - k) + dx * k

    last_idx = n - 1
    return {
        "last_smoothed_tr": smoothed_tr[last_idx],
        "last_smoothed_plus_dm": smoothed_plus_dm[last_idx],
        "last_smoothed_minus_dm": smoothed_minus_dm[last_idx],
        "last_adx": adx[last_idx],
    }


def _get_atr_state(highs, lows, closes, period=14):
    """Compute ATR and return state values for state persistence.

    Returns a dict with:
      - last_tr: true range at the last row
      - last_atr: ATR value at the last row (or None)
    """
    n = len(highs)
    if n == 0:
        return {"last_tr": 0.0, "last_atr": None}

    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)
    c = np.asarray(closes, dtype=float)

    # Pad shorter arrays to match the longest
    if len(c) < n:
        c = np.pad(c, (0, n - len(c)), constant_values=c[-1] if len(c) > 0 else 0)
    if len(l) < n:
        l = np.pad(l, (0, n - len(l)), constant_values=0.0)

    # True Range vectorized
    tr = np.empty(n, dtype=float)
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(
        np.maximum(h[1:] - l[1:], np.abs(h[1:] - c[:-1])),
        np.abs(l[1:] - c[:-1]),
    )

    atr_values = compute_atr(highs, lows, closes, period)
    return {"last_tr": float(tr[n - 1]), "last_atr": atr_values[n - 1]}


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


# =============================================================================
# Incremental ATR helper
# =============================================================================


def compute_atr_from_state(highs, lows, closes, period, last_tr, last_atr, last_idx):
    """Compute ATR continuing from a previous state.

    Parameters
    ----------
    highs, lows, closes : list
        All OHLC data from the beginning.
    period : int
        ATR period.
    last_tr : float
        True range at the last index of the previous run.
    last_atr : float
        ATR value at the last index of the previous run.
    last_idx : int
        The index in the data that `last_atr` corresponds to.

    Returns
    -------
    list
        ATR values for all indices (None where not yet valid).
    """
    n = len(highs)
    result = [None] * n
    k = 2.0 / (period + 1)

    # Vectorized True Range for new rows
    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)
    c = np.asarray(closes, dtype=float)
    tr = np.empty(n, dtype=float)
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(
        np.maximum(h[1:] - l[1:], np.abs(h[1:] - c[:-1])),
        np.abs(l[1:] - c[:-1]),
    )

    # Continue from last known ATR
    current_atr = last_atr
    for i in range(last_idx + 1, n):
        if i > period:
            current_atr = tr[i] * k + current_atr * (1 - k)
            result[i] = current_atr

    return result


# =============================================================================
# EMA computation
# =============================================================================


def compute_ma_slope_incremental(closes, period, lookback, prev_row_count,
                                  last_ma_values):
    """Compute MA slope for new rows starting from a boundary.

    MA slope at index i = (MA[i] - MA[i - lookback]) / lookback

    Parameters
    ----------
    closes : list
        All close prices.
    period : int
        MA period.
    lookback : int
        Lookback for slope calculation.
    prev_row_count : int
        Number of rows from the previous run.
    last_ma_values : dict
        Mapping of index -> MA value for the last `lookback` rows
        before `prev_row_count`.

    Returns
    -------
    list
        MA slope values for all indices (None where not yet valid).
    """
    n = len(closes)
    result = [None] * n
    ma_start = period - 1

    # Compute MA for the boundary window and new rows
    for i in range(max(period - 1 + lookback, ma_start + lookback), n):
        if i >= len(last_ma_values) or (i - lookback) < 0:
            # Need to compute MA from scratch for this index
            window = closes[i - period + 1: i + 1]
            ma_i = sum(window) / period
            if i - lookback >= 0 and i - lookback < len(last_ma_values):
                ma_prev = last_ma_values[i - lookback]
                if ma_prev is not None:
                    result[i] = (ma_i - ma_prev) / lookback
            continue
        ma_prev = last_ma_values.get(i - lookback)
        if ma_prev is None:
            continue
        # Compute current MA
        window = closes[i - period + 1: i + 1]
        ma_i = sum(window) / period
        result[i] = (ma_i - ma_prev) / lookback

    return result


def compute_atr(highs, lows, closes, period=14):
    """Compute Wilder's ATR. Returns list aligned with input.

    Vectorized implementation: True Range via numpy, ATR via FFT-based EMA.
    ATR seeds at index ``period`` (SMA of first period TRs), then recurses
    from index ``period + 1`` using TR values — TR[period] is skipped.
    """
    n = len(highs)
    if n < period + 1:
        return [None] * n
    if n == 0:
        return []

    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)
    c = np.asarray(closes, dtype=float)

    # Pad shorter arrays to match the longest (matches original loop behavior)
    if len(c) < n:
        c = np.pad(c, (0, n - len(c)), constant_values=c[-1] if len(c) > 0 else 0)
    if len(l) < n:
        l = np.pad(l, (0, n - len(l)), constant_values=0.0)

    # True Range vectorized
    tr = np.empty(n, dtype=float)
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(
        np.maximum(h[1:] - l[1:], np.abs(h[1:] - c[:-1])),
        np.abs(l[1:] - c[:-1]),
    )

    k = 2.0 / (period + 1)
    beta = 1.0 - k

    # Seed: SMA of first `period` TRs
    seed = float(np.mean(tr[:period]))

    atr = [None] * n
    atr[period] = seed

    # TR values used in recursion start at index `period + 1`
    new_tr = tr[period + 1:n]
    n_new = len(new_tr)
    if n_new == 0:
        return atr

    # Vectorized EMA recursion (same closed-form as compute_ema):
    #   atr[period + j] = beta^j * seed
    #                   + k * sum_{m=0}^{j-1} new_tr[m] * beta^(j-1-m)
    weights = k * beta ** np.arange(n_new)
    conv = np.convolve(new_tr, weights, 'full')
    price_contrib = conv[:n_new]
    seed_decay = beta ** np.arange(1, n_new + 1) * seed

    atr[period + 1:period + 1 + n_new] = seed_decay + price_contrib
    return atr


def compute_supertrend_incremental(highs, lows, closes, atr_period, multiplier,
                                    prev_row_count, last_atr_values,
                                    last_direction, last_upper_band,
                                    last_lower_band, existing_direction=None):
    """Compute SuperTrend for new rows continuing from previous state.
    
    Uses numpy for band computation and sequential loop for band smoothing
    (comparing against previous smoothed value).
    
    Returns dict with supertrend, direction, upper_band, lower_band for
    all indices (full-length lists).
    """
    n = len(highs)
    atr = compute_atr(highs, lows, closes, atr_period)
    
    # Convert to numpy arrays
    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)
    c = np.asarray(closes, dtype=float)
    a = np.asarray(atr, dtype=float)
    
    # Mid point and raw bands (vectorized)
    mid = (h + l) / 2.0
    upper_band_raw = np.where(a != 0, mid + multiplier * a, np.nan)
    lower_band_raw = np.where(a != 0, mid - multiplier * a, np.nan)
    
    # Smooth bands: upper = min(raw, prev_smoothed), lower = max(raw, prev_smoothed)
    upper_band = np.full(n, np.nan, dtype=float)
    lower_band = np.full(n, np.nan, dtype=float)
    
    has_valid = np.any(~np.isnan(upper_band_raw))
    
    if existing_direction is not None and len(existing_direction) >= prev_row_count:
        # For incremental: compute smooth bands from scratch using sequential loop
        if has_valid:
            first_valid = np.argmax(~np.isnan(upper_band_raw))
            if first_valid < n:
                upper_band[first_valid] = upper_band_raw[first_valid]
                lower_band[first_valid] = lower_band_raw[first_valid]
                for i in range(first_valid + 1, n):
                    if np.isnan(upper_band_raw[i]) or np.isnan(lower_band_raw[i]):
                        continue
                    upper_band[i] = min(upper_band_raw[i], upper_band[i - 1])
                    lower_band[i] = max(lower_band_raw[i], lower_band[i - 1])
        
        # Direction and SuperTrend line - continue from existing state
        direction = np.zeros(n, dtype=int)
        if len(existing_direction) >= n:
            direction[:n] = np.array(existing_direction[:n], dtype=int)
        else:
            direction[:len(existing_direction)] = np.array(existing_direction, dtype=int)
        supertrend = np.full(n, np.nan, dtype=float)
        
        # Continue direction computation from prev_row_count
        for i in range(prev_row_count, n):
            if np.isnan(upper_band[i]) or np.isnan(lower_band[i]):
                continue
            if direction[i - 1] == 1:
                if c[i] <= lower_band[i]:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
                else:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
            else:
                if c[i] >= upper_band[i]:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
                else:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
    else:
        # No existing direction: compute from scratch
        if has_valid:
            first_valid = np.argmax(~np.isnan(upper_band_raw))
            if first_valid < n:
                upper_band[first_valid] = upper_band_raw[first_valid]
                lower_band[first_valid] = lower_band_raw[first_valid]
                for i in range(first_valid + 1, n):
                    if np.isnan(upper_band_raw[i]) or np.isnan(lower_band_raw[i]):
                        continue
                    upper_band[i] = min(upper_band_raw[i], upper_band[i - 1])
                    lower_band[i] = max(lower_band_raw[i], lower_band[i - 1])
        
        # Direction and SuperTrend line
        direction = np.zeros(n, dtype=int)
        supertrend = np.full(n, np.nan, dtype=float)
        
        if has_valid:
            first_valid = np.argmax(~np.isnan(upper_band_raw))
            if first_valid == 0:
                if c[0] > lower_band[0]:
                    direction[0] = 1
                    supertrend[0] = lower_band[0]
                else:
                    direction[0] = -1
                    supertrend[0] = upper_band[0]
            else:
                # First valid index is not 0: use "continue from prev" logic
                if c[first_valid] >= upper_band[first_valid]:
                    direction[first_valid] = 1
                    supertrend[first_valid] = lower_band[first_valid]
                else:
                    direction[first_valid] = -1
                    supertrend[first_valid] = upper_band[first_valid]
            
            for i in range(first_valid + 1, n):
                if np.isnan(upper_band[i]) or np.isnan(lower_band[i]):
                    continue
                if direction[i - 1] == 1:
                    if c[i] <= lower_band[i]:
                        direction[i] = -1
                        supertrend[i] = upper_band[i]
                    else:
                        direction[i] = 1
                        supertrend[i] = lower_band[i]
                else:
                    if c[i] >= upper_band[i]:
                        direction[i] = 1
                        supertrend[i] = lower_band[i]
                    else:
                        direction[i] = -1
                        supertrend[i] = upper_band[i]
    
    # Convert all np.nan to Python None for consistency with original
    return {
        "supertrend": [None if np.isnan(v) else float(v) for v in supertrend],
        "direction": direction.tolist(),
        "upper_band": [None if np.isnan(v) else float(v) for v in upper_band],
        "lower_band": [None if np.isnan(v) else float(v) for v in lower_band],
    }


def compute_ma(closes, period):
    """Compute Simple Moving Average (SMA) for each candle.
    
    Vectorized implementation using numpy cumsum for O(n) computation
    instead of O(n*period).
    """
    n = len(closes)
    ma_values = [None] * n
    if n < period:
        return ma_values
    c = np.asarray(closes, dtype=float)
    cumsum = np.cumsum(c)
    cumsum[period:] = cumsum[period:] - cumsum[:-period]
    for i in range(period - 1, n):
        ma_values[i] = cumsum[i] / period
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
    
    Uses numpy for band computation and a sequential loop for band smoothing,
    since SuperTrend smoothing compares against the previous smoothed value
    (not the running min/max of all raw values).
    
    Returns dict with:
      - supertrend: list of SuperTrend line values
      - direction: +1 for uptrend (price above ST), -1 for downtrend (price below ST)
      - upper_band: the upper band line (used when in downtrend)
      - lower_band: the lower band line (used when in uptrend)
    """
    atr = compute_atr(highs, lows, closes, atr_period)
    n = len(highs)
    
    # Guard: empty input
    if n == 0:
        return {
            "supertrend": [],
            "direction": [],
            "upper_band": [],
            "lower_band": [],
        }
    
    # Guard: single value - not enough data for ATR, return None bands, direction=0
    if n == 1:
        return {
            "supertrend": [None],
            "direction": [0],
            "upper_band": [None],
            "lower_band": [None],
        }
    
    # Convert to numpy arrays for vectorized operations
    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)
    c = np.asarray(closes, dtype=float)
    a = np.asarray(atr, dtype=float)
    
    # Mid point and raw bands (vectorized)
    mid = (h + l) / 2.0
    upper_band_raw = np.where(a != 0, mid + multiplier * a, np.nan)
    lower_band_raw = np.where(a != 0, mid - multiplier * a, np.nan)
    
    # Smooth bands: upper = min(raw, prev_smoothed), lower = max(raw, prev_smoothed)
    # This is inherently sequential (each value depends on previous smoothed value)
    upper_band = np.full(n, np.nan, dtype=float)
    lower_band = np.full(n, np.nan, dtype=float)
    
    # Find first valid index
    first_valid_idx = n  # sentinel
    for i in range(n):
        if not np.isnan(upper_band_raw[i]):
            first_valid_idx = i
            break
    
    if first_valid_idx < n:
        upper_band[first_valid_idx] = upper_band_raw[first_valid_idx]
        lower_band[first_valid_idx] = lower_band_raw[first_valid_idx]
        
        for i in range(first_valid_idx + 1, n):
            if np.isnan(upper_band_raw[i]) or np.isnan(lower_band_raw[i]):
                continue
            upper_band[i] = min(upper_band_raw[i], upper_band[i - 1])
            lower_band[i] = max(lower_band_raw[i], lower_band[i - 1])
    
    # Direction and SuperTrend line
    direction = np.zeros(n, dtype=int)
    supertrend = np.full(n, np.nan, dtype=float)
    
    if first_valid_idx < n:
        # Initial direction: match original behavior
        # At i=0: fresh start, compare close to lower_band
        # At i>0: continue from prev direction (0 = downtrend logic)
        if first_valid_idx == 0:
            if c[0] > lower_band[0]:
                direction[0] = 1
                supertrend[0] = lower_band[0]
            else:
                direction[0] = -1
                supertrend[0] = upper_band[0]
        else:
            # First valid index is not 0: use "continue from prev" logic
            # direction[0] = 0 → treat as downtrend: flip to uptrend only if close >= upper_band
            if c[first_valid_idx] >= upper_band[first_valid_idx]:
                direction[first_valid_idx] = 1
                supertrend[first_valid_idx] = lower_band[first_valid_idx]
            else:
                direction[first_valid_idx] = -1
                supertrend[first_valid_idx] = upper_band[first_valid_idx]
        
        # Sequential direction computation
        for i in range(first_valid_idx + 1, n):
            if np.isnan(upper_band[i]) or np.isnan(lower_band[i]):
                continue
            if direction[i - 1] == 1:
                if c[i] <= lower_band[i]:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
                else:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
            else:
                if c[i] >= upper_band[i]:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
                else:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
    
    # Convert all np.nan to Python None for consistency with original
    return {
        "supertrend": [None if np.isnan(v) else float(v) for v in supertrend],
        "direction": direction.tolist(),
        "upper_band": [None if np.isnan(v) else float(v) for v in upper_band],
        "lower_band": [None if np.isnan(v) else float(v) for v in lower_band],
    }


def compute_aroon(highs, lows, period=25):
    """Compute Aroon Up and Aroon Down indicators.

    Vectorized implementation using numpy argmax/argmin for window
    operations instead of Python loops.

    Aroon Up    = ((Period - Days Since Highest High) / Period) * 100
    Aroon Down  = ((Period - Days Since Lowest Low)  / Period) * 100

    Returns dict with:
      - aroon_up:    list of Aroon Up values (100 = strong uptrend)
      - aroon_down:  list of Aroon Down values (100 = strong downtrend)
    """
    n = len(highs)
    aroon_up = np.full(n, np.nan, dtype=float)
    aroon_down = np.full(n, np.nan, dtype=float)

    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)

    for i in range(period - 1, n):
        window_start = i - period + 1
        # np.argmax/argmin return relative index within the slice
        rel_high = np.argmax(h[window_start:i + 1])
        rel_low = np.argmin(l[window_start:i + 1])
        days_since_high = i - (window_start + rel_high)
        days_since_low = i - (window_start + rel_low)
        aroon_up[i] = ((period - days_since_high) / period) * 100
        aroon_down[i] = ((period - days_since_low) / period) * 100

    # Convert all np.nan to Python None for consistency with original
    return {
        "aroon_up": [None if np.isnan(v) else float(v) for v in aroon_up],
        "aroon_down": [None if np.isnan(v) else float(v) for v in aroon_down],
    }


def compute_aroon_incremental(highs, lows, period, prev_row_count):
    """Compute Aroon for new rows.

    Uses numpy argmax/argmin for vectorized window operations.
    """
    n = len(highs)
    aroon_up = np.full(n, np.nan, dtype=float)
    aroon_down = np.full(n, np.nan, dtype=float)

    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)

    start_idx = max(period - 1, prev_row_count)
    for i in range(start_idx, n):
        window_start = i - period + 1
        # np.argmax/argmin return relative index within the slice
        rel_high = np.argmax(h[window_start:i + 1])
        rel_low = np.argmin(l[window_start:i + 1])
        days_since_high = i - (window_start + rel_high)
        days_since_low = i - (window_start + rel_low)
        aroon_up[i] = ((period - days_since_high) / period) * 100
        aroon_down[i] = ((period - days_since_low) / period) * 100

    return {
        "aroon_up": aroon_up.tolist(),
        "aroon_down": aroon_down.tolist(),
    }


def compute_donchian(highs, lows, period=20):
    """Compute Donchian Upper and Lower channels.

    Vectorized implementation: uses numpy rolling max/min via sliding
    window operations instead of Python loops.

    Donchian Upper = Highest High over the last `period` bars
    Donchian Lower = Lowest Low over the last `period` bars

    Returns dict with:
      - donchian_upper: list of upper channel values (resistance level)
      - donchian_lower: list of lower channel values (support level)

    First valid value at index ``period - 1`` (19 for period=20).
    """
    n = len(highs)
    donchian_upper = np.full(n, np.nan, dtype=float)
    donchian_lower = np.full(n, np.nan, dtype=float)

    if n < period:
        # Convert all np.nan to Python None for consistency with original
        return {
            "donchian_upper": [None] * n,
            "donchian_lower": [None] * n,
        }

    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)

    # Vectorized rolling max/min using stride tricks or manual approach
    # For each position i >= period-1, compute max/min of window[i-period+1:i+1]
    for i in range(period - 1, n):
        window_start = i - period + 1
        donchian_upper[i] = np.max(h[window_start:i + 1])
        donchian_lower[i] = np.min(l[window_start:i + 1])

    # Convert all np.nan to Python None for consistency with original
    return {
        "donchian_upper": [None if np.isnan(v) else float(v) for v in donchian_upper],
        "donchian_lower": [None if np.isnan(v) else float(v) for v in donchian_lower],
    }


def compute_donchian_incremental(highs, lows, period, prev_row_count):
    """Compute Donchian channels for new rows.

    Uses numpy max/min for vectorized window operations.
    """
    n = len(highs)
    donchian_upper = np.full(n, np.nan, dtype=float)
    donchian_lower = np.full(n, np.nan, dtype=float)

    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)

    start_idx = max(period - 1, prev_row_count)
    for i in range(start_idx, n):
        window_start = i - period + 1
        donchian_upper[i] = np.max(h[window_start:i + 1])
        donchian_lower[i] = np.min(l[window_start:i + 1])

    # Convert all np.nan to Python None for consistency with original
    return {
        "donchian_upper": [None if np.isnan(v) else float(v) for v in donchian_upper],
        "donchian_lower": [None if np.isnan(v) else float(v) for v in donchian_lower],
    }


def compute_keltner(highs, lows, closes, ema_period=20, atr_period=10, multiplier=2.0):
    """Compute Keltner Upper and Lower channels.

    Keltner Channels use ATR-based bands around an EMA of the typical price.
      - Typical Price (TP) = (High + Low + Close) / 3
      - Middle Line = EMA(TP, ema_period)
      - Upper Band = Middle + (multiplier × ATR)
      - Lower Band = Middle - (multiplier × ATR)

    Returns dict with:
      - keltner_upper: list of upper channel values (resistance)
      - keltner_lower: list of lower channel values (support)

    First valid value at index ``max(ema_period - 1, atr_period)``.
      For default params: max(19, 10) = 19.
    """
    n = len(highs)
    keltner_upper = [None] * n
    keltner_lower = [None] * n

    # Compute Typical Price
    tp = [(float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0 for i in range(n)]

    # Compute EMA of Typical Price
    ema_tp = compute_ema(tp, ema_period)

    # Compute ATR (using existing compute_atr with atr_period)
    atr_values = compute_atr(highs, lows, closes, atr_period)

    for i in range(n):
        if ema_tp[i] is not None and atr_values[i] is not None:
            keltner_upper[i] = ema_tp[i] + multiplier * atr_values[i]
            keltner_lower[i] = ema_tp[i] - multiplier * atr_values[i]

    return {
        "keltner_upper": keltner_upper,
        "keltner_lower": keltner_lower,
    }


def compute_keltner_incremental(highs, lows, closes, ema_period, atr_period, multiplier,
                                 prev_row_count, last_ema_tp, last_atr_values,
                                 boundary_start):
    """Compute Keltner channels for new rows continuing from previous state."""
    n = len(highs)
    keltner_upper = [None] * n
    keltner_lower = [None] * n

    # Compute Typical Price
    tp = [(float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0 for i in range(n)]

    # Compute EMA of TP for new rows
    ema_tp = [None] * n
    if last_ema_tp is not None:
        ema_tp_new = compute_ema_from_state(tp, ema_period, last_ema_tp, prev_row_count - 1)
        for i in range(prev_row_count, n):
            ema_tp[i] = ema_tp_new[i]

    # Compute ATR for new rows
    atr_values = [None] * n
    if last_atr_values is not None:
        atr_new = compute_atr_from_state(highs, lows, closes, atr_period,
                                          last_atr_values["last_tr"],
                                          last_atr_values["last_atr"],
                                          prev_row_count - 1)
        for i in range(prev_row_count, n):
            atr_values[i] = atr_new[i]

    # Also compute full for boundary region
    tp_boundary = [tp[i] for i in range(boundary_start, n)]
    ema_tp_full = compute_ema(tp_boundary, ema_period)
    atr_full = compute_atr(highs[boundary_start:], lows[boundary_start:],
                           closes[boundary_start:], atr_period)
    for i in range(boundary_start, n):
        ema_tp[i] = ema_tp_full[i - boundary_start]
        atr_values[i] = atr_full[i - boundary_start]

    for i in range(boundary_start, n):
        if ema_tp[i] is not None and atr_values[i] is not None:
            keltner_upper[i] = ema_tp[i] + multiplier * atr_values[i]
            keltner_lower[i] = ema_tp[i] - multiplier * atr_values[i]

    return {
        "keltner_upper": keltner_upper,
        "keltner_lower": keltner_lower,
    }


def compute_adx_di(highs, lows, closes, period=14):
    """Compute ADX, +DI, and -DI using Wilder's smoothing.

    Vectorized implementation: numpy for directional movement and
    true range computation.

    Returns dict with:
      - adx:       list of ADX values (trend strength 0-100)
      - plus_di:   list of +DI values (bullish directional movement)
      - minus_di:  list of -DI values (bearish directional movement)

    Index validity (period=14):
      +DI/-DI : first valid at index ``period`` (14)
      DX      : first valid at index ``period + 1`` (15)
      ADX     : initial at index ``period + 14`` (28), then smoothed
    """
    n = len(highs)
    adx = np.full(n, np.nan)
    plus_di = np.full(n, np.nan)
    minus_di = np.full(n, np.nan)

    if n < period + 1:
        return {"adx": [None] * n, "plus_di": [None] * n, "minus_di": [None] * n}

    h = np.asarray(highs, dtype=float)
    l = np.asarray(lows, dtype=float)
    c = np.asarray(closes, dtype=float)

    # --- Step 0: Directional movement (vectorized) ---
    up_move = h[1:] - h[:-1]
    down_move = l[:-1] - l[1:]

    plus_dm = np.zeros(n, dtype=float)
    minus_dm = np.zeros(n, dtype=float)

    plus_mask = (up_move > down_move) & (up_move > 0)
    minus_mask = (down_move > up_move) & (down_move > 0)
    plus_dm[1:] = np.where(plus_mask, up_move, 0)
    minus_dm[1:] = np.where(minus_mask, down_move, 0)

    # --- Step 1: True Range (vectorized) ---
    true_range = np.zeros(n, dtype=float)
    true_range[1:] = np.maximum(
        np.maximum(h[1:] - l[1:], np.abs(h[1:] - c[:-1])),
        np.abs(l[1:] - c[:-1]),
    )

    # --- Step 2: Wilder's smoothing (initial sum → recursive) ---
    k = 1.0 / period

    def _wilder_sum(values, start, end, period):
        """Initial sum of ``values[start:end]``, then recursive smoothing."""
        s = np.sum(values[start:end])
        out = np.zeros(len(values), dtype=float)
        out[end - 1] = s
        for i in range(end, len(values)):
            out[i] = out[i - 1] - out[i - 1] * k + values[i]
        return out

    smoothed_tr = _wilder_sum(true_range, 1, period + 1, period)
    smoothed_plus_dm = _wilder_sum(plus_dm, 1, period + 1, period)
    smoothed_minus_dm = _wilder_sum(minus_dm, 1, period + 1, period)

    # --- Step 3: +DI / -DI (first valid at index ``period``) ---
    valid_tr = smoothed_tr[period:] != 0
    plus_di[period:] = np.where(valid_tr, (smoothed_plus_dm[period:] / smoothed_tr[period:]) * 100, np.nan)
    minus_di[period:] = np.where(valid_tr, (smoothed_minus_dm[period:] / smoothed_tr[period:]) * 100, np.nan)

    # --- Step 4: DX (first valid at index ``period + 1``) ---
    dx_values = {}
    for i in range(period + 1, n):
        pdi = plus_di[i]
        mdi = minus_di[i]
        if np.isnan(pdi) or np.isnan(mdi):
            continue
        di_sum = pdi + mdi
        if di_sum == 0:
            continue
        dx_values[i] = (abs(pdi - mdi) / di_sum) * 100

    # --- Step 5: ADX ---
    init_dx_start = period + 1
    init_dx_end = period + 15
    init_idx = init_dx_end - 1

    for i in range(period + 1, n):
        if i not in dx_values:
            continue
        dx = dx_values[i]

        if i == init_idx:
            sum_dx = sum(dx_values[j] for j in range(init_dx_start, init_dx_end) if j in dx_values)
            count = sum(1 for j in range(init_dx_start, init_dx_end) if j in dx_values)
            if count > 0:
                adx[i] = sum_dx / count
        else:
            if not np.isnan(adx[i - 1]):
                adx[i] = adx[i - 1] * (1 - k) + dx * k

    # Convert all np.nan to Python None for consistency with original
    return {
        "adx": [None if np.isnan(v) else float(v) for v in adx],
        "plus_di": [None if np.isnan(v) else float(v) for v in plus_di],
        "minus_di": [None if np.isnan(v) else float(v) for v in minus_di],
    }


def compute_adx_di_incremental(highs, lows, closes, period, prev_row_count,
                                last_smoothed_tr, last_smoothed_plus_dm,
                                last_smoothed_minus_dm, last_adx,
                                boundary_start):
    """Compute ADX, +DI, -DI for new rows continuing from previous state.

    Wilder's smoothing requires state (previous smoothed values) to continue
    computing without full recalculation.
    """
    n = len(highs)
    adx = [None] * n
    plus_di = [None] * n
    minus_di = [None] * n

    if n < period + 1:
        return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}

    # --- Step 0: Directional movement (for boundary + new rows) ---
    k = 1.0 / period

    # Compute directional movement and true range for boundary region
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    true_range = [0.0] * n

    for i in range(max(1, boundary_start), n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]

        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move

        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_range[i] = tr

    # If we have previous smoothed values, continue from them
    if last_smoothed_tr is not None:
        # Continue Wilder's smoothing from prev_row_count - 1
        current_tr = last_smoothed_tr
        current_pdm = last_smoothed_plus_dm
        current_mdm = last_smoothed_minus_dm
        current_adx = last_adx

        for i in range(prev_row_count, n):
            current_tr = current_tr - current_tr * k + true_range[i]
            current_pdm = current_pdm - current_pdm * k + plus_dm[i]
            current_mdm = current_mdm - current_mdm * k + minus_dm[i]

            if current_tr > 0:
                plus_di[i] = (current_pdm / current_tr) * 100
                minus_di[i] = (current_mdm / current_tr) * 100

            # DX and ADX
            pdi = plus_di[i]
            mdi = minus_di[i]
            if pdi is not None and mdi is not None:
                di_sum = pdi + mdi
                if di_sum > 0:
                    dx = (abs(pdi - mdi) / di_sum) * 100
                    if current_adx is not None:
                        adx[i] = current_adx * (1 - k) + dx * k
                        current_adx = adx[i]

    return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}


def compute_price_dist_ma(closes, ma_values):
    """Compute percentage distance from price to a moving average.

    Vectorized implementation: uses numpy element-wise operations.

    dist = (close - MA) / MA * 100

    A positive value means price is above the MA; negative means below.

    Returns a list aligned with closes; ``None`` where MA is unavailable
    or zero.
    """
    n = len(closes)
    c = np.asarray(closes, dtype=float)
    m = np.asarray(ma_values, dtype=float)
    valid = ~np.isnan(m) & (m != 0) & ~np.isnan(c)
    result = np.where(valid, (c - m) / np.where(valid, m, 1.0) * 100, np.nan)
    # Convert all np.nan to Python None for consistency with original
    return [None if np.isnan(v) else float(v) for v in result]


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

    ta_price_dist_ema20 = compute_price_dist_ma(closes, ta_ema20)
    ta_price_dist_ema50 = compute_price_dist_ma(closes, ta_ema50)
    ta_price_dist_ema200 = compute_price_dist_ma(closes, ta_ema200)

    aroon = compute_aroon(highs, lows, period=25)
    adx_di = compute_adx_di(highs, lows, closes, period=14)
    donchian = compute_donchian(highs, lows, period=20)
    keltner = compute_keltner(highs, lows, closes)

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
        "ta_price_dist_ema20": ta_price_dist_ema20,
        "ta_price_dist_ema50": ta_price_dist_ema50,
        "ta_price_dist_ema200": ta_price_dist_ema200,
        "ta_aroon_up": aroon["aroon_up"],
        "ta_aroon_down": aroon["aroon_down"],
        "ta_adx14": adx_di["adx"],
        "ta_plus_di14": adx_di["plus_di"],
        "ta_minus_di14": adx_di["minus_di"],
        "ta_donchian_upper": donchian["donchian_upper"],
        "ta_donchian_lower": donchian["donchian_lower"],
        "ta_keltner_upper": keltner["keltner_upper"],
        "ta_keltner_lower": keltner["keltner_lower"],
    }


def compute_trend_columns_incremental(highs, lows, closes, n, prev_row_count,
                                       state, output_path=None):
    """Compute all trend indicator columns for new rows, continuing from previous state.

    This function computes indicators for rows starting from a boundary point
    (to handle lookback dependencies) and returns full-length lists aligned
    with all rows. Old values (before prev_row_count) are filled in from state.

    Parameters
    ----------
    highs, lows, closes : list
        Full OHLC data.
    n : int
        Total number of rows.
    prev_row_count : int
        Number of rows from the previous run.
    state : dict
        State dictionary from the previous run, containing:
        - ema20_last, ema50_last, ema200_last: last EMA values
        - ema20_last_idx, ema50_last_idx, ema200_last_idx: last EMA indices
        - atr_last_tr, atr_last_atr: ATR state
        - atr_last_idx: last ATR index
        - last_direction, last_upper_band, last_lower_band: SuperTrend state
        - last_ema_tp: EMA of typical price for Keltner
        - last_atr_values: ATR values for Keltner
        - last_smoothed_tr, last_smoothed_plus_dm, last_smoothed_minus_dm: ADX state
        - last_adx: last ADX value

    Returns
    -------
    dict
        All trend columns as full-length lists.
    """
    # Determine boundary: max lookback period for any indicator
    # SuperTrend: ATR(14) + band smoothing
    # ADX/DI: Wilder's smoothing with period=14
    # EMA: period=200 (longest)
    # Donchian/Aroon: period=25
    buffer = 250  # generous buffer for EMA200 dependency
    boundary_start = max(0, prev_row_count - buffer)

    # ---- EMA (incremental) ----
    ta_ema20 = [None] * n
    ta_ema50 = [None] * n
    ta_ema200 = [None] * n

    last_ema20 = state.get("ema20_last")
    last_ema50 = state.get("ema50_last")
    last_ema200 = state.get("ema200_last")
    last_idx20 = state.get("ema20_last_idx", prev_row_count - 1)
    last_idx50 = state.get("ema50_last_idx", prev_row_count - 1)
    last_idx200 = state.get("ema200_last_idx", prev_row_count - 1)

    if last_ema20 is not None:
        ta_ema20 = compute_ema_from_state(closes, 20, last_ema20, last_idx20)
    if last_ema50 is not None:
        ta_ema50 = compute_ema_from_state(closes, 50, last_ema50, last_idx50)
    if last_ema200 is not None:
        ta_ema200 = compute_ema_from_state(closes, 200, last_ema200, last_idx200)

    # SuperTrend (incremental)
    # Load existing direction for old rows from output file
    existing_direction = None
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        if "ta_supertrend_direction" in existing_df.columns:
            existing_direction = existing_df["ta_supertrend_direction"].tolist()

    st = compute_supertrend_incremental(
        highs, lows, closes, atr_period=14, multiplier=3.0,
        prev_row_count=prev_row_count,
        last_atr_values=None,
        last_direction=state.get("last_direction"),
        last_upper_band=state.get("last_upper_band"),
        last_lower_band=state.get("last_lower_band"),
        existing_direction=existing_direction,
    )

    # MA (lookback-based, compute for boundary + new rows)
    ta_ma20 = compute_ma(closes, 20)
    ta_ma50 = compute_ma(closes, 50)
    ta_sma10 = compute_ma(closes, 10)

    # MA slope (incremental with boundary)
    ta_ma20_slope = compute_ma_slope(closes, 20, lookback=10)
    ta_ma50_slope = compute_ma_slope(closes, 50, lookback=10)

    # Price/MA ratio and price/EMA distance (derived, compute for new rows)
    ta_price_ma20_ratio = [None] * n
    for i in range(prev_row_count, n):
        if ta_ma20[i] is not None and ta_ma20[i] != 0:
            ta_price_ma20_ratio[i] = closes[i] / ta_ma20[i]

    ta_price_dist_ema20 = compute_price_dist_ma(closes, ta_ema20)
    ta_price_dist_ema50 = compute_price_dist_ma(closes, ta_ema50)
    ta_price_dist_ema200 = compute_price_dist_ma(closes, ta_ema200)

    # Aroon (lookback-based, compute for new rows)
    aroon = compute_aroon_incremental(highs, lows, period=25,
                                       prev_row_count=prev_row_count)

    # ADX/DI (incremental with state)
    adx_di = compute_adx_di_incremental(
        highs, lows, closes, period=14, prev_row_count=prev_row_count,
        last_smoothed_tr=state.get("last_smoothed_tr"),
        last_smoothed_plus_dm=state.get("last_smoothed_plus_dm"),
        last_smoothed_minus_dm=state.get("last_smoothed_minus_dm"),
        last_adx=state.get("last_adx"),
        boundary_start=boundary_start,
    )

    # Donchian (lookback-based, compute for new rows)
    donchian = compute_donchian_incremental(highs, lows, period=20,
                                             prev_row_count=prev_row_count)

    # Keltner (incremental with EMA + ATR state)
    keltner = compute_keltner_incremental(
        highs, lows, closes, ema_period=20, atr_period=10, multiplier=2.0,
        prev_row_count=prev_row_count,
        last_ema_tp=state.get("last_ema_tp"),
        last_atr_values=state.get("last_atr_values"),
        boundary_start=boundary_start,
    )

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
        "ta_price_dist_ema20": ta_price_dist_ema20,
        "ta_price_dist_ema50": ta_price_dist_ema50,
        "ta_price_dist_ema200": ta_price_dist_ema200,
        "ta_aroon_up": aroon["aroon_up"],
        "ta_aroon_down": aroon["aroon_down"],
        "ta_adx14": adx_di["adx"],
        "ta_plus_di14": adx_di["plus_di"],
        "ta_minus_di14": adx_di["minus_di"],
        "ta_donchian_upper": donchian["donchian_upper"],
        "ta_donchian_lower": donchian["donchian_lower"],
        "ta_keltner_upper": keltner["keltner_upper"],
        "ta_keltner_lower": keltner["keltner_lower"],
    }


def process_csv(input_or_df, output_path, total_files, current_file, _lock=None):
    """Process a single ticker's OHLCV data into trend indicator output.

    Accepts either a pre-parsed DataFrame (from run_calculation.py shared cache)
    or a file path string (when called standalone via main()).

    Parameters
    ----------
    input_or_df : str or pd.DataFrame
        File path or pre-parsed DataFrame.
    output_path : str
        Path to write the trend indicator CSV.
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

    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()

    # Determine state file path (saved in state/ subdirectory)
    base = output_path.rsplit(".", 1)[0]
    state_dir = os.path.join(os.path.dirname(output_path), "state")
    os.makedirs(state_dir, exist_ok=True)
    state_path = os.path.join(state_dir, os.path.basename(base) + "_state.json")

    # Check for existing state
    state = load_state(state_path)

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

    # Skip incremental when force flag is set
    force_full = os.environ.get("TA_FORCE_FULL_RECALCULATION", "0") == "1"

    incremental = (
        not overwrite_today
        and not force_full
        and state is not None
        and state.get("_version") == 1
        and file_total > state.get("prev_row_count", 0)
    )

    if incremental:
        prev_row_count = state["prev_row_count"]

        # Compute only for new rows, merging with old
        new_cols = compute_trend_columns_incremental(
            highs, lows, closes, file_total, prev_row_count, state, output_path
        )

        # Build output with old + new
        df = pd.DataFrame({"Date": raw_df["Date"]})
        for col in new_cols:
            # Fill old values from existing output file
            if os.path.exists(output_path):
                existing_df = pd.read_csv(output_path)
                if col in existing_df.columns:
                    # Map old values by index
                    old_values = existing_df[col].tolist()
                    for i in range(prev_row_count):
                        if pd.notna(old_values[i]):
                            new_cols[col][i] = old_values[i]
            df[col] = new_cols[col]

        # Save state for next incremental run
        # Extract ADX/DI, ATR, and Keltner state from full data
        _adx_state = _get_adx_di_state(highs, lows, closes, 14)
        _atr_state = _get_atr_state(highs, lows, closes, 14)
        _tp = [(highs[i] + lows[i] + closes[i]) / 3.0 for i in range(file_total)]
        _ema_tp = compute_ema(_tp, 20)
        save_state({
            "_version": 1,
            "prev_row_count": file_total,
            "last_date": str(raw_df["Date"].iloc[-1]),
            "ema20_last": new_cols["ta_ema20"][-1] if new_cols["ta_ema20"][-1] is not None else None,
            "ema50_last": new_cols["ta_ema50"][-1] if new_cols["ta_ema50"][-1] is not None else None,
            "ema200_last": new_cols["ta_ema200"][-1] if new_cols["ta_ema200"][-1] is not None else None,
            "ema20_last_idx": file_total - 1,
            "ema50_last_idx": file_total - 1,
            "ema200_last_idx": file_total - 1,
            "last_direction": new_cols["ta_supertrend_direction"][-1] if new_cols["ta_supertrend_direction"][-1] is not None else None,
            "last_upper_band": new_cols["ta_supertrend_upper"][-1] if new_cols["ta_supertrend_upper"][-1] is not None else None,
            "last_lower_band": new_cols["ta_supertrend_lower"][-1] if new_cols["ta_supertrend_lower"][-1] is not None else None,
            "last_smoothed_tr": _adx_state["last_smoothed_tr"],
            "last_smoothed_plus_dm": _adx_state["last_smoothed_plus_dm"],
            "last_smoothed_minus_dm": _adx_state["last_smoothed_minus_dm"],
            "last_adx": _adx_state["last_adx"],
            "last_ema_tp": _ema_tp[-1] if _ema_tp[-1] is not None else None,
            "last_atr_values": {
                "last_tr": _atr_state["last_tr"],
                "last_atr": _atr_state["last_atr"],
            },
        }, state_path)
    else:
        # Full computation (first run or data shrank)
        trend_cols = compute_trend_columns(highs, lows, closes, file_total)

        # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
        df = pd.DataFrame({"Date": raw_df["Date"]})
        for col, values in trend_cols.items():
            df[col] = values

        # Save initial state
        _adx_state = _get_adx_di_state(highs, lows, closes, 14)
        _atr_state = _get_atr_state(highs, lows, closes, 14)
        if file_total > 0:
            _tp = [(highs[i] + lows[i] + closes[i]) / 3.0 for i in range(file_total)]
            _ema_tp = compute_ema(_tp, 20)
        else:
            _ema_tp = []
        save_state({
            "_version": 1,
            "prev_row_count": file_total,
            "last_date": str(raw_df["Date"].iloc[-1]) if file_total > 0 else "",
            "ema20_last": trend_cols["ta_ema20"][-1] if file_total > 0 and trend_cols["ta_ema20"][-1] is not None else None,
            "ema50_last": trend_cols["ta_ema50"][-1] if file_total > 0 and trend_cols["ta_ema50"][-1] is not None else None,
            "ema200_last": trend_cols["ta_ema200"][-1] if file_total > 0 and trend_cols["ta_ema200"][-1] is not None else None,
            "ema20_last_idx": file_total - 1 if file_total > 0 else 0,
            "ema50_last_idx": file_total - 1 if file_total > 0 else 0,
            "ema200_last_idx": file_total - 1 if file_total > 0 else 0,
            "last_direction": trend_cols["ta_supertrend_direction"][-1] if file_total > 0 and trend_cols["ta_supertrend_direction"][-1] is not None else None,
            "last_upper_band": trend_cols["ta_supertrend_upper"][-1] if file_total > 0 and trend_cols["ta_supertrend_upper"][-1] is not None else None,
            "last_lower_band": trend_cols["ta_supertrend_lower"][-1] if file_total > 0 and trend_cols["ta_supertrend_lower"][-1] is not None else None,
            "last_smoothed_tr": _adx_state["last_smoothed_tr"],
            "last_smoothed_plus_dm": _adx_state["last_smoothed_plus_dm"],
            "last_smoothed_minus_dm": _adx_state["last_smoothed_minus_dm"],
            "last_adx": _adx_state["last_adx"],
            "last_ema_tp": _ema_tp[-1] if _ema_tp and _ema_tp[-1] is not None else None,
            "last_atr_values": {
                "last_tr": _atr_state["last_tr"],
                "last_atr": _atr_state["last_atr"],
            },
        }, state_path)

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_trend",
    description="trend indicators: EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA ratio, price/EMA distance, Aroon, ADX/DI, Donchian, Keltner",
    process_csv_fn=process_csv,
)

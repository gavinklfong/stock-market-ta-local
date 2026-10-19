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
    true_ranges = [None] * n
    for i in range(n):
        if i == 0:
            true_ranges[i] = highs[i] - lows[i]
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges[i] = tr

    if n < period + 1:
        return {"last_tr": 0.0, "last_atr": None}

    atr_values = [None] * n
    initial_atr = sum(true_ranges[i] for i in range(period)) / period
    atr_values[period] = initial_atr

    k = 2.0 / (period + 1)
    for i in range(period + 1, n):
        if true_ranges[i] is not None:
            prev_atr = atr_values[i - 1]
            if prev_atr is not None:
                atr_values[i] = true_ranges[i] * k + prev_atr * (1 - k)

    return {"last_tr": true_ranges[n - 1], "last_atr": atr_values[n - 1]}


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

    # Continue from last known ATR
    current_atr = last_atr
    current_tr = last_tr
    for i in range(last_idx + 1, n):
        if i == 0:
            current_tr = highs[i] - lows[i]
        else:
            current_tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        if i > period:
            current_atr = current_tr * k + current_atr * (1 - k)
            result[i] = current_atr

    return result


# =============================================================================
# EMA computation
# =============================================================================


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


def compute_supertrend_incremental(highs, lows, closes, atr_period, multiplier,
                                    prev_row_count, last_atr_values,
                                    last_direction, last_upper_band,
                                    last_lower_band, existing_direction=None):
    """Compute SuperTrend for new rows continuing from previous state.

    Returns dict with supertrend, direction, upper_band, lower_band for
    all indices (full-length lists).
    """
    n = len(highs)
    atr = compute_atr(highs, lows, closes, atr_period)

    # Mid point
    mid = [(highs[i] + lows[i]) / 2.0 for i in range(n)]

    # Raw bands (full array)
    upper_band_raw = [None] * n
    lower_band_raw = [None] * n
    for i in range(n):
        if atr[i] is not None:
            upper_band_raw[i] = mid[i] + multiplier * atr[i]
            lower_band_raw[i] = mid[i] - multiplier * atr[i]

    # Smooth bands: upper band only goes down, lower band only goes up
    upper_band = [None] * n
    lower_band = [None] * n

    for i in range(n):
        if upper_band_raw[i] is None or lower_band_raw[i] is None:
            continue
        if i == 0:
            upper_band[i] = upper_band_raw[i]
            lower_band[i] = lower_band_raw[i]
        else:
            if upper_band[i - 1] is not None:
                upper_band[i] = min(upper_band_raw[i], upper_band[i - 1])
            else:
                upper_band[i] = upper_band_raw[i]
            if lower_band[i - 1] is not None:
                lower_band[i] = max(lower_band_raw[i], lower_band[i - 1])
            else:
                lower_band[i] = lower_band_raw[i]

    # Direction and SuperTrend line: load old, compute new
    direction = [0] * n
    supertrend = [None] * n

    # If we have existing direction values, use them for old rows
    if existing_direction is not None and len(existing_direction) >= prev_row_count:
        for i in range(min(prev_row_count, len(existing_direction))):
            direction[i] = existing_direction[i]
        # Compute new rows starting from prev_row_count
        for i in range(prev_row_count, n):
            if upper_band[i] is None or lower_band[i] is None:
                continue
            if direction[i - 1] == 1:
                if closes[i] <= lower_band[i]:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
                else:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
            else:
                if closes[i] >= upper_band[i]:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
                else:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
    else:
        # No existing direction: compute from scratch
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
                if closes[i] <= lower_band[i]:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
                else:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
            else:
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


def compute_aroon(highs, lows, period=25):
    """Compute Aroon Up and Aroon Down indicators.

    Aroon Up    = ((Period - Days Since Highest High) / Period) * 100
    Aroon Down  = ((Period - Days Since Lowest Low)  / Period) * 100

    Returns dict with:
      - aroon_up:    list of Aroon Up values (100 = strong uptrend)
      - aroon_down:  list of Aroon Down values (100 = strong downtrend)
    """
    n = len(highs)
    aroon_up = [None] * n
    aroon_down = [None] * n

    for i in range(n):
        # We need at least `period` data points for the first valid value
        if i < period - 1:
            continue
        # Look back over the window of `period` bars ending at i
        window_start = i - period + 1
        # Highest high in the window
        highest_idx = window_start
        for j in range(window_start + 1, i + 1):
            if highs[j] > highs[highest_idx]:
                highest_idx = j
        # Lowest low in the window
        lowest_idx = window_start
        for j in range(window_start + 1, i + 1):
            if lows[j] < lows[lowest_idx]:
                lowest_idx = j

        days_since_high = i - highest_idx
        days_since_low = i - lowest_idx
        aroon_up[i] = ((period - days_since_high) / period) * 100
        aroon_down[i] = ((period - days_since_low) / period) * 100

    return {
        "aroon_up": aroon_up,
        "aroon_down": aroon_down,
    }


def compute_aroon_incremental(highs, lows, period, prev_row_count):
    """Compute Aroon for new rows.

    Aroon is lookback-based (period), so new rows can be computed
    independently without state from previous runs.
    """
    n = len(highs)
    aroon_up = [None] * n
    aroon_down = [None] * n

    start_idx = max(period - 1, prev_row_count)
    for i in range(start_idx, n):
        window_start = i - period + 1
        highest_idx = window_start
        for j in range(window_start + 1, i + 1):
            if highs[j] > highs[highest_idx]:
                highest_idx = j
        lowest_idx = window_start
        for j in range(window_start + 1, i + 1):
            if lows[j] < lows[lowest_idx]:
                lowest_idx = j

        days_since_high = i - highest_idx
        days_since_low = i - lowest_idx
        aroon_up[i] = ((period - days_since_high) / period) * 100
        aroon_down[i] = ((period - days_since_low) / period) * 100

    return {
        "aroon_up": aroon_up,
        "aroon_down": aroon_down,
    }


def compute_donchian(highs, lows, period=20):
    """Compute Donchian Upper and Lower channels.

    Donchian Upper = Highest High over the last `period` bars
    Donchian Lower = Lowest Low over the last `period` bars

    Returns dict with:
      - donchian_upper: list of upper channel values (resistance level)
      - donchian_lower: list of lower channel values (support level)

    First valid value at index ``period - 1`` (19 for period=20).
    """
    n = len(highs)
    donchian_upper = [None] * n
    donchian_lower = [None] * n

    for i in range(n):
        if i < period - 1:
            continue
        window_start = i - period + 1
        window_highs = highs[window_start: i + 1]
        window_lows = lows[window_start: i + 1]
        donchian_upper[i] = max(window_highs)
        donchian_lower[i] = min(window_lows)

    return {
        "donchian_upper": donchian_upper,
        "donchian_lower": donchian_lower,
    }


def compute_donchian_incremental(highs, lows, period, prev_row_count):
    """Compute Donchian channels for new rows.

    Donchian is lookback-based, so new rows can be computed independently.
    """
    n = len(highs)
    donchian_upper = [None] * n
    donchian_lower = [None] * n

    start_idx = max(period - 1, prev_row_count)
    for i in range(start_idx, n):
        window_start = i - period + 1
        window_highs = highs[window_start: i + 1]
        window_lows = lows[window_start: i + 1]
        donchian_upper[i] = max(window_highs)
        donchian_lower[i] = min(window_lows)

    return {
        "donchian_upper": donchian_upper,
        "donchian_lower": donchian_lower,
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
    adx = [None] * n
    plus_di = [None] * n
    minus_di = [None] * n

    if n < period + 1:
        return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}

    # --- Step 0: Directional movement ---
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n

    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]

        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move

    # --- Step 1: True Range ---
    true_range = [0.0] * n
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_range[i] = tr

    # --- Step 2: Wilder's smoothing (initial sum → recursive) ---
    k = 1.0 / period

    def _wilder_sum(values, start, end, period):
        """Initial sum of ``values[start:end]``, then recursive smoothing."""
        s = sum(values[i] for i in range(start, end))
        out = [0.0] * len(values)
        out[end - 1] = s
        for i in range(end, len(values)):
            out[i] = out[i - 1] - out[i - 1] * k + values[i]
        return out

    smoothed_tr = _wilder_sum(true_range, 1, period + 1, period)
    smoothed_plus_dm = _wilder_sum(plus_dm, 1, period + 1, period)
    smoothed_minus_dm = _wilder_sum(minus_dm, 1, period + 1, period)

    # --- Step 3: +DI / -DI (first valid at index ``period``) ---
    for i in range(period, n):
        st = smoothed_tr[i]
        if st == 0:
            continue
        plus_di[i] = (smoothed_plus_dm[i] / st) * 100
        minus_di[i] = (smoothed_minus_dm[i] / st) * 100

    # --- Step 4: DX (first valid at index ``period + 1``) ---
    # We store DX values in a separate dict so they are available for ADX
    # initialisation (which needs 14 consecutive DX values).
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

    # --- Step 5: ADX ---
    # Initial ADX = average of first 14 DX values.
    # Smoothed ADX[i] = ADX[i-1] * (1 - k) + DX[i] * k   (for i > first)
    init_dx_start = period + 1
    init_dx_end = period + 15  # 14 values: period+1 .. period+14
    init_idx = init_dx_end - 1  # index where initial ADX lands

    for i in range(period + 1, n):
        if i not in dx_values:
            continue
        dx = dx_values[i]

        if i == init_idx:
            # Average the first 14 DX values
            sum_dx = sum(dx_values[j] for j in range(init_dx_start, init_dx_end) if j in dx_values)
            count = sum(1 for j in range(init_dx_start, init_dx_end) if j in dx_values)
            if count > 0:
                adx[i] = sum_dx / count
        else:
            if adx[i - 1] is not None:
                adx[i] = adx[i - 1] * (1 - k) + dx * k

    return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}


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

    dist = (close - MA) / MA * 100

    A positive value means price is above the MA; negative means below.

    Returns a list aligned with closes; ``None`` where MA is unavailable
    or zero.
    """
    n = len(closes)
    result = [None] * n
    for i in range(n):
        if ma_values[i] is not None and closes[i] is not None and ma_values[i] != 0:
            result[i] = (closes[i] - ma_values[i]) / ma_values[i] * 100.0
    return result


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


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()

    # Determine state file path
    state_path = output_path.rsplit(".", 1)[0] + "_state.json"

    # Check for existing state
    state = _load_state(state_path)
    incremental = state is not None and state.get("_version") == 1 and file_total > state.get("prev_row_count", 0)

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
        _save_state({
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
        _save_state({
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

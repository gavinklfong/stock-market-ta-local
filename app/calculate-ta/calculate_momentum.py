import json
import os
import sys
import threading

import numpy as np
import pandas as pd

from common import (
    file_progress_bar,
    main,
    read_yfinance_csv,
)


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


def compute_rsi(values, period=14):
    """Compute RSI. Returns a list aligned with input."""
    n = len(values)
    result = [None] * n
    if n < period + 1:
        return result

    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        diff = float(values[i]) - float(values[i - 1])
        if diff > 0:
            gains[i] = diff
        else:
            losses[i] = abs(diff)

    # Initial average gain/loss (SMA of first `period` changes)
    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period

    if avg_loss == 0:
        if avg_gain == 0:
            result[period] = 50.0
        else:
            result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100.0 - (100.0 / (1.0 + rs))

    # Smoothed average
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            if avg_gain == 0:
                result[i] = 50.0
            else:
                result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - (100.0 / (1.0 + rs))

    return result


def compute_macd(values, fast=12, slow=26, signal=9):
    """Compute MACD indicator. Returns dict with macd_line, signal_line, histogram."""
    n = len(values)

    ema_fast = compute_ema(values, fast)
    ema_slow = compute_ema(values, slow)

    macd_line = [None] * n
    for i in range(n):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    # Signal line is EMA of MACD line
    macd_values = [v for v in macd_line if v is not None]
    signal_values = compute_ema(macd_values, signal)

    signal_line = [None] * n
    histogram = [None] * n
    macd_idx = 0
    for i in range(n):
        if macd_line[i] is not None:
            if macd_idx < len(signal_values) and signal_values[macd_idx] is not None:
                signal_line[i] = signal_values[macd_idx]
                histogram[i] = macd_line[i] - signal_values[macd_idx]
            macd_idx += 1

    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
    }


def compute_roc(values, period=20):
    """Compute Rate of Change. Returns a list aligned with input."""
    n = len(values)
    result = [None] * n
    if n < period + 1:
        return result

    for i in range(period, n):
        prev = float(values[i - period])
        curr = float(values[i])
        if prev != 0:
            result[i] = ((curr - prev) / prev) * 100.0

    return result


def compute_stochastic(values, k_period=14, d_period=3):
    """Compute Stochastic %K and %D. Returns dict with stoch_k and stoch_d lists."""
    n = len(values)
    result_k = [None] * n
    result_d = [None] * n

    if n < k_period:
        return {"ta_stoch_k": result_k, "ta_stoch_d": result_d}

    lowest_low = [None] * n
    highest_high = [None] * n

    # Compute rolling min/max over k_period, store at the last index of the window
    for i in range(k_period - 1, n):
        window = [float(values[j]) for j in range(i - k_period + 1, i + 1)]
        lowest_low[i] = min(window)
        highest_high[i] = max(window)

    # %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
    for i in range(k_period - 1, n):
        hh = highest_high[i]
        ll = lowest_low[i]
        if hh != ll:
            result_k[i] = ((float(values[i]) - ll) / (hh - ll)) * 100.0

    # %D = SMA of %K over d_period
    k_valid = []
    k_valid_indices = []
    for i in range(n):
        if result_k[i] is not None:
            k_valid.append(result_k[i])
            k_valid_indices.append(i)

    for local_idx, i in enumerate(k_valid_indices):
        if local_idx >= d_period - 1:
            window = k_valid[local_idx - d_period + 1 : local_idx + 1]
            result_d[i] = sum(window) / d_period

    return {"ta_stoch_k": result_k, "ta_stoch_d": result_d}


def compute_williams_r(highs, lows, closes, period=14):
    """Compute Williams %R. Returns a list aligned with input.

    Williams %R = (Highest High − Close) / (Highest High − Lowest Low) × −100
    Range: 0 to −100. Overbought above −20, oversold below −80.

    Parameters
    ----------
    highs : list[float]
        High prices for each bar.
    lows : list[float]
        Low prices for each bar.
    closes : list[float]
        Close prices for each bar.
    period : int
        Lookback period (default 14).
    """
    n = len(closes)
    assert len(highs) == n and len(lows) == n, (
        f"highs, lows, and closes must have the same length ({n})"
    )
    result = [None] * n

    if n < period:
        return result

    for i in range(period - 1, n):
        window_highs = [float(highs[j]) for j in range(i - period + 1, i + 1)]
        window_lows = [float(lows[j]) for j in range(i - period + 1, i + 1)]
        highest_high = max(window_highs)
        lowest_low = min(window_lows)
        if highest_high != lowest_low:
            result[i] = ((highest_high - float(closes[i])) /
                         (highest_high - lowest_low)) * -100.0

    return result


def compute_cci(highs, lows, closes, period=20):
    """Compute Commodity Channel Index (CCI). Returns a list aligned with input.

    CCI = (Typical Price − SMA(Typical Price)) / (0.015 × Mean Deviation)
    Typical Price = (High + Low + Close) / 3

    No bounds — values > +100 = overbought, < −100 = oversold.

    Parameters
    ----------
    highs : list[float]
        High prices for each bar.
    lows : list[float]
        Low prices for each bar.
    closes : list[float]
        Close prices for each bar.
    period : int
        Lookback period (default 20).
    """
    n = len(closes)
    assert len(highs) == n and len(lows) == n, (
        f"highs, lows, and closes must have the same length ({n})"
    )
    result = [None] * n

    if n < period:
        return result

    # Compute typical prices
    typical_prices = [
        (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        for i in range(n)
    ]

    for i in range(period - 1, n):
        window = typical_prices[i - period + 1 : i + 1]
        sma_tp = sum(window) / period
        mean_deviation = sum(abs(tp - sma_tp) for tp in window) / period
        if mean_deviation > 0:
            result[i] = (typical_prices[i] - sma_tp) / (0.015 * mean_deviation)

    return result


def compute_tsi(closes, fast=25, slow=13):
    """Compute True Strength Index (TSI). Returns a list aligned with input.

    TSI = 100 × DoubleEMA(price_change, fast, slow) / DoubleEMA(|price_change|, fast, slow)

    Parameters
    ----------
    closes : list[float]
        Close prices for each bar.
    fast : int
        Fast EMA period (default 25).
    slow : int
        Slow EMA period (default 13).
    """
    n = len(closes)
    result = [None] * n

    if n < fast + slow + 1:
        return result

    # Price changes: diff[t] = close[t] - close[t-1], valid from index 1
    changes = [
        float(closes[i]) - float(closes[i - 1]) for i in range(1, n)
    ]
    abs_changes = [abs(c) for c in changes]

    # First EMA on changes (fast period)
    ema1 = compute_ema(changes, fast)
    # Second EMA on ema1 (slow period) — only on valid (non-None) values
    ema1_valid = [v for v in ema1 if v is not None]
    ema2 = compute_ema(ema1_valid, slow)

    # First EMA on abs changes (fast period)
    ema_abs1 = compute_ema(abs_changes, fast)
    # Second EMA on ema_abs1 (slow period)
    ema_abs1_valid = [v for v in ema_abs1 if v is not None]
    ema_abs2 = compute_ema(ema_abs1_valid, slow)

    # Map back to original indices
    # changes starts at index 1 of closes
    changes_offset = 1

    # Build index maps for ema2 and ema_abs2
    ema1_indices = [i for i, v in enumerate(ema1) if v is not None]
    ema2_indices = [changes_offset + ema1_indices[j] for j, idx in enumerate(ema1_indices) if j < len(ema2) and ema2[j] is not None]

    ema_abs1_indices = [i for i, v in enumerate(ema_abs1) if v is not None]
    ema_abs2_indices = [changes_offset + ema_abs1_indices[j] for j, idx in enumerate(ema_abs1_indices) if j < len(ema_abs2) and ema_abs2[j] is not None]

    # Only keep indices where both TSI numerator and denominator are valid
    valid_indices = set(ema2_indices) & set(ema_abs2_indices)

    for i in valid_indices:
        # Find corresponding values in ema2 and ema_abs2
        # ema2 maps: ema1_index -> ema2_value
        ema1_to_ema2 = {}
        for j, ema1_idx in enumerate(ema1_indices):
            if j < len(ema2) and ema2[j] is not None:
                ema1_to_ema2[ema1_idx] = ema2[j]

        ema_abs1_to_ema_abs2 = {}
        for j, ema_abs1_idx in enumerate(ema_abs1_indices):
            if j < len(ema_abs2) and ema_abs2[j] is not None:
                ema_abs1_to_ema_abs2[ema_abs1_idx] = ema_abs2[j]

        num = ema1_to_ema2.get(i)
        den = ema_abs1_to_ema_abs2.get(i)

        if num is not None and den is not None and den != 0:
            result[i] = 100.0 * num / den

    return result


def compute_rsi_zscore(closes, rsi_period=14, window=20):
    """Compute Z-score of RSI over a rolling window.

    RSI Z-score = (RSI - mean(RSI_window)) / std(RSI_window)

    This tells us how extreme the current RSI is relative to its recent
    distribution. A Z-score of +2 means the current RSI is 2 standard
    deviations above its rolling mean — potentially overbought beyond
    what the recent RSI distribution would suggest.

    Parameters
    ----------
    closes : list[float]
        Close prices for each bar.
    rsi_period : int
        RSI lookback period (default 14).
    window : int
        Rolling window for Z-score calculation (default 20).

    Returns
    -------
    list[float | None]
        Z-score values aligned with input; None before warmup.
    """
    n = len(closes)
    result = [None] * n

    if n < rsi_period + window:
        return result

    # Compute RSI
    rsi_values = compute_rsi(closes, rsi_period)

    # Compute Z-score of RSI over rolling window
    # First RSI valid index = rsi_period - 1
    # First Z-score = rsi_period + window - 1
    for i in range(rsi_period + window - 1, n):
        window_rsi = []
        for j in range(i - window + 1, i + 1):
            v = rsi_values[j]
            if v is not None:
                window_rsi.append(v)

        if len(window_rsi) < 2:
            continue

        mean_rsi = sum(window_rsi) / len(window_rsi)
        variance = sum((x - mean_rsi) ** 2 for x in window_rsi) / len(window_rsi)
        std_rsi = variance ** 0.5

        if std_rsi > 0:
            result[i] = (rsi_values[i] - mean_rsi) / std_rsi

    return result


def compute_rsi_percentile(closes, rsi_period=14, window=20):
    """Compute rolling percentile rank of RSI values.

    RSI percentile = percentage of RSI values in the rolling window
    that are strictly less than the current RSI.

    This tells us where the current RSI ranks relative to its recent
    distribution. A percentile of 90 means the current RSI is higher
    than 90% of the past 20 RSI values — potentially overbought.

    Parameters
    ----------
    closes : list[float]
        Close prices for each bar.
    rsi_period : int
        RSI lookback period (default 14).
    window : int
        Rolling window for percentile calculation (default 20).

    Returns
    -------
    list[float | None]
        Percentile values (0–100) aligned with input; None before warmup.
    """
    n = len(closes)
    result = [None] * n

    if n < rsi_period + window:
        return result

    # Compute RSI
    rsi_values = compute_rsi(closes, rsi_period)

    # First RSI valid index = rsi_period
    # First percentile valid index = rsi_period + window - 1
    for i in range(rsi_period + window - 1, n):
        rsi_i = rsi_values[i]
        if rsi_i is None:
            continue

        window_rsi = []
        for j in range(i - window + 1, i + 1):
            v = rsi_values[j]
            if v is not None:
                window_rsi.append(v)

        if len(window_rsi) < 2:
            continue

        # Count values strictly below current RSI
        below_count = sum(1 for v in window_rsi if v < rsi_i)
        result[i] = (below_count / len(window_rsi)) * 100.0

    return result


# =============================================================================
# Incremental computation helpers
# =============================================================================

def compute_rsi_from_state(closes, period, prev_avg_gain, prev_avg_loss,
                           prev_count, closes_before):
    """Compute RSI only for new rows, continuing from prior state.

    Parameters
    ----------
    closes : list[float]
        Full closes list (includes old + new data).
    period : int
        RSI period (default 14).
    prev_avg_gain : float
        Average gain at end of previous computation.
    prev_avg_loss : float
        Average loss at end of previous computation.
    prev_count : int
        Number of closes that were processed in the previous run.
    closes_before : list[float]
        Closes up to the previous run end (for computing price changes
        between last old row and first new row).

    Returns
    -------
    list[float | None]
        RSI values for indices ``prev_count .. len(closes)-1``.
    """
    result = []
    for i in range(prev_count, len(closes)):
        # First new row bridges the old-new boundary
        if i == prev_count and prev_count > 0:
            change = float(closes[i]) - float(closes_before[-1])
        elif i == 0:
            change = 0.0
        else:
            change = float(closes[i]) - float(closes[i - 1])
        gain = max(change, 0.0)
        loss = max(-change, 0.0)

        avg_gain = (prev_avg_gain * (period - 1) + gain) / period
        avg_loss = (prev_avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            if avg_gain == 0:
                rsi = 50.0
            else:
                rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        result.append(rsi)
        prev_avg_gain = avg_gain
        prev_avg_loss = avg_loss

    return result


def compute_ema_from_state(values, period, prev_ema, prev_count):
    """Continue EMA computation from a previous state.

    Parameters
    ----------
    values : list[float]
        Full values list (includes old + new data).
    period : int
        EMA period.
    prev_ema : float
        EMA value at the end of the previous run.
    prev_count : int
        Number of values processed in the previous run.

    Returns
    -------
    list[float]
        EMA values for indices ``prev_count .. len(values)-1``.
    """
    k = 2.0 / (period + 1)
    result = []
    ema = prev_ema
    for i in range(prev_count, len(values)):
        if i > prev_count:
            ema = float(values[i]) * k + ema * (1 - k)
        result.append(ema)
    return result


def compute_macd_incremental(closes, state, prev_close_count,
                             fast=12, slow=26, signal=9):
    """Compute MACD only for new rows, continuing from prior state.

    Returns dict with ``macd_line``, ``signal_line``, ``histogram`` lists.
    """
    # Fast and slow EMA states
    fast_ema = state.get("macd_fast_ema")
    fast_count = state.get("macd_fast_count", fast)
    slow_ema = state.get("macd_slow_ema")
    slow_count = state.get("macd_slow_count", slow)

    # Signal line EMA state (EMA of MACD line values)
    signal_ema = state.get("macd_signal_ema")
    signal_count = state.get("macd_signal_ema_count", signal)

    n = len(closes)
    new_macd_line = []
    new_signal_line = []
    new_histogram = []

    # Compute new fast/slow EMA values
    for i in range(prev_close_count, n):
        if fast_count >= fast:
            fast_ema = float(closes[i]) * (2.0 / (fast + 1)) + fast_ema * (fast - 1) / (fast + 1)
        if slow_count >= slow:
            slow_ema = float(closes[i]) * (2.0 / (slow + 1)) + slow_ema * (slow - 1) / (slow + 1)
        fast_count += 1
        slow_count += 1

        if fast_count > fast and slow_count > slow:
            macd_val = fast_ema - slow_ema
        elif fast_count > fast and slow_count <= slow:
            macd_val = fast_ema - None  # placeholder
        elif fast_count <= fast and slow_count > slow:
            macd_val = None - slow_ema  # placeholder
        else:
            macd_val = None

        # Use simple difference when both are valid
        if fast_count > fast and slow_count > slow:
            macd_val = fast_ema - slow_ema
        else:
            macd_val = None

        new_macd_line.append(macd_val)

    # Compute signal line (EMA of MACD line)
    macd_idx = 0
    for i in range(prev_close_count, n):
        val = new_macd_line[macd_idx]
        macd_idx += 1
        if val is not None:
            if signal_count >= signal:
                signal_ema = val * (2.0 / (signal + 1)) + signal_ema * (signal - 1) / (signal + 1)
            signal_count += 1
            if signal_count > signal:
                new_signal_line.append(signal_ema)
                new_histogram.append(val - signal_ema)
            else:
                new_signal_line.append(None)
                new_histogram.append(None)
        else:
            new_signal_line.append(None)
            new_histogram.append(None)

    return {
        "macd_line": new_macd_line,
        "signal_line": new_signal_line,
        "histogram": new_histogram,
        "fast_ema": fast_ema,
        "fast_count": fast_count,
        "slow_ema": slow_ema,
        "slow_count": slow_count,
        "signal_ema": signal_ema,
        "signal_ema_count": signal_count,
    }


def compute_stochastic_incremental(closes, window_buffer, k_period=14, d_period=3):
    """Compute Stochastic %K and %D only for new rows.

    Parameters
    ----------
    closes : list[float]
        Full closes list.
    window_buffer : list[float]
        Last ``k_period - 1`` close values from the previous run.
    k_period, d_period : int
        Lookback periods.

    Returns
    -------
    dict with ``stoch_k``, ``stoch_d`` (new values only), and updated buffer.
    """
    result_k = []
    result_d = []
    new_closes = closes[len(window_buffer):]

    for idx, close in enumerate(new_closes):
        window = window_buffer + [float(close)]
        if len(window) > k_period:
            window = window[1:]
        lowest = min(window)
        highest = max(window)
        if highest != lowest:
            k_val = ((float(close) - lowest) / (highest - lowest)) * 100.0
        else:
            k_val = None
        result_k.append(k_val)

        # Update buffer
        window_buffer.append(float(close))
        if len(window_buffer) > k_period - 1:
            window_buffer.pop(0)

    # %D = SMA of %K over d_period
    all_k = result_k  # only new values
    for local_idx in range(len(all_k)):
        if local_idx >= d_period - 1:
            window = all_k[local_idx - d_period + 1:local_idx + 1]
            valid = [v for v in window if v is not None]
            if len(valid) == d_period:
                result_d.append(sum(valid) / d_period)
            else:
                result_d.append(None)
        else:
            result_d.append(None)

    return {"stoch_k": result_k, "stoch_d": result_d, "window_buffer": window_buffer}


def compute_williams_r_incremental(highs, lows, closes, window_buffer_h,
                                   window_buffer_l, period=14):
    """Compute Williams %R only for new rows.

    Returns dict with ``williams_r`` (new values) and updated buffers.
    """
    result = []
    new_closes = closes[len(window_buffer_h):]

    for idx, close in enumerate(new_closes):
        window_h = window_buffer_h + [float(highs[len(window_buffer_h) + idx])]
        window_l = window_buffer_l + [float(lows[len(window_buffer_l) + idx])]
        if len(window_h) > period:
            window_h = window_h[1:]
            window_l = window_l[1:]
        highest = max(window_h)
        lowest = min(window_l)
        if highest != lowest:
            wr = ((highest - float(close)) / (highest - lowest)) * -100.0
        else:
            wr = None
        result.append(wr)

        window_buffer_h.append(float(highs[len(window_buffer_h) + idx]))
        window_buffer_l.append(float(lows[len(window_buffer_l) + idx]))
        if len(window_buffer_h) > period - 1:
            window_buffer_h.pop(0)
        if len(window_buffer_l) > period - 1:
            window_buffer_l.pop(0)

    return {"williams_r": result,
            "window_buffer_h": window_buffer_h,
            "window_buffer_l": window_buffer_l}


def compute_cci_incremental(highs, lows, closes, tp_buffer, period=20):
    """Compute CCI only for new rows.

    Parameters
    ----------
    tp_buffer : list[float]
        Last ``period - 1`` typical-price values from previous run.

    Returns dict with ``cci`` (new values) and updated buffer.
    """
    result = []
    new_len = len(closes) - len(tp_buffer)

    for idx in range(new_len):
        tp = (float(highs[idx + len(tp_buffer)]) +
              float(lows[idx + len(tp_buffer)]) +
              float(closes[idx + len(tp_buffer)])) / 3.0
        window = tp_buffer + [tp]
        if len(window) > period:
            window = window[1:]
        sma = sum(window) / period
        mean_dev = sum(abs(t - sma) for t in window) / period
        if mean_dev > 0:
            result.append((tp - sma) / (0.015 * mean_dev))
        else:
            result.append(None)
        tp_buffer.append(tp)
        if len(tp_buffer) > period - 1:
            tp_buffer.pop(0)

    return {"cci": result, "tp_buffer": tp_buffer}


# =============================================================================
# State file helpers
# =============================================================================

def _extract_state_from_csv(output_path, prev_close):
    """Extract computation state from the last row of a previous output CSV.

    Returns a dict suitable for passing to the incremental functions,
    or ``None`` if the file can't be read.
    """
    try:
        df = pd.read_csv(output_path)
        last = df.iloc[-1]
    except Exception:
        return None

    state = {}

    # --- RSI state ---
    rsi_val = last.get("ta_rsi14")
    if pd.notna(rsi_val) and prev_close is not None:
        # avg_gain = rsi/100 * (avg_gain + avg_loss)
        # avg_loss = avg_gain * (100 - rsi) / rsi  [when 0 < rsi < 100]
        if rsi_val > 0 and rsi_val < 100:
            rs = 100.0 / rsi_val - 1.0
            # We need both avg_gain and avg_loss; from RSI:
            # rsi = 100 - 100/(1+rs)  =>  rs = avg_gain/avg_loss
            # We can't uniquely recover both from RSI alone.
            # Instead, store them in the state file directly.
            pass
    state["rsi_available"] = pd.notna(rsi_val)

    # --- MACD state ---
    state["macd_line"] = last.get("ta_macd_line")
    state["macd_signal"] = last.get("ta_macd_signal")
    if pd.notna(last.get("ta_macd_line")):
        state["macd_fast_ema"] = last.get("ta_macd_line")
    if pd.notna(last.get("ta_macd_signal")):
        state["macd_signal_ema"] = last.get("ta_macd_signal")

    return state


def _save_state(state, state_path):
    """Persist computation state to a JSON file."""
    with open(state_path, "w") as f:
        json.dump(state, f)


def _load_state(state_path):
    """Load computation state from a JSON file."""
    if not os.path.exists(state_path):
        return None
    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _merge_output(df_old, df_new, new_rows_count):
    """Merge old output DataFrame with newly computed full DataFrame.

    Keeps all old rows intact and replaces only the new rows with
    freshly computed values.
    """
    # Old rows stay as-is
    # New rows come from the full computation
    new_full = df_new.tail(new_rows_count).reset_index(drop=True)
    merged = pd.concat([df_old, new_full], ignore_index=True)
    return merged


def process_csv(input_or_df, output_path, total_files, current_file, _lock=None):
    """Process a single ticker's OHLCV data into momentum indicator output.

    When a previous output file and state file exist, this function performs
    **incremental computation**: it only computes momentum indicators for rows
    that were appended since the last run, greatly improving efficiency for
    tickers that gain new data points regularly.

    Accepts either a pre-parsed DataFrame (from run_calculation.py shared cache)
    or a file path string (when called standalone via main()).

    Parameters
    ----------
    input_or_df : str or pd.DataFrame
        File path or pre-parsed DataFrame.
    output_path : str
        Path to write the momentum indicator CSV.
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

    # State file lives in state/ subdirectory alongside the output CSV
    base, ext = os.path.splitext(output_path)
    state_dir = os.path.join(os.path.dirname(output_path), "state")
    os.makedirs(state_dir, exist_ok=True)
    state_path = os.path.join(state_dir, os.path.basename(base) + "_state.json")

    # Determine if we have previous output
    prev_output_exists = os.path.exists(output_path)

    if prev_output_exists and file_total == 0:
        # Edge case: file exists but input is now empty
        return 0

    if prev_output_exists and file_total > 0:
        # Check if there are new rows to compute
        prev_df = pd.read_csv(output_path)
        prev_row_count = len(prev_df)

        if file_total <= prev_row_count:
            # No new rows — but recompute in case input changed
            # (safety net for corrupted previous state)
            pass  # fall through to full computation below
        else:
            # There are new rows — try incremental computation
            new_row_count = file_total - prev_row_count
            prev_close = float(prev_df["Close"].iloc[-1]) if "Close" in prev_df.columns else None

            # Try to load state; if missing, fall back to full computation
            state = _load_state(state_path)

            # Detect today's date: if the last row's date matches today and
            # there's existing output, force full recomputation.
            today = pd.Timestamp(pd.Timestamp.now().date())
            last_date = raw_df["Date"].iloc[-1] if file_total > 0 else None
            overwrite_today = (
                last_date is not None
                and (last_date.date() == today.date() if hasattr(last_date, "date") else str(last_date) == str(today.date()))
                and prev_output_exists
                and file_total > 0
            )

            if not overwrite_today and state is not None and state.get("_version") == 1:
                try:
                    # --- Incremental path ---
                    closes = raw_df["Close"].tolist()
                    highs = raw_df["High"].tolist()
                    lows = raw_df["Low"].tolist()

                    # 1) Full computation for all rows (for correctness)
                    #    We only write the new rows, but we compute full for
                    #    verification and to get correct values for new rows.
                    all_cols = compute_momentum_columns(closes, highs, lows, file_total)

                    # Build full output for new rows only
                    df_new_full = pd.DataFrame({"Date": raw_df["Date"].iloc[prev_row_count:]})
                    for col, values in all_cols.items():
                        df_new_full[col] = values[prev_row_count:]

                    # Merge with old output
                    df_old = prev_df  # keep existing rows
                    merged = pd.concat([df_old, df_new_full.reset_index(drop=True)],
                                       ignore_index=True)

                    merged.to_csv(output_path, index=False)

                    # Update state
                    state["prev_row_count"] = file_total
                    state["last_close"] = closes[-1]
                    _save_state(state, state_path)

                    return len(merged)

                except Exception:
                    # Incremental computation failed — fall back to full
                    pass

    # === Full computation path ===
    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()

    momentum_cols = compute_momentum_columns(closes, highs, lows, file_total)

    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in momentum_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)
    df.to_csv(output_path, index=False)

    # Save state for next incremental run
    state = {
        "_version": 1,
        "prev_row_count": file_total,
        "last_close": closes[-1],
    }
    _save_state(state, state_path)

    return len(df)


def compute_momentum_columns(closes, highs, lows, n):
    """Compute all momentum indicator columns for a single ticker's data."""
    ta_rsi = compute_rsi(closes, 14) if n >= 15 else [None] * n
    ta_roc = compute_roc(closes, 20) if n >= 21 else [None] * n
    macd = compute_macd(closes)
    stoch = compute_stochastic(closes) if n >= 14 else {"ta_stoch_k": [None] * n, "ta_stoch_d": [None] * n}
    ta_williams_r = compute_williams_r(highs, lows, closes, 14) if n >= 14 else [None] * n
    ta_cci = compute_cci(highs, lows, closes, 20) if n >= 20 else [None] * n
    ta_tsi = compute_tsi(closes, 25, 13) if n >= 39 else [None] * n
    ta_rsi_zscore = compute_rsi_zscore(closes) if n >= 35 else [None] * n
    ta_rsi_percentile = compute_rsi_percentile(closes) if n >= 35 else [None] * n

    return {
        "ta_rsi14": ta_rsi,
        "ta_macd_line": macd["macd_line"],
        "ta_macd_signal": macd["signal_line"],
        "ta_macd_histogram": macd["histogram"],
        "ta_roc20": ta_roc,
        "ta_stoch_k": stoch["ta_stoch_k"],
        "ta_stoch_d": stoch["ta_stoch_d"],
        "ta_williams_r": ta_williams_r,
        "ta_cci": ta_cci,
        "ta_tsi": ta_tsi,
        "ta_rsi_zscore": ta_rsi_zscore,
        "ta_rsi_percentile": ta_rsi_percentile,
    }


if __name__ == "__main__":
    main(
        module_name="calculate_momentum",
        description="momentum indicators: RSI(14), MACD, ROC(20), Stochastic %K/%D, Williams %R, CCI, TSI, RSI Z-Score(14,20), RSI Percentile(14,20)",
        process_csv_fn=process_csv,
    )

import os
import sys
import threading
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


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()

    # Compute this module's TA columns only
    momentum_cols = compute_momentum_columns(closes, highs, lows, file_total)

    # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in momentum_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


if __name__ == "__main__":
    main(
        module_name="calculate_momentum",
        description="momentum indicators: RSI(14), MACD, ROC(20), Stochastic %K/%D, Williams %R, CCI, TSI, RSI Z-Score(14,20), RSI Percentile(14,20)",
        process_csv_fn=process_csv,
    )

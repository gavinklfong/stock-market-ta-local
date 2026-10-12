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


def compute_momentum_columns(closes, n):
    """Compute all momentum indicator columns for a single ticker's data."""
    ta_rsi = compute_rsi(closes, 14) if n >= 15 else [None] * n
    ta_roc = compute_roc(closes, 20) if n >= 21 else [None] * n
    macd = compute_macd(closes)

    return {
        "ta_rsi14": ta_rsi,
        "ta_macd_line": macd["macd_line"],
        "ta_macd_signal": macd["signal_line"],
        "ta_macd_histogram": macd["histogram"],
        "ta_roc20": ta_roc,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()

    # Use market data as the source of truth
    file_total = len(raw_df)

    # Start from market data, merge existing TA columns onto it
    df = raw_df.copy()
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        existing_df["Date"] = pd.to_datetime(existing_df["Date"])
        # Only keep TA-prefixed columns (drop all non-TA columns to avoid duplicates)
        ta_cols = [c for c in existing_df.columns if c.startswith("ta_")]
        if ta_cols:
            df = df.merge(existing_df[["Date"] + ta_cols], on="Date", how="left")

    momentum_cols = compute_momentum_columns(closes, file_total)
    for col, values in momentum_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


if __name__ == "__main__":
    main(
        module_name="calculate_momentum",
        description="momentum indicators: RSI(14), MACD, ROC(20)",
        process_csv_fn=process_csv,
    )

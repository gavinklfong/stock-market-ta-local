import math
import os
import pandas as pd

from common import main, read_yfinance_csv

# Standard trading days per year for annualization
_ANNUALIZATION_FACTOR = 252


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


def compute_bollinger_bands(closes, period=20, num_std=2.0):
    """Compute Bollinger Bands. Returns dict with upper, middle (SMA), lower."""
    n = len(closes)
    upper = [None] * n
    middle = [None] * n
    lower = [None] * n

    if n < period:
        return {"upper": upper, "middle": middle, "lower": lower}

    for i in range(period - 1, n):
        window = [float(closes[j]) for j in range(i - period + 1, i + 1)]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        middle[i] = mean
        upper[i] = mean + num_std * std
        lower[i] = mean - num_std * std

    return {"upper": upper, "middle": middle, "lower": lower}


def compute_historical_volatility(closes, period=20, annualize=True):
    """Compute Historical Volatility from log returns.

    HV is the standard deviation of log returns over *period* bars,
    optionally annualised by multiplying by sqrt(252).

    Returns a list aligned with *closes*; ``None`` where insufficient data.
    """
    n = len(closes)
    result = [None] * n

    if n < period + 1:
        return result

    # Build log returns: ln(close[i] / close[i-1])
    log_returns = [0.0] * n
    for i in range(1, n):
        if closes[i] > 0 and closes[i - 1] > 0:
            log_returns[i] = math.log(closes[i] / closes[i - 1])
        else:
            log_returns[i] = 0.0

    factor = math.sqrt(_ANNUALIZATION_FACTOR) if annualize else 1.0

    for i in range(period, n):
        window = log_returns[i - period + 1: i + 1]
        mean = sum(window) / period
        variance = sum((r - mean) ** 2 for r in window) / period
        std = math.sqrt(variance)
        result[i] = std * factor

    return result


def compute_volatility_columns(highs, lows, closes, n):
    """Compute all volatility indicator columns for a single ticker's data."""
    ta_atr = compute_atr(highs, lows, closes, 14) if n >= 15 else [None] * n
    ta_normalized_atr14 = [
        ta_atr[i] / closes[i] if ta_atr[i] is not None and closes[i] != 0 else None
        for i in range(n)
    ]
    bb = compute_bollinger_bands(closes) if n >= 20 else {"upper": [None] * n, "middle": [None] * n, "lower": [None] * n}

    n = len(closes)
    ta_bband_width = [None] * n
    ta_bband_pctb = [None] * n
    for i in range(n):
        if (bb["upper"][i] is not None and bb["lower"][i] is not None
                and bb["middle"][i] is not None and bb["middle"][i] != 0):
            ta_bband_width[i] = (bb["upper"][i] - bb["lower"][i]) / bb["middle"][i]
        if (bb["upper"][i] is not None and bb["lower"][i] is not None
                and bb["upper"][i] != bb["lower"][i]):
            ta_bband_pctb[i] = (closes[i] - bb["lower"][i]) / (bb["upper"][i] - bb["lower"][i])

    ta_hvol20 = compute_historical_volatility(closes) if n >= 21 else [None] * n

    return {
        "ta_atr14": ta_atr,
        "ta_normalized_atr14": ta_normalized_atr14,
        "ta_bband_upper": bb["upper"],
        "ta_bband_middle": bb["middle"],
        "ta_bband_lower": bb["lower"],
        "ta_bband_width": ta_bband_width,
        "ta_bband_pctb": ta_bband_pctb,
        "ta_hvol20": ta_hvol20,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()

    # Compute this module's TA columns only
    volatility_cols = compute_volatility_columns(highs, lows, closes, file_total)

    # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in volatility_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_volatility",
    description="volatility indicators: ATR(14), Bollinger Bands(20,2), Band Width(20), %B(20), Historical Volatility(20, annualized)",
    process_csv_fn=process_csv,
)

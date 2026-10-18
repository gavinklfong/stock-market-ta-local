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


def compute_parkinson_volatility(highs, lows, period=20, annualize=True):
    """Compute Parkinson Volatility from high-low ranges.

    Parkinson volatility uses the intra-bar high-low range, which is a
    more efficient estimator of volatility than close-to-close returns
    (the factor 4 * ln(2) accounts for the expected ratio of ranges
    to close-to-close estimators).

    Formula: sqrt( (1 / (4 * ln(2) * n)) * sum(ln(high_i / low_i)^2) )

    Returns a list aligned with *highs*; ``None`` where insufficient data.
    """
    n = len(highs)
    result = [None] * n

    if n < period:
        return result

    _CONST = 4.0 * math.log(2)

    # Precompute ln(high/low) for each bar
    hl_log = [0.0] * n
    for i in range(n):
        if highs[i] > 0 and lows[i] > 0:
            hl_log[i] = math.log(highs[i] / lows[i])
        else:
            hl_log[i] = 0.0

    factor = math.sqrt(_ANNUALIZATION_FACTOR) if annualize else 1.0

    for i in range(period - 1, n):
        sum_sq = sum(hl_log[j] ** 2 for j in range(i - period + 1, i + 1))
        parkinson = math.sqrt(sum_sq / (_CONST * period))
        result[i] = parkinson * factor

    return result


def compute_atr_stop_distance(closes, atr_values, multiplier=3.0):
    """Compute ATR-based stop distance as a percentage of price.

    The stop level is ``close - multiplier * ATR`` (a trailing ATR stop).
    This function returns the distance from current close to stop level,
    expressed as a percentage of the current close:

        ta_atr_stop_dist = (multiplier * ATR / close) * 100

    A larger value means the stop is farther away (wider buffer).

    Returns a list aligned with *closes*; ``None`` where ATR is unavailable.
    """
    n = len(closes)
    result = [None] * n
    for i in range(n):
        if (atr_values[i] is not None and closes[i] is not None
                and closes[i] != 0 and atr_values[i] > 0):
            result[i] = (multiplier * atr_values[i] / closes[i]) * 100
    return result


def compute_atr_position_size(closes, atr_values, risk_pct=2.0, multiplier=3.0):
    """Compute ATR-based position size as a percentage of portfolio.

    Position sizing uses your risk budget and the ATR-based stop distance
    to determine the maximum position size as a percentage of your portfolio.

    Formula::

        stop_distance_pct = (multiplier * ATR / close) * 100
        position_size_pct = risk_pct / stop_distance_pct * 100

    A smaller ATR (tighter stop) allows a larger position; a larger ATR
    (wider stop) reduces the maximum position.

    Returns a list aligned with *closes*; ``None`` where ATR is unavailable
    or values are zero.
    """
    n = len(closes)
    result = [None] * n
    for i in range(n):
        if (atr_values[i] is not None and closes[i] is not None
                and closes[i] != 0 and atr_values[i] > 0):
            stop_distance_pct = (multiplier * atr_values[i] / closes[i]) * 100
            if stop_distance_pct > 0:
                result[i] = risk_pct / stop_distance_pct * 100
    return result


def compute_rr_ratio(closes, atr_values, bb_upper, multiplier=3.0):
    """Compute Reward-to-Risk ratio using ATR stop and Bollinger Band target.

    This indicator compares the potential reward (upside to the upper Bollinger
    Band) against the risk (downside to the ATR-based stop level).

    Formula::

        reward  = BB_upper - close
        risk    = multiplier * ATR
        rr_ratio = reward / risk

    A value greater than 1 means the potential upside exceeds the downside
    risk; less than 1 means the risk outweighs the reward.

    Returns a list aligned with *closes*; ``None`` where ATR, close, or
    BB upper is unavailable.
    """
    n = len(closes)
    result = [None] * n
    for i in range(n):
        if (atr_values[i] is not None and closes[i] is not None
                and bb_upper[i] is not None and atr_values[i] > 0
                and closes[i] != 0):
            risk = multiplier * atr_values[i]
            if risk > 0:
                result[i] = (bb_upper[i] - closes[i]) / risk
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
    ta_parkinson_vol = compute_parkinson_volatility(highs, lows) if n >= 20 else [None] * n
    ta_atr_stop_dist = compute_atr_stop_distance(closes, ta_atr, multiplier=3.0)
    ta_atr_position = compute_atr_position_size(closes, ta_atr, risk_pct=2.0, multiplier=3.0)
    ta_rr_ratio = compute_rr_ratio(closes, ta_atr, bb["upper"], multiplier=3.0)

    return {
        "ta_atr14": ta_atr,
        "ta_normalized_atr14": ta_normalized_atr14,
        "ta_bband_upper": bb["upper"],
        "ta_bband_middle": bb["middle"],
        "ta_bband_lower": bb["lower"],
        "ta_bband_width": ta_bband_width,
        "ta_bband_pctb": ta_bband_pctb,
        "ta_hvol20": ta_hvol20,
        "ta_parkinson_vol": ta_parkinson_vol,
        "ta_atr_stop_dist": ta_atr_stop_dist,
        "ta_atr_position": ta_atr_position,
        "ta_rr_ratio": ta_rr_ratio,
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
    description="volatility indicators: ATR(14), Bollinger Bands(20,2), Band Width(20), %B(20), Historical Volatility(20, annualized), Parkinson Volatility(20, annualized), ATR Stop Distance(3×ATR, % of price), ATR Position Size(2% risk, 3×ATR), Reward Risk Ratio(BB upper / ATR stop)",
    process_csv_fn=process_csv,
)

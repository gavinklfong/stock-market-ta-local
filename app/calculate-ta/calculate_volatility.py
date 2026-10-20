import json
import math
import os
import pandas as pd

from common import main, read_yfinance_csv

# Standard trading days per year for annualization
_ANNUALIZATION_FACTOR = 252


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
# Incremental ATR helper
# =============================================================================


def compute_atr_from_state(highs, lows, closes, period, last_tr, last_atr, last_idx, boundary_start=0):
    """Compute ATR continuing from a previous state.

    For rows before boundary_start + period, ATR is computed from scratch
    (same as full computation) to ensure consistency with lookback-based
    indicators like ATR Percentile. From last_idx onward, Wilder's smoothing
    continues from the saved state.

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
    boundary_start : int
        Start of the boundary region. ATR is computed from scratch for
        rows [0 .. boundary_start + period - 1].

    Returns
    -------
    list
        ATR values for all indices (None where not yet valid).
    """
    n = len(highs)
    result = [None] * n

    # Step 1: Compute TR for all rows
    tr = [0.0] * n
    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i]
        else:
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )

    # Step 2: Compute ATR from scratch for all rows (same formula as compute_atr)
    # Uses EMA smoothing: k = 2/(period+1), matching the original.
    k = 2.0 / (period + 1)
    for i in range(n):
        if i == 0:
            result[i] = None
            continue
        if i < period:
            result[i] = None
            continue
        if i == period:
            # Seed ATR at index `period` using first `period` true ranges
            result[i] = sum(tr[j] for j in range(period)) / period
        else:
            prev = result[i - 1]
            if prev is not None:
                result[i] = prev * (1 - k) + tr[i] * k
            else:
                result[i] = None

    # Step 3: Continue from state for rows after last_idx
    if last_atr is not None and last_idx + 1 < n:
        current_atr = last_atr
        for i in range(last_idx + 1, n):
            current_atr = current_atr * (1 - k) + tr[i] * k
            result[i] = current_atr

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


def compute_atr_percentile(highs, lows, closes, atr_period=14, window=20):
    """Compute rolling percentile rank of ATR values.

    ATR percentile = percentage of ATR values in the rolling window
    that are strictly less than the current ATR.

    This tells us where the current volatility (ATR) ranks relative to
    its recent distribution. A percentile of 90 means current ATR is
    higher than 90% of the past 20 ATR values — potentially elevated
    volatility.

    Parameters
    ----------
    closes : list[float]
        Close prices for each bar (used to determine data length).
    highs : list[float]
        High prices.
    lows : list[float]
        Low prices.
    atr_period : int
        ATR lookback period (default 14).
    window : int
        Rolling window for percentile calculation (default 20).

    Returns
    -------
    list[float | None]
        Percentile values (0–100) aligned with input; None before warmup.
    """
    n = len(closes)
    result = [None] * n

    if n < atr_period + window:
        return result

    # Compute ATR
    atr_values = compute_atr(highs, lows, closes, atr_period)

    # First ATR valid index = atr_period
    # First percentile valid index = atr_period + window - 1
    for i in range(atr_period + window - 1, n):
        atr_i = atr_values[i]
        if atr_i is None:
            continue

        window_atr = []
        for j in range(i - window + 1, i + 1):
            v = atr_values[j]
            if v is not None:
                window_atr.append(v)

        if len(window_atr) < 2:
            continue

        # Count values strictly below current ATR
        below_count = sum(1 for v in window_atr if v < atr_i)
        result[i] = (below_count / len(window_atr)) * 100.0

    return result


def compute_volatility_columns_incremental(highs, lows, closes, n, prev_row_count, state):
    """Compute all volatility indicator columns for new rows, continuing from previous state.

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
        - last_atr: last ATR value
        - last_tr: last true range value
        - last_atr_idx: last ATR index

    Returns
    -------
    dict
        All volatility columns as full-length lists.
    """
    # Determine boundary: max lookback period for any indicator
    # ATR: period=14, BB: period=20, HV: period=20, Parkinson: period=20
    # ATR Percentile needs ATR + window=20, so first valid at atr_period + window - 1 = 33
    buffer = 50
    boundary_start = max(0, prev_row_count - buffer)

    # ---- ATR (incremental) ----
    # Try incremental first, fall back to full if state missing
    last_atr = state.get("last_atr")
    last_tr = state.get("last_tr")
    last_atr_idx = state.get("last_atr_idx", prev_row_count - 1)

    if last_atr is not None:
        ta_atr = compute_atr_from_state(
            highs, lows, closes, 14, last_tr, last_atr, last_atr_idx,
            boundary_start=boundary_start
        )
    else:
        ta_atr = compute_atr(highs, lows, closes, 14)

    # ---- Derived: normalized ATR ----
    ta_normalized_atr14 = [
        ta_atr[i] / closes[i] if ta_atr[i] is not None and closes[i] != 0 else None
        for i in range(n)
    ]

    # ---- Bollinger Bands (incremental with boundary) ----
    bb = compute_bollinger_bands_from_state(
        closes, period=20, boundary_start=boundary_start
    )

    # ---- Derived: BB Width, %B ----
    ta_bband_width = [None] * n
    ta_bband_pctb = [None] * n
    for i in range(n):
        if (bb["upper"][i] is not None and bb["lower"][i] is not None
                and bb["middle"][i] is not None and bb["middle"][i] != 0):
            ta_bband_width[i] = (bb["upper"][i] - bb["lower"][i]) / bb["middle"][i]
        if (bb["upper"][i] is not None and bb["lower"][i] is not None
                and bb["upper"][i] != bb["lower"][i]):
            ta_bband_pctb[i] = (closes[i] - bb["lower"][i]) / (bb["upper"][i] - bb["lower"][i])

    # ---- Historical Volatility (incremental with boundary) ----
    ta_hvol20 = compute_historical_volatility_from_state(
        closes, period=20, boundary_start=boundary_start
    )

    # ---- Parkinson Volatility (incremental with boundary) ----
    ta_parkinson_vol = compute_parkinson_volatility_from_state(
        highs, lows, period=20, boundary_start=boundary_start
    )

    # ---- Derived: ATR Stop Distance, Position Size, RR Ratio ----
    ta_atr_stop_dist = compute_atr_stop_distance(closes, ta_atr, multiplier=3.0)
    ta_atr_position = compute_atr_position_size(closes, ta_atr, risk_pct=2.0, multiplier=3.0)
    ta_rr_ratio = compute_rr_ratio(closes, ta_atr, bb["upper"], multiplier=3.0)

    # ---- ATR Percentile (incremental with boundary) ----
    ta_atr_percentile = compute_atr_percentile_from_state(
        highs, lows, closes, ta_atr, window=20, boundary_start=boundary_start
    )

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
        "ta_atr_percentile": ta_atr_percentile,
    }


def compute_bollinger_bands_from_state(closes, period, boundary_start):
    """Compute Bollinger Bands for a boundary region.

    Returns full-length lists (None before boundary_start).
    """
    n = len(closes)
    upper = [None] * n
    middle = [None] * n
    lower = [None] * n

    for i in range(boundary_start, n):
        if i < period - 1:
            continue
        window = [float(closes[j]) for j in range(i - period + 1, i + 1)]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        middle[i] = mean
        upper[i] = mean + 2.0 * std
        lower[i] = mean - 2.0 * std

    return {"upper": upper, "middle": middle, "lower": lower}


def compute_historical_volatility_from_state(closes, period, boundary_start):
    """Compute Historical Volatility for a boundary region.

    Returns full-length list (None before boundary_start).
    """
    n = len(closes)
    result = [None] * n

    # Build log returns for the boundary region
    factor = math.sqrt(_ANNUALIZATION_FACTOR)

    for i in range(boundary_start, n):
        if i < period:
            continue
        # Build log returns window
        log_returns = []
        valid = True
        for j in range(i - period + 1, i + 1):
            if j == 0 or closes[j - 1] <= 0 or closes[j] <= 0:
                valid = False
                break
            log_returns.append(math.log(closes[j] / closes[j - 1]))
        if not valid or len(log_returns) < period:
            continue

        mean = sum(log_returns) / period
        variance = sum((r - mean) ** 2 for r in log_returns) / period
        std = math.sqrt(variance)
        result[i] = std * factor

    return result


def compute_parkinson_volatility_from_state(highs, lows, period, boundary_start):
    """Compute Parkinson Volatility for a boundary region.

    Returns full-length list (None before boundary_start).
    """
    n = len(highs)
    result = [None] * n

    _CONST = 4.0 * math.log(2)
    factor = math.sqrt(_ANNUALIZATION_FACTOR)

    for i in range(boundary_start, n):
        if i < period - 1:
            continue
        sum_sq = 0.0
        for j in range(i - period + 1, i + 1):
            if highs[j] > 0 and lows[j] > 0:
                sum_sq += math.log(highs[j] / lows[j]) ** 2
            else:
                sum_sq += 0.0
        parkinson = math.sqrt(sum_sq / (_CONST * period))
        result[i] = parkinson * factor

    return result


def compute_atr_percentile_from_state(highs, lows, closes, atr_values, window, boundary_start):
    """Compute ATR percentile for a boundary region.

    Uses pre-computed ATR values (full-length list) to ensure consistency
    with the main ATR computation.

    Returns full-length list (None before boundary_start).
    """
    n = len(closes)
    result = [None] * n

    if n < window + 1:
        return result

    # First valid percentile index (need at least 2 valid ATR values in window)
    first_pct_idx = window  # 0-indexed, first valid percentile at atr_period + window - 1

    for i in range(max(first_pct_idx, boundary_start), n):
        atr_i = atr_values[i]
        if atr_i is None:
            continue

        window_atr = []
        for j in range(i - window + 1, i + 1):
            v = atr_values[j]
            if v is not None:
                window_atr.append(v)

        if len(window_atr) < 2:
            continue

        below_count = sum(1 for v in window_atr if v < atr_i)
        result[i] = (below_count / len(window_atr)) * 100.0

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
    ta_atr_percentile = compute_atr_percentile(highs, lows, closes) if n >= 35 else [None] * n

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
        "ta_atr_percentile": ta_atr_percentile,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    # Guard: empty data — write empty output and return
    if file_total == 0:
        pd.DataFrame(columns=["Date"]).to_csv(output_path, index=False)
        return 0

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()

    # Determine incremental mode: state file exists and data has grown
    state_path = output_path.rsplit(".", 1)[0] + "_state.json"
    state = _load_state(state_path)
    incremental = (state is not None
                   and state.get("_version") == 1
                   and file_total > state.get("prev_row_count", 0))

    # --- Incremental path ---
    if incremental:
        state_pr = state["prev_row_count"]
        new_cols = compute_volatility_columns_incremental(
            highs, lows, closes, file_total, state_pr, state
        )

        # Copy old values (before prev_row_count) from existing output
        df_old = None
        if os.path.exists(output_path):
            df_old = pd.read_csv(output_path)

        # Build output: Date + own ta_ columns
        df = pd.DataFrame({"Date": raw_df["Date"]})
        for col, values in new_cols.items():
            if df_old is not None and col in df_old.columns:
                old_vals = df_old[col].tolist()
                merged = old_vals[:state_pr] + values[state_pr:]
                df[col] = merged
            else:
                df[col] = values

        # Save updated state
        _save_state({
            "_version": 1,
            "prev_row_count": file_total,
            "last_date": str(raw_df["Date"].iloc[-1]),
            "last_atr": new_cols["ta_atr14"][-1] if new_cols["ta_atr14"][-1] is not None else None,
            "last_tr": _get_atr_state(highs, lows, closes, 14)["last_tr"],
            "last_atr_idx": file_total - 1,
        }, state_path)

    # --- Full computation path ---
    else:
        volatility_cols = compute_volatility_columns(highs, lows, closes, file_total)

        df = pd.DataFrame({"Date": raw_df["Date"]})
        for col, values in volatility_cols.items():
            df[col] = values

        # Save initial state
        atr_state = _get_atr_state(highs, lows, closes, 14)
        _save_state({
            "_version": 1,
            "prev_row_count": file_total,
            "last_date": str(raw_df["Date"].iloc[-1]),
            "last_atr": volatility_cols["ta_atr14"][-1] if volatility_cols["ta_atr14"][-1] is not None else None,
            "last_tr": atr_state["last_tr"],
            "last_atr_idx": file_total - 1,
        }, state_path)

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_volatility",
    description="volatility indicators: ATR(14), Bollinger Bands(20,2), Band Width(20), %B(20), Historical Volatility(20, annualized), Parkinson Volatility(20, annualized), ATR Stop Distance(3×ATR, % of price), ATR Position Size(2% risk, 3×ATR), Reward Risk Ratio(BB upper / ATR stop), ATR Percentile(14,20)",
    process_csv_fn=process_csv,
)

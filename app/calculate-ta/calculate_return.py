import json
import os
import sys

import pandas as pd

from common import (
    file_progress_bar,
    main,
    read_yfinance_csv,
)


def compute_future_returns(closes, horizons=(5, 10, 20)):
    """Compute forward-looking percentage returns for each horizon.

    For each horizon H, future_return_H = (close[t+H] - close[t]) / close[t].
    Returns None for the last H rows where future data is unavailable.

    Args:
        closes: list/array of close prices.
        horizons: tuple of integer horizons in trading days.

    Returns:
        dict mapping horizon (int) to list of float returns aligned with input.
    """
    n = len(closes)
    result = {}
    for h in horizons:
        returns = [None] * n
        for i in range(n - h):
            prev_close = closes[i]
            future_close = closes[i + h]
            if prev_close != 0:
                returns[i] = (future_close - prev_close) / prev_close
        result[h] = returns
    return result


def compute_past_performance(closes, horizons=(21, 63, 126, 252)):
    """Compute past performance (percentage returns) for each horizon.

    For each horizon H, past_performance_H = (close[t] - close[t-H]) / close[t-H] * 100.
    Returns None for the first H rows where past data is unavailable.

    Args:
        closes: list/array of close prices.
        horizons: tuple of integer horizons in trading days.

    Returns:
        dict mapping horizon label (str) to list of float returns
        aligned with input, expressed as percentages.
    """
    n = len(closes)
    result = {}
    for h in horizons:
        returns = [None] * n
        for i in range(h, n):
            past_close = closes[i - h]
            current_close = closes[i]
            if past_close != 0:
                returns[i] = (current_close - past_close) / past_close * 100
        result[h] = returns
    return result


def compute_alpha_beta(stock_closes, benchmark_closes, window=20):
    """Compute rolling alpha and beta relative to a benchmark.

    Using daily returns over a rolling window of W days:
        beta  = Cov(r_stock, r_benchmark) / Var(r_benchmark)
        alpha = mean(r_stock) - beta * mean(r_benchmark)

    Both alpha and beta are expressed as percentages (×100).

    Args:
        stock_closes: list/array of stock close prices.
        benchmark_closes: list/array of benchmark close prices (same length).
        window: rolling window size in trading days.

    Returns:
        dict with keys "alpha" and "beta", each mapping to a list of floats
        aligned with input (None for first window-1 rows).
    """
    n = len(stock_closes)
    stock_ret = [None] * n
    bench_ret = [None] * n
    for i in range(1, n):
        if stock_closes[i - 1] != 0:
            stock_ret[i] = (stock_closes[i] - stock_closes[i - 1]) / stock_closes[i - 1]
        if benchmark_closes[i - 1] != 0:
            bench_ret[i] = (benchmark_closes[i] - benchmark_closes[i - 1]) / benchmark_closes[i - 1]

    alpha = [None] * n
    beta = [None] * n

    for i in range(window, n):
        # Extract windows of returns (both need to be valid)
        s_window = stock_ret[i - window + 1 : i + 1]
        b_window = bench_ret[i - window + 1 : i + 1]

        if None in s_window or None in b_window:
            continue

        s_mean = sum(s_window) / window
        b_mean = sum(b_window) / window

        cov = sum((s_window[j] - s_mean) * (b_window[j] - b_mean) for j in range(window)) / window
        var_b = sum((b_window[j] - b_mean) ** 2 for j in range(window)) / window

        if var_b != 0:
            beta[i] = cov / var_b
            alpha[i] = (s_mean - beta[i] * b_mean) * 100
        else:
            beta[i] = 0.0
            alpha[i] = s_mean * 100

    return {"alpha": alpha, "beta": beta}


def _align_benchmark(stock_dates, benchmark_df):
    """Align benchmark data with stock dates.

    Returns a list of benchmark closes matching stock_dates order, or None.
    """
    if benchmark_df is None:
        return None
    try:
        aligned = benchmark_df[benchmark_df["Date"].isin(stock_dates)]
        aligned = aligned.sort_values("Date").reset_index(drop=True)
        return aligned["Close"].tolist()
    except Exception:
        return None


def compute_relative_strength(stock_closes, benchmark_closes):
    """Compute relative strength of stock vs benchmark.

    RS = (stock_close / benchmark_close) * 100

    An indexed value where 100 means the stock is at the same relative level
    as the benchmark. Values above 100 indicate outperformance; below 100,
    underperformance.

    Args:
        stock_closes: list/array of stock close prices.
        benchmark_closes: list/array of benchmark close prices (same length).

    Returns:
        list of float relative strength values aligned with input.
        Returns None where benchmark price is zero.
    """
    n = len(stock_closes)
    rs = [None] * n
    for i in range(n):
        if benchmark_closes[i] != 0:
            rs[i] = (stock_closes[i] / benchmark_closes[i]) * 100
    return rs


def compute_return_columns(highs, lows, closes, volumes, n, dates, horizons=(5, 10, 20),
                           benchmark_df=None):
    """Compute all future-return, past-performance, alpha/beta, and relative strength columns."""
    future = compute_future_returns(closes, horizons)
    cols = {}
    for h in horizons:
        cols[f"ta_return_{h}d"] = future[h]

    # Past performance columns with standard horizons (in trading days):
    # 1M=21d, 3M=63d, 6M=126d, 1Y=252d
    past_horizons = (21, 63, 126, 252)
    past = compute_past_performance(closes, past_horizons)
    label_map = {21: "1m", 63: "3m", 126: "6m", 252: "1y"}
    for h in past_horizons:
        cols[f"ta_performance_{label_map[h]}"] = past[h]

    # Rolling alpha and beta relative to benchmark (date-aligned)
    if benchmark_df is not None:
        ab = _compute_aligned_alpha_beta(closes, dates, benchmark_df)
        if ab is not None:
            cols["ta_alpha20"] = ab["alpha"]
            cols["ta_beta20"] = ab["beta"]

        # Relative strength (date-aligned)
        rs = _compute_aligned_relative_strength(closes, dates, benchmark_df)
        if rs is not None:
            cols["ta_rs_ftse100"] = rs

    return cols


def _compute_aligned_alpha_beta(closes, dates, benchmark_df):
    """Compute rolling alpha/beta with date-based alignment.

    Aligns stock and benchmark by date, computes alpha/beta on the
    overlapping portion, then expands results back to the full stock length.
    Returns dict with full-length "alpha" and "beta" lists, or None.
    """
    n = len(closes)
    if n < 21 or benchmark_df is None:
        return None

    # Map each stock date to its index
    date_to_idx = {dates[i]: i for i in range(n)}

    # Benchmark rows that match stock dates, sorted by date
    matching = benchmark_df[benchmark_df["Date"].isin(date_to_idx.keys())]
    matching = matching.sort_values("Date").reset_index(drop=True)

    if len(matching) < 21:
        return None

    # Build aligned arrays and track original stock indices
    stock_aligned = []
    bench_aligned = []
    stock_indices = []

    for _, row in matching.iterrows():
        d = row["Date"]
        idx = date_to_idx[d]
        stock_aligned.append(closes[idx])
        bench_aligned.append(row["Close"])
        stock_indices.append(idx)

    # Compute alpha/beta on the aligned subset
    ab = compute_alpha_beta(stock_aligned, bench_aligned, window=20)

    # Expand back to full stock length
    full_alpha = [None] * n
    full_beta = [None] * n
    for aligned_idx, stock_idx in enumerate(stock_indices):
        if aligned_idx >= 20:
            full_alpha[stock_idx] = ab["alpha"][aligned_idx]
            full_beta[stock_idx] = ab["beta"][aligned_idx]

    return {"alpha": full_alpha, "beta": full_beta}


def _compute_aligned_relative_strength(closes, dates, benchmark_df):
    """Compute relative strength with date-based alignment.

    Aligns stock and benchmark by date, computes RS on the overlapping
    portion, then expands results back to the full stock length.
    Returns a full-length list of RS values, or None.
    """
    n = len(closes)
    if n < 2 or benchmark_df is None:
        return None

    # Map each stock date to its index
    date_to_idx = {dates[i]: i for i in range(n)}

    # Benchmark rows that match stock dates, sorted by date
    matching = benchmark_df[benchmark_df["Date"].isin(date_to_idx.keys())]

    if len(matching) < 2:
        return None

    matching = matching.sort_values("Date").reset_index(drop=True)

    # Build aligned arrays and track original stock indices
    stock_aligned = []
    bench_aligned = []
    stock_indices = []

    for _, row in matching.iterrows():
        d = row["Date"]
        idx = date_to_idx[d]
        stock_aligned.append(closes[idx])
        bench_aligned.append(row["Close"])
        stock_indices.append(idx)

    # Compute RS on the aligned subset
    rs_aligned = compute_relative_strength(stock_aligned, bench_aligned)

    # Expand back to full stock length
    full_rs = [None] * n
    for aligned_idx, stock_idx in enumerate(stock_indices):
        full_rs[stock_idx] = rs_aligned[aligned_idx]

    return full_rs


def _load_benchmark(input_dir):
    """Load ^FTSE benchmark data from market-data directory.

    Returns a DataFrame with Date and Close columns, or None on failure.
    """
    bench_path = os.path.join(input_dir, "^FTSE.csv")
    if not os.path.exists(bench_path):
        return None
    try:
        df = read_yfinance_csv(bench_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        return df[["Date", "Close"]]
    except Exception:
        return None


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


def process_csv(input_or_df, output_path, total_files, current_file, _lock=None):
    """Process a single ticker's OHLCV data into return indicator output.

    When a previous output file and state file exist, this function performs
    **incremental computation**: it only computes indicators for rows that
    were appended since the last run, greatly improving efficiency for
    tickers that gain new data points regularly.

    For future returns specifically, old rows near the end of the previous
    output may now have valid values (previously None because horizon data
    was unavailable). These rows are updated in-place.

    Accepts either a pre-parsed DataFrame (from run_calculation.py shared cache)
    or a file path string (when called standalone via main()).

    Parameters
    ----------
    input_or_df : str or pd.DataFrame
        File path or pre-parsed DataFrame.
    output_path : str
        Path to write the return indicator CSV.
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
            # Detect today's date: if the last row's date matches today,
            # force full recomputation so today's indicators are always
            # up to date even without new rows.
            today = pd.Timestamp(pd.Timestamp.now().date())
            last_date = raw_df["Date"].iloc[-1] if file_total > 0 else None
            overwrite_today = (
                last_date is not None
                and (last_date.date() == today.date() if hasattr(last_date, "date") else str(last_date) == str(today.date()))
                and prev_output_exists
                and file_total > 0
            )
            if not overwrite_today:
                pass  # fall through to full computation below
        else:
            # There are new rows — try incremental computation
            new_row_count = file_total - prev_row_count

            # Load state; if missing, fall back to full computation
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

            # Check force flag
            force_full = os.environ.get("TA_FORCE_FULL_RECALCULATION", "0") == "1"

            if not overwrite_today and not force_full and state is not None and state.get("_version") == 1:
                try:
                    # --- Incremental path ---
                    closes = raw_df["Close"].tolist()
                    highs = raw_df["High"].tolist()
                    lows = raw_df["Low"].tolist()
                    volumes = raw_df["Volume"].tolist()
                    dates = raw_df["Date"].tolist()

                    # Load benchmark
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    base_dir = os.path.dirname(os.path.dirname(script_dir))
                    input_dir = os.path.join(base_dir, "data", "market-data")
                    benchmark_df = _load_benchmark(input_dir)

                    # Full computation for all rows (needed for correct
                    # future returns that span the boundary)
                    return_cols = compute_return_columns(
                        highs, lows, closes, volumes, file_total, dates,
                        benchmark_df=benchmark_df,
                    )

                    # Update future returns for old rows near the end that
                    # now have valid data (previously None)
                    max_horizon = 20
                    future_start = max(0, prev_row_count - max_horizon)

                    for h in (5, 10, 20):
                        col_name = f"ta_return_{h}d"
                        if future_start < prev_row_count:
                            for i in range(future_start, prev_row_count):
                                prev_df.loc[i, col_name] = return_cols[col_name][i]

                    # Build new rows DataFrame
                    df_new_full = pd.DataFrame(
                        {"Date": raw_df["Date"].iloc[prev_row_count:]}
                    )
                    for col, values in return_cols.items():
                        df_new_full[col] = values[prev_row_count:]

                    # Merge with old output
                    merged = pd.concat(
                        [prev_df, df_new_full.reset_index(drop=True)],
                        ignore_index=True,
                    )
                    merged = merged.sort_values("Date").reset_index(drop=True)
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
    volumes = raw_df["Volume"].tolist()
    dates = raw_df["Date"].tolist()

    # Load benchmark data for alpha/beta calculation
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(script_dir))
    input_dir = os.path.join(base_dir, "data", "market-data")
    benchmark_df = _load_benchmark(input_dir)

    # Compute this module's TA columns only
    return_cols = compute_return_columns(
        highs, lows, closes, volumes, file_total, dates,
        benchmark_df=benchmark_df,
    )

    # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in return_cols.items():
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


if __name__ == "__main__":
    main(
        module_name="calculate_return",
        description="future returns: 5d/10d/20d | past performance: 1m/3m/6m/1y | rolling alpha/beta vs ^FTSE (20d)",
        process_csv_fn=process_csv,
    )

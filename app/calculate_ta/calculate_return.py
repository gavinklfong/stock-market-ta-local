import os
import sys

import numpy as np
import pandas as pd

from common import (
    file_progress_bar,
    load_state,
    main,
    read_yfinance_csv,
    save_state,
)


def compute_future_returns(closes, horizons=(5, 10, 20)):
    """Compute forward-looking percentage returns for each horizon.

    Vectorized implementation: uses numpy shift operations instead
    of Python loops for all horizon calculations.

    Args:
        closes: list/array of close prices.
        horizons: tuple of integer horizons in trading days.

    Returns:
        dict mapping horizon (int) to list of float returns aligned with input.
    """
    n = len(closes)
    c = np.asarray(closes, dtype=float)
    result = {}
    for h in horizons:
        returns = np.full(n, np.nan, dtype=float)
        valid = c[:n - h] != 0
        returns[:n - h] = np.where(valid, (c[h:] - c[:n - h]) / c[:n - h], np.nan)
        # Convert nan to None for JSON/CSV compatibility
        result[h] = [None if np.isnan(v) else float(v) for v in returns]
    return result


def compute_past_performance(closes, horizons=(21, 63, 126, 252)):
    """Compute past performance (percentage returns) for each horizon.

    Vectorized implementation: uses numpy shift operations instead
    of Python loops for all horizon calculations.

    Args:
        closes: list/array of close prices.
        horizons: tuple of integer horizons in trading days.

    Returns:
        dict mapping horizon label (str) to list of float returns
        aligned with input, expressed as percentages.
    """
    n = len(closes)
    c = np.asarray(closes, dtype=float)
    result = {}
    for h in horizons:
        returns = np.full(n, np.nan, dtype=float)
        if h < n:
            valid = c[:n - h] != 0
            returns[h:] = np.where(valid, (c[h:] - c[:n - h]) / c[:n - h] * 100, np.nan)
        result[h] = [None if np.isnan(v) else float(v) for v in returns]
    return result


def compute_alpha_beta(stock_closes, benchmark_closes, window=20):
    """Compute rolling alpha and beta relative to a benchmark.

    Using daily returns over a rolling window of W days:
        beta  = Cov(r_stock, r_benchmark) / Var(r_benchmark)
        alpha = mean(r_stock) - beta * mean(r_benchmark)

    Both alpha and beta are expressed as percentages (×100).

    Vectorized implementation: uses pandas rolling operations for
    covariance, variance, and means instead of Python loops.

    Args:
        stock_closes: list/array of stock close prices.
        benchmark_closes: list/array of benchmark close prices (same length).
        window: rolling window size in trading days.

    Returns:
        dict with keys "alpha" and "beta", each mapping to a list of floats
        aligned with input (None for first window-1 rows).
    """
    n = len(stock_closes)
    stock_arr = np.asarray(stock_closes, dtype=float)
    bench_arr = np.asarray(benchmark_closes, dtype=float)

    # Compute daily returns using numpy (vectorized)
    stock_ret = np.empty(n, dtype=float)
    bench_ret = np.empty(n, dtype=float)
    stock_ret[0] = np.nan
    bench_ret[0] = np.nan

    stock_diff = np.diff(stock_arr)
    bench_diff = np.diff(bench_arr)

    # Avoid division by zero
    stock_prev = stock_arr[:-1]
    bench_prev = bench_arr[:-1]
    valid_stock = stock_prev != 0
    valid_bench = bench_prev != 0

    stock_ret[1:] = np.where(valid_stock, stock_diff / np.where(valid_stock, stock_prev, 1.0), np.nan)
    bench_ret[1:] = np.where(valid_bench, bench_diff / np.where(valid_bench, bench_prev, 1.0), np.nan)

    # Fully vectorized rolling operations using pandas
    s_series = pd.Series(stock_ret)
    b_series = pd.Series(bench_ret)

    rolling_cov = s_series.rolling(window, min_periods=window).cov(b_series).values
    rolling_var = b_series.rolling(window, min_periods=window).var().values
    s_mean = s_series.rolling(window, min_periods=window).mean().values
    b_mean = b_series.rolling(window, min_periods=window).mean().values

    # Compute beta and alpha (fully vectorized, no Python loop)
    beta_arr = np.full(n, np.nan)
    alpha_arr = np.full(n, np.nan)

    valid_mask = (~np.isnan(rolling_cov)) & (~np.isnan(rolling_var)) & (rolling_var != 0)
    beta_arr[valid_mask] = rolling_cov[valid_mask] / rolling_var[valid_mask]
    alpha_arr[valid_mask] = (s_mean[valid_mask] - beta_arr[valid_mask] * b_mean[valid_mask]) * 100

    # For zero variance: beta=0, alpha = s_mean * 100
    zero_var_mask = (~np.isnan(rolling_cov)) & (~np.isnan(rolling_var)) & (rolling_var == 0)
    beta_arr[zero_var_mask] = 0.0
    alpha_arr[zero_var_mask] = s_mean[zero_var_mask] * 100

    return {
        "alpha": [None if np.isnan(v) else float(v) for v in alpha_arr],
        "beta": [None if np.isnan(v) else float(v) for v in beta_arr],
    }


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

    Vectorized implementation: uses numpy element-wise division
    instead of Python loops.

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
    stock = np.asarray(stock_closes, dtype=float)
    bench = np.asarray(benchmark_closes, dtype=float)
    valid = bench != 0
    # Avoid divide-by-zero warning: replace zeros with 1 in denominator where invalid
    safe_bench = np.where(valid, bench, 1.0)
    rs = np.where(valid, stock / safe_bench * 100, np.nan)
    return [None if np.isnan(v) else float(v) for v in rs]


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


# Module-level cache for ^FTSE benchmark data (shared across all ticker processing).
_bench_cached: pd.DataFrame | None = None


def _load_benchmark(input_dir: str) -> pd.DataFrame | None:
    """Load ^FTSE benchmark data from market-data directory.

    Results are cached in-process so the benchmark is only loaded once
    regardless of how many tickers are processed.

    Returns a DataFrame with Date and Close columns, or None on failure.
    """
    global _bench_cached
    if _bench_cached is not None:
        return _bench_cached

    bench_path = os.path.join(input_dir, "^FTSE.csv")
    if not os.path.exists(bench_path):
        return None
    try:
        df = read_yfinance_csv(bench_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        _bench_cached = df[["Date", "Close"]]
        return _bench_cached
    except Exception:
        return None


# =============================================================================
# State file helpers
# =============================================================================


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
            state = load_state(state_path)

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
                    save_state(state, state_path)

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
    save_state(state, state_path)

    return len(df)


if __name__ == "__main__":
    main(
        module_name="calculate_return",
        description="future returns: 5d/10d/20d | past performance: 1m/3m/6m/1y | rolling alpha/beta vs ^FTSE (20d)",
        process_csv_fn=process_csv,
    )

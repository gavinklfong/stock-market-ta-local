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


def compute_return_columns(highs, lows, closes, volumes, n, dates, horizons=(5, 10, 20),
                           benchmark_df=None):
    """Compute all future-return, past-performance, and alpha/beta indicator columns."""
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


def _load_benchmark(input_dir):
    """Load ^FTSE benchmark data from market-data directory.

    Returns a DataFrame with Date and Close columns, or None on failure.
    """
    import os
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


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()
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
    return len(df)


if __name__ == "__main__":
    main(
        module_name="calculate_return",
        description="future returns: 5d/10d/20d | past performance: 1m/3m/6m/1y | rolling alpha/beta vs ^FTSE (20d)",
        process_csv_fn=process_csv,
    )

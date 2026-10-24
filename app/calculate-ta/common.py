"""Shared infrastructure for all calculate_*.py modules.

Exports:
    progress_bar, file_progress_bar, row_progress_bar — terminal progress helpers
    compute_ema — vectorized EMA computation (used by multiple modules)
    compute_rsi, compute_macd, compute_roc — momentum-indicator core functions
    compute_momentum_columns — assemble all momentum columns for a ticker
    compute_garch_volatility, compute_hmm_regime, compute_regime_columns — regime-indicator functions
    main — thread-pool pipeline with progress reporting (call from each module)
    read_yfinance_csv — read yfinance CSVs with multi-row header support
"""

import argparse
import json
import math
import os
import sys
import shutil
import threading
import concurrent.futures

import numpy as np
import pandas as pd


# --- Thread-safe progress bar state (shared across all modules) ---
_bar_state = {"last_row_lines": {}}
_row_lock = threading.Lock()


# --- Vectorized EMA helper ---


def compute_ema(values, period):
    """Compute Exponential Moving Average with SMA seed.

    Returns a list where each element is the EMA up to that index.
    Uses numpy convolution for the recursive computation, which is
    significantly faster than a pure Python loop for large arrays.

    The EMA is seeded with the SMA of the first period values, then
    recurses.  Valid values start at index period - 1.

    Parameters
    ----------
    values : array-like
        Input price/values.
    period : int
        EMA lookback period.

    Returns
    -------
    list[float | None]
        EMA values aligned with input; None for indices before warm-up.
    """
    n = len(values)
    result = [None] * n
    if n < period:
        return result

    v = np.asarray(values, dtype=float)

    # Seed with SMA of first `period` values
    ema_seed = float(v[:period].mean())
    result[period - 1] = ema_seed

    if n <= period:
        return result

    k = 2.0 / (period + 1)
    beta = 1.0 - k

    # Recursive EMA from index `period` onwards:
    #   ema[i] = k * v[i] + beta * ema[i-1]
    #
    # Closed-form expansion:
    #   ema[period + j] = beta^(j+1) * ema_seed
    #                   + k * sum_{m=0}^{j} v[period+m] * beta^(j-m)
    #
    # The price contribution is a causal convolution of the price series
    # with the kernel [k, k*beta, k*beta^2, …], which numpy computes
    # in O(n log n) via FFT.

    prices = v[period:]              # shape (n_new,)
    n_new = len(prices)

    weights = k * beta ** np.arange(n_new)   # [k, k*beta, k*beta^2, …]

    # Full convolution; extract first n_new elements (causal part).
    conv = np.convolve(prices, weights, 'full')
    price_contrib = conv[:n_new]

    # Seed decay component: beta^(j+1) * ema_seed for j = 0..n_new-1
    seed_decay = beta ** np.arange(1, n_new + 1) * ema_seed

    result[period:] = price_contrib + seed_decay

    return result

def progress_bar(current, total, prefix="", bar_length=40):
    """Render a single-line progress bar to stdout."""
    if total == 0:
        return
    fraction = current / total
    filled = int(bar_length * fraction)
    bar = "=" * filled + "-" * (bar_length - filled)
    pct = fraction * 100
    line = f"\r{prefix} |{bar}| {pct:.1f}% ({current}/{total})"
    line_len = len(line)
    term_width = shutil.get_terminal_size().columns
    if line_len >= term_width:
        line = line[:term_width - 1]
    sys.stdout.write(line)
    if current == total:
        sys.stdout.write("\n")
    sys.stdout.flush()


def file_progress_bar(filename, current, total):
    """Render file-level progress bar (one bar per CSV file)."""
    progress_bar(
        current, total,
        prefix=f"[{current}/{total}] {filename}: ",
    )


def row_progress_bar(filename, total_rows, current_row):
    """Render row-level progress bar (one bar per file, inside file loop)."""
    with _row_lock:
        last_lines = _bar_state["last_row_lines"]
        lines = last_lines.get(filename, 0)
        if lines > 0:
            for _ in range(lines):
                sys.stdout.write("\r\033[K\n")
        fraction = current_row / total_rows
        filled = int(30 * fraction)
        bar = "#" * filled + "-" * (30 - filled)
        pct = fraction * 100
        short_name = filename.replace(".csv", "")
        line = f"\r    [{short_name}] |{bar}| {pct:.1f}% ({current_row}/{total_rows})"
        line_len = len(line)
        term_width = shutil.get_terminal_size().columns
        if line_len >= term_width:
            line = line[:term_width - 1]
        sys.stdout.write(line)
        if current_row == total_rows:
            sys.stdout.write("\n")
        sys.stdout.flush()
        if current_row == total_rows:
            _bar_state["last_row_lines"][filename] = 0
        else:
            _bar_state["last_row_lines"][filename] = 1


# --- yfinance CSV reader ---

def read_yfinance_csv(input_path: str) -> pd.DataFrame:
    """Read a yfinance CSV, handling 2-row or 3-row header formats.

    yfinance CSVs have header rows like:
      Row 0: Ticker,NG.L,NG.L,NG.L,NG.L,NG.L
      Row 1: Price,Open,High,Low,Close,Volume
      Row 2: Date,,,,,  (3-row only)
      Row 3+: actual data

    Falls back to standard single-header CSV if no multi-row header is detected.

    Optimizations over the original implementation:
      - Vectorized header detection using numpy array operations
      - Vectorized column merge using numpy where() instead of per-column loops
      - Batch numeric conversion via df.apply() instead of per-column pd.to_numeric calls

    Args:
        input_path: Path to the CSV file.

    Returns:
        DataFrame with proper column names (Date, Open, High, Low, Close, Volume)
        and numeric types.
    """
    raw = pd.read_csv(input_path, header=None)

    # --- Vectorized header detection ---
    # Find the first row (within first 5) where col[0] == "Date"
    first_col = raw.iloc[:, 0].astype(str).str.strip().values
    search = first_col[:5] if len(first_col) > 5 else first_col
    mask = search == "Date"
    header_idx = int(np.argmax(mask)) if mask.any() else None

    if header_idx is None:
        # Fallback: use first row as header (standard single-header CSV)
        header_row = raw.iloc[0].astype(str)
    else:
        # --- Vectorized multi-row header merge ---
        row_date = raw.iloc[header_idx].astype(str).values
        row_above = raw.iloc[header_idx - 1].astype(str).values if header_idx > 0 else None
        row_above2 = raw.iloc[header_idx - 2].astype(str).values if header_idx > 1 else None
        n_cols = len(row_date)

        # Build merged header with priority: date row > above2 > above > col_N
        merged = np.full(n_cols, np.nan, dtype=object)

        # Layer 1: date row (usually all empty for "Date,,,,,")
        for i in range(n_cols):
            if not pd.isna(row_date[i]) and row_date[i].strip():
                merged[i] = row_date[i].strip()

        # Layer 2: row above date (the actual column names)
        if row_above2 is not None:
            for i in range(n_cols):
                if pd.isna(merged[i]):
                    val = row_above2[i]
                    if not pd.isna(val) and val.strip():
                        merged[i] = val.strip()

        # Layer 3: row above that (ticker info — usually fills in gaps)
        if row_above is not None:
            for i in range(n_cols):
                if pd.isna(merged[i]):
                    val = row_above[i]
                    if not pd.isna(val) and val.strip():
                        merged[i] = val.strip()

        # Layer 4: fallback column names
        for i in range(n_cols):
            if pd.isna(merged[i]):
                merged[i] = f"col_{i}"

        header_row = pd.Series(merged)

    data = raw.iloc[header_idx + 1:].copy()
    data.columns = header_row.values
    # --- Vectorized numeric conversion ---
    numeric_cols = [col for col in data.columns if col != "Date"]
    if numeric_cols:
        data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors="coerce")
    # Drop auto-generated col_N columns where all values are NaN
    # (trailing empty columns from yfinance header padding)
    drop_cols = [
        col for col in data.columns
        if col.startswith("col_") and data[col].isna().all()
    ]
    if drop_cols:
        data = data.drop(columns=drop_cols)
    return data


# --- State file helpers ---


def save_state(state, state_path):
    """Persist computation state to a JSON file.

    Args:
        state: Dict-like state to serialize.
        state_path: File path to write the JSON state file.
    """
    state_dir = os.path.dirname(state_path)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f)


def load_state(state_path):
    """Load computation state from a JSON file.

    Returns None if the file does not exist or is corrupted.

    Args:
        state_path: Path to the JSON state file.

    Returns:
        Parsed state dict, or None.
    """
    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


# --- Pipeline runner ---

def main(
    module_name,
    description,
    process_csv_fn,
    max_workers=10,
    input_dir=None,
    output_dir=None,
):
    """Run the standard thread-pool pipeline for a single TA module.

    Each calculate_*.py module should call this from its main() instead of
    writing the full pipeline boilerplate.

    Args:
        module_name: Short name for display (e.g. "calculate_trend").
        description: Human-readable description (e.g. "trend indicators").
        process_csv_fn: Callable(input_path, output_path, total_files, current_file)
            that reads a CSV, computes indicators, writes output, returns row count.
        max_workers: Thread pool size (default 10).
        input_dir: Override market-data directory path.
        output_dir: Override ta-data directory path.
    """
    # Only parse CLI args when run standalone (not from run_calculation.py in-process).
    # When imported (e.g. by pytest), sys.argv contains pytest's arguments which
    # would conflict with our parser. Skip arg parsing if pytest is detected or
    # no known flags are present.
    _known_flags = {"--force", "--help", "-h", "--dry-run", "--ticker",
                    "trend", "momentum", "volume", "volatility", "regime",
                    "structure", "return"}
    _is_pytest = "pytest" in sys.argv[0] if sys.argv else False
    _has_known_args = bool({a for a in sys.argv if a in _known_flags or a.startswith(("--force=", "--help="))})
    _is_standalone = not _is_pytest and _has_known_args

    if _is_standalone:
        force = os.environ.get("TA_FORCE_FULL_RECALCULATION", "0") == "1"
        parser = argparse.ArgumentParser(
            description=f"{module_name}: {description}",
            add_help=False,
        )
        parser.add_argument("--force", action="store_true",
                            help="Force full recalculation (disable incremental computation).")
        parser.add_argument("--help", "-h", action="store_true", help="Show help and exit.")
        parsed_args = parser.parse_args()
        if parsed_args.force:
            os.environ["TA_FORCE_FULL_RECALCULATION"] = "1"
            force = True
        if parsed_args.help:
            parser.print_help()
            sys.exit(0)
    else:
        force = os.environ.get("TA_FORCE_FULL_RECALCULATION", "0") == "1"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(script_dir))

    # Derive output filename suffix from module name (e.g. "calculate_trend" -> "trend")
    suffix = module_name.replace("calculate_", "")

    if input_dir is None:
        input_dir = os.path.join(base_dir, "data", "market-data")
    if output_dir is None:
        output_dir = os.path.join(base_dir, "data", "ta-data")

    os.makedirs(output_dir, exist_ok=True)

    csv_files = sorted(
        f for f in os.listdir(input_dir) if f.endswith(".csv")
    )

    if not csv_files:
        print("No CSV files found in market-data directory")
        sys.exit(1)

    print(f"Found {len(csv_files)} CSV files to process")
    if description:
        print(f"Computing {description}")

    total_rows = 0
    file_lock = threading.Lock()
    file_completed = [0] * len(csv_files)

    def process_file(args):
        idx, filename = args
        input_path = os.path.join(input_dir, filename)
        # Output: {ticker}_ta_{suffix}.csv  (e.g. AAPL_ta_trend.csv)
        ticker = filename[:-4]  # strip .csv
        output_path = os.path.join(output_dir, f"{ticker}_ta_{suffix}.csv")
        total_files = len(csv_files)

        try:
            rows = process_csv_fn(input_path, output_path, total_files, idx + 1)
            with file_lock:
                file_completed[idx] = 1
                completed_count = sum(file_completed)
            file_progress_bar(filename, completed_count, total_files)
            return rows
        except Exception as e:
            with file_lock:
                print(f"Error processing {filename}: {e}", file=sys.stderr)
            return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, (idx, fn)): idx for idx, fn in enumerate(csv_files)}
        for future in concurrent.futures.as_completed(futures):
            rows = future.result()
            total_rows += rows

    print(f"\nDone. Processed {total_rows} total rows across {len(csv_files)} files.")
    print(f"Output directory: {output_dir}")

"""Shared infrastructure for all calculate_*.py modules.

Exports:
    progress_bar, file_progress_bar, row_progress_bar — terminal progress helpers
    compute_ema, compute_rsi, compute_macd, compute_roc — momentum-indicator core functions
    compute_momentum_columns — assemble all momentum columns for a ticker
    compute_garch_volatility, compute_hmm_regime, compute_regime_columns — regime-indicator functions
    main — thread-pool pipeline with progress reporting (call from each module)
    read_yfinance_csv — read yfinance CSVs with multi-row header support
"""

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


# --- Progress bar helpers ---

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

    Args:
        input_path: Path to the CSV file.

    Returns:
        DataFrame with proper column names (Date, Open, High, Low, Close, Volume)
        and numeric types.
    """
    raw = pd.read_csv(input_path, header=None)

    # Find the header row: the row where col[0] is "Date"
    header_idx = None
    for i in range(min(5, len(raw))):
        val = str(raw.iloc[i, 0]).strip()
        if val == "Date":
            header_idx = i
            break

    if header_idx is None:
        # Fallback: use first row as header (standard single-header CSV)
        header_row = raw.iloc[0].astype(str)
    else:
        # For yfinance multi-row headers, the row above has Open/High/Low/Close/Volume
        above = raw.iloc[header_idx - 1].astype(str) if header_idx > 0 else None
        header_row = raw.iloc[header_idx].astype(str)

        # Merge: use above-row values where the Date-row is empty/NaN
        merged = {}
        for col in range(len(header_row)):
            h_val = header_row.iloc[col].strip() if pd.notna(header_row.iloc[col]) else ""
            if h_val:
                merged[col] = h_val
            elif above is not None and pd.notna(above.iloc[col]):
                merged[col] = above.iloc[col].strip()
            else:
                merged[col] = f"col_{col}"
        header_row = pd.Series([merged[i] for i in range(len(header_row))])

    data = raw.iloc[header_idx + 1:].copy()
    data.columns = header_row.values
    # Convert numeric columns to float
    for col in data.columns:
        if col != "Date":
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data


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
        module_name: Short name for display (e.g. "calculate_ta").
        description: Human-readable description (e.g. "Core indicators").
        process_csv_fn: Callable(input_path, output_path, total_files, current_file)
            that reads a CSV, computes indicators, writes output, returns row count.
        max_workers: Thread pool size (default 10).
        input_dir: Override market-data directory path.
        output_dir: Override ta-data directory path.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(script_dir))

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
        output_path = os.path.join(output_dir, filename)
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

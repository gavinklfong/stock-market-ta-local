import os
import sys
import math
import threading
import concurrent.futures
import pandas as pd
import shutil
import time


_bar_state = {"last_row_lines": {}}
_row_lock = threading.Lock()


def progress_bar(current, total, prefix="", bar_length=40):
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
    progress_bar(
        current, total,
        prefix=f"[{current}/{total}] {filename}: ",
    )


def row_progress_bar(filename, total_rows, current_row):
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
    raw_df = pd.read_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()

    # Merge with existing TA data if available (preserves columns from calculate_ta.py and calculate_trend.py)
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        # Recompute momentum columns aligned to the sorted existing data
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        closes = raw_df["Close"].tolist()
    else:
        df = raw_df.copy()

    momentum_cols = compute_momentum_columns(closes, file_total)
    for col, values in momentum_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    # Progress updates
    for i in range(file_total):
        if (i + 1) % max(1, file_total // 50) == 0 or i == file_total - 1:
            row_progress_bar(os.path.basename(input_path), file_total, i + 1)

    df.to_csv(output_path, index=False)
    return len(df)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    input_dir = os.path.join(base_dir, "data", "market-data")
    output_dir = os.path.join(base_dir, "data", "ta-data")

    os.makedirs(output_dir, exist_ok=True)

    csv_files = sorted(
        f for f in os.listdir(input_dir) if f.endswith(".csv")
    )

    if not csv_files:
        print("No CSV files found in market-data directory")
        sys.exit(1)

    print(f"Found {len(csv_files)} CSV files to process")
    print(f"Computing momentum indicators: RSI(14), MACD, ROC(20)")

    total_rows = 0
    file_lock = threading.Lock()
    file_completed = [0] * len(csv_files)

    def process_file(args):
        idx, filename = args
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        total_files = len(csv_files)
        lock = file_lock

        try:
            rows = process_csv(input_path, output_path, total_files, idx + 1, _lock=lock)
            with lock:
                file_completed[idx] = 1
                completed_count = sum(file_completed)
            with lock:
                file_progress_bar(filename, completed_count, total_files)
            return rows
        except Exception as e:
            with lock:
                print(f"Error processing {filename}: {e}", file=sys.stderr)
            return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_file, (idx, fn)): idx for idx, fn in enumerate(csv_files)}
        for future in concurrent.futures.as_completed(futures):
            rows = future.result()
            total_rows += rows

    print(f"\nDone. Processed {total_rows} total rows across {len(csv_files)} files.")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()

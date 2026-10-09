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


def compute_obv(closes, volumes):
    """Compute On-Balance Volume. Returns a list aligned with input."""
    n = len(closes)
    result = [0.0] * n
    if n < 1:
        return result

    result[0] = float(volumes[0])
    for i in range(1, n):
        if float(closes[i]) > float(closes[i - 1]):
            result[i] = result[i - 1] + float(volumes[i])
        elif float(closes[i]) < float(closes[i - 1]):
            result[i] = result[i - 1] - float(volumes[i])
        else:
            result[i] = result[i - 1]

    return result


def compute_cmf(highs, lows, closes, volumes, period=20):
    """Compute Chaikin Money Flow. Returns a list aligned with input."""
    n = len(highs)
    result = [None] * n
    if n < period:
        return result

    mfv_sums = [0.0] * period
    vol_sums = [0.0] * period

    for i in range(period):
        high_i = float(highs[i])
        low_i = float(lows[i])
        vol_i = float(volumes[i])
        if high_i != low_i:
            mfv = ((float(closes[i]) - low_i) - (high_i - float(closes[i]))) / (high_i - low_i)
        else:
            mfv = 0.0
        mfv_sums[i] = mfv * vol_i
        vol_sums[i] = vol_i

    for i in range(period - 1, n):
        if vol_sums[i % period] != 0:
            result[i] = mfv_sums[i % period] / vol_sums[i % period]
        else:
            result[i] = 0.0

    # Slide window
    for i in range(period, n):
        idx = i % period
        high_i = float(highs[i])
        low_i = float(lows[i])
        vol_i = float(volumes[i])
        if high_i != low_i:
            mfv = ((float(closes[i]) - low_i) - (high_i - float(closes[i]))) / (high_i - low_i)
        else:
            mfv = 0.0
        mfv_sums[idx] = mfv * vol_i
        vol_sums[idx] = vol_i

        rolling_mfv_sum = sum(mfv_sums)
        rolling_vol_sum = sum(vol_sums)

        if rolling_vol_sum != 0:
            result[i] = rolling_mfv_sum / rolling_vol_sum
        else:
            result[i] = 0.0

    return result


def compute_vwap(highs, lows, closes, volumes):
    """Compute cumulative Volume-Weighted Average Price. Returns a list aligned with input."""
    n = len(highs)
    result = [None] * n
    if n < 1:
        return result

    cumulative_tp_vol = 0.0
    cumulative_vol = 0.0

    for i in range(n):
        typical_price = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        vol = float(volumes[i])
        cumulative_tp_vol += typical_price * vol
        cumulative_vol += vol
        if cumulative_vol > 0:
            result[i] = cumulative_tp_vol / cumulative_vol

    return result


def compute_volume_columns(highs, lows, closes, volumes, n):
    """Compute all volume indicator columns for a single ticker's data."""
    ta_obv = compute_obv(closes, volumes)
    ta_cmf = compute_cmf(highs, lows, closes, volumes) if n >= 20 else [None] * n
    ta_vwap = compute_vwap(highs, lows, closes, volumes)

    return {
        "ta_obv": ta_obv,
        "ta_cmf": ta_cmf,
        "ta_vwap": ta_vwap,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = pd.read_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    closes = raw_df["Close"].tolist()
    volumes = raw_df["Volume"].tolist()

    # Merge with existing TA data if available (preserves columns from calculate_ta.py,
    # calculate_trend.py, and calculate_momentum.py)
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        highs = raw_df["High"].tolist()
        lows = raw_df["Low"].tolist()
        closes = raw_df["Close"].tolist()
        volumes = raw_df["Volume"].tolist()
    else:
        df = raw_df.copy()

    volume_cols = compute_volume_columns(highs, lows, closes, volumes, file_total)
    for col, values in volume_cols.items():
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
    print(f"Computing volume indicators: OBV, CMF(20), VWAP")

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

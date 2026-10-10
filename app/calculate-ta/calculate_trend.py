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


def compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0):
    """Compute SuperTrend indicator.
    
    Returns dict with:
      - supertrend: list of SuperTrend line values
      - direction: +1 for uptrend (price above ST), -1 for downtrend (price below ST)
      - upper_band: the upper band line (used when in downtrend)
      - lower_band: the lower band line (used when in uptrend)
    """
    atr = compute_atr(highs, lows, closes, atr_period)
    n = len(highs)
    
    # Mid point
    mid = [(highs[i] + lows[i]) / 2.0 for i in range(n)]
    
    # Raw bands
    upper_band_raw = [None] * n
    lower_band_raw = [None] * n
    for i in range(n):
        if atr[i] is not None:
            upper_band_raw[i] = mid[i] + multiplier * atr[i]
            lower_band_raw[i] = mid[i] - multiplier * atr[i]
    
    # Smooth bands: upper band only goes up, lower band only goes down
    upper_band = [None] * n
    lower_band = [None] * n
    
    for i in range(n):
        if upper_band_raw[i] is None or lower_band_raw[i] is None:
            continue
        if i == 0:
            upper_band[i] = upper_band_raw[i]
            lower_band[i] = lower_band_raw[i]
        else:
            # Upper band: only decrease if current raw < previous, else keep previous
            if upper_band[i - 1] is not None:
                upper_band[i] = min(upper_band_raw[i], upper_band[i - 1])
            else:
                upper_band[i] = upper_band_raw[i]
            # Lower band: only increase if current raw > previous, else keep previous
            if lower_band[i - 1] is not None:
                lower_band[i] = max(lower_band_raw[i], lower_band[i - 1])
            else:
                lower_band[i] = lower_band_raw[i]
    
    # Direction: +1 = uptrend, -1 = downtrend
    direction = [0] * n
    supertrend = [None] * n
    
    for i in range(n):
        if upper_band[i] is None or lower_band[i] is None:
            continue
        
        if i == 0:
            if closes[i] > lower_band[i]:
                direction[i] = 1
                supertrend[i] = lower_band[i]
            else:
                direction[i] = -1
                supertrend[i] = upper_band[i]
            continue
        
        if direction[i - 1] == 1:
            # Was in uptrend: stay up if close > lower_band, flip to down if close < lower_band
            if closes[i] <= lower_band[i]:
                direction[i] = -1
                supertrend[i] = upper_band[i]
            else:
                direction[i] = 1
                supertrend[i] = lower_band[i]
        else:
            # Was in downtrend: stay down if close < upper_band, flip to up if close > upper_band
            if closes[i] >= upper_band[i]:
                direction[i] = 1
                supertrend[i] = lower_band[i]
            else:
                direction[i] = -1
                supertrend[i] = upper_band[i]
    
    return {
        "supertrend": supertrend,
        "direction": direction,
        "upper_band": upper_band,
        "lower_band": lower_band,
    }


def compute_trend_columns(highs, lows, closes, n):
    """Compute all trend indicator columns for a single ticker's data."""
    ta_ema20 = compute_ema(closes, 20) if n >= 20 else [None] * n
    ta_ema50 = compute_ema(closes, 50) if n >= 50 else [None] * n
    ta_ema200 = compute_ema(closes, 200) if n >= 200 else [None] * n
    st = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)
    
    return {
        "ta_ema20": ta_ema20,
        "ta_ema50": ta_ema50,
        "ta_ema200": ta_ema200,
        "ta_supertrend": st["supertrend"],
        "ta_supertrend_direction": st["direction"],
        "ta_supertrend_upper": st["upper_band"],
        "ta_supertrend_lower": st["lower_band"],
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = pd.read_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()

    # Merge with existing TA data if available (preserves columns from calculate_ta.py)
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        # Recompute trend columns aligned to the sorted existing data
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        closes = raw_df["Close"].tolist()
        highs = raw_df["High"].tolist()
        lows = raw_df["Low"].tolist()
    else:
        df = raw_df.copy()

    trend_cols = compute_trend_columns(highs, lows, closes, file_total)
    for col, values in trend_cols.items():
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
    print(f"Computing trend indicators: EMA20, EMA50, EMA200, SuperTrend")

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

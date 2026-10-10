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


def detect_swings(highs, lows, lookback=5):
    """Detect swing highs and swing lows using pivot point approach.

    A swing high at index i: high[i] >= max(high[i-lookback:i]) AND high[i] >= max(high[i+1:i+lookback+1])
    A swing low at index i: low[i] <= min(low[i-lookback:i]) AND low[i] <= min(low[i+1:i+lookback+1])

    Returns:
        swing_high: list of True/False per bar
        swing_low: list of True/False per bar
    """
    n = len(highs)
    swing_high = [False] * n
    swing_low = [False] * n

    for i in range(lookback, n - lookback):
        # Check swing high
        window_before = highs[i - lookback:i]
        window_after = highs[i + 1:i + lookback + 1]
        if highs[i] >= max(window_before) and highs[i] >= max(window_after):
            swing_high[i] = True

        # Check swing low
        window_before_low = lows[i - lookback:i]
        window_after_low = lows[i + 1:i + lookback + 1]
        if lows[i] <= min(window_before_low) and lows[i] <= min(window_after_low):
            swing_low[i] = True

    return swing_high, swing_low


def find_last_swing(swing_flags, current_idx, direction=-1):
    """Find the last swing flag (True) at or before/after current_idx.

    direction=-1: search backwards from current_idx
    direction=1: search forwards from current_idx
    """
    if direction == -1:
        for i in range(current_idx, -1, -1):
            if swing_flags[i]:
                return i
    else:
        for i in range(current_idx, len(swing_flags)):
            if swing_flags[i]:
                return i
    return -1


def compute_structure(highs, lows, lookback=5):
    """Detect swing highs, swing lows, HH/HL/LH/LL, BOS, CHoCH.

    Returns:
        swing_high: list of price at swing high bar, or None
        swing_low: list of price at swing low bar, or None
        swing_high_idx: list of index of swing high, or -1
        swing_low_idx: list of index of swing low, or -1
        hh: 1 if Higher High, else 0
        hl: 1 if Higher Low, else 0
        lh: 1 if Lower High, else 0
        ll: 1 if Lower Low, else 0
        trend: 1 bullish, -1 bearish, 0 undetermined
        bos: 1 break of structure (continuation), else 0
        choch: 1 change of character (reversal), else 0
    """
    n = len(highs)
    swing_high_flags, swing_low_flags = detect_swings(highs, lows, lookback)

    # Build output lists
    swing_high = [None] * n
    swing_low = [None] * n
    swing_high_idx = [-1] * n
    swing_low_idx = [-1] * n
    hh = [0] * n
    hl = [0] * n
    lh = [0] * n
    ll = [0] * n
    trend = [0] * n
    bos = [0] * n
    choch = [0] * n

    # Track the last confirmed swing high/low price and index
    last_sh_idx = -1
    last_sl_idx = -1
    last_sh_price = None
    last_sl_price = None

    # Track trend state
    # We determine trend by comparing the most recent swing structure
    last_trend = 0

    for i in range(n):
        # Update swing high/low references
        if swing_high_flags[i]:
            last_sh_idx = i
            last_sh_price = highs[i]
        if swing_low_flags[i]:
            last_sl_idx = i
            last_sl_price = lows[i]

        swing_high_idx[i] = last_sh_idx
        swing_low_idx[i] = last_sl_idx
        swing_high[i] = last_sh_price
        swing_low[i] = last_sl_price

        # HH/HL/LH/LL detection requires at least 2 swings
        if last_sh_idx >= 0 and last_sl_idx >= 0:
            # Determine the last swing type before this bar
            # Find the most recent swing high index before this bar
            prev_sh_idx = -1
            prev_sl_idx = -1
            for j in range(i - 1, max(i - 2 * lookback - 1, -1), -1):
                if swing_high_flags[j] and j != last_sh_idx:
                    prev_sh_idx = j
                    break
                if swing_low_flags[j] and j != last_sl_idx:
                    prev_sl_idx = j
                    break
                # If we've gone far enough without finding another swing, stop
                if j < max(last_sh_idx, last_sl_idx) - lookback * 3 and last_sh_idx >= 0 and last_sl_idx >= 0:
                    break

            # Actually, let's use a simpler approach:
            # Compare current swing high to previous swing high
            # Compare current swing low to previous swing low
            if last_sh_idx > 0 and swing_high_flags[i]:
                # Current bar is a swing high; find previous swing high
                prev_sh_idx = -1
                for j in range(i - 1, max(i - lookback * 3 - 1, -1), -1):
                    if swing_high_flags[j]:
                        prev_sh_idx = j
                        break
                if prev_sh_idx > 0:
                    if highs[i] > highs[prev_sh_idx]:
                        hh[i] = 1
                    else:
                        lh[i] = 1

            if last_sl_idx > 0 and swing_low_flags[i]:
                # Current bar is a swing low; find previous swing low
                prev_sl_idx = -1
                for j in range(i - 1, max(i - lookback * 3 - 1, -1), -1):
                    if swing_low_flags[j]:
                        prev_sl_idx = j
                        break
                if prev_sl_idx > 0:
                    if lows[i] > lows[prev_sl_idx]:
                        hl[i] = 1
                    else:
                        ll[i] = 1

        # BOS and CHoCH: detect based on swing structure
        if last_sh_idx >= lookback and last_sl_idx >= lookback:
            # Find the two most recent swing highs before current position
            recent_sh = []
            for j in range(i, -1, -1):
                if swing_high_flags[j]:
                    recent_sh.append(j)
                    if len(recent_sh) >= 2:
                        break

            # Find the two most recent swing lows before current position
            recent_sl = []
            for j in range(i, -1, -1):
                if swing_low_flags[j]:
                    recent_sl.append(j)
                    if len(recent_sl) >= 2:
                        break

            if len(recent_sh) >= 2:
                prev_sh_idx = recent_sh[1]
                curr_sh_idx = recent_sh[0]
                # BOS: new HH continues uptrend
                if highs[curr_sh_idx] > highs[prev_sh_idx]:
                    bos[curr_sh_idx] = 1
                    if last_trend != 1:
                        if last_trend != 0:
                            choch[curr_sh_idx] = 1  # reversal to bullish
                        last_trend = 1
                else:
                    # Lower high - potential downtrend
                    if highs[curr_sh_idx] < highs[prev_sh_idx]:
                        if last_trend == 1:
                            choch[curr_sh_idx] = 1  # reversal from bullish
                        last_trend = -1

            if len(recent_sl) >= 2:
                prev_sl_idx = recent_sl[1]
                curr_sl_idx = recent_sl[0]
                # BOS: new LL continues downtrend
                if lows[curr_sl_idx] < lows[prev_sl_idx]:
                    bos[curr_sl_idx] = 1
                    if last_trend != -1:
                        if last_trend != 0:
                            choch[curr_sl_idx] = 1  # reversal to bearish
                        last_trend = -1
                else:
                    # Higher low - potential uptrend
                    if lows[curr_sl_idx] > lows[prev_sl_idx]:
                        if last_trend == -1:
                            choch[curr_sl_idx] = 1  # reversal from bearish
                        last_trend = 1

        trend[i] = last_trend

    return {
        "swing_high": swing_high,
        "swing_low": swing_low,
        "swing_high_idx": swing_high_idx,
        "swing_low_idx": swing_low_idx,
        "hh": hh,
        "hl": hl,
        "lh": lh,
        "ll": ll,
        "trend": trend,
        "bos": bos,
        "choch": choch,
    }


def compute_support_resistance(highs, lows, swings, lookback=5, tolerance_pct=0.02):
    """Compute nearest support and resistance levels based on swing points.

    Clusters nearby swing highs/lows within tolerance_pct of each other
    and finds the nearest level above/below the current price.

    Args:
        highs: list of high prices
        lows: list of low prices
        swings: dict from compute_structure() containing swing_high/low flags
        lookback: number of recent bars to consider
        tolerance_pct: price proximity threshold for clustering (2%)

    Returns:
        resistance: list of nearest resistance price, or None
        support: list of nearest support price, or None
    """
    n = len(highs)
    swing_high_flags, swing_low_flags = swings["swing_high"], swings["swing_low"]

    # Collect all swing high prices and their indices
    swing_highs = [(i, highs[i]) for i in range(n) if swing_high_flags[i]]
    swing_lows = [(i, lows[i]) for i in range(n) if swing_low_flags[i]]

    # Cluster swing highs into resistance levels
    resistance_levels = _cluster_levels(swing_highs, tolerance_pct)
    # Cluster swing lows into support levels
    support_levels = _cluster_levels(swing_lows, tolerance_pct)

    resistance = [None] * n
    support = [None] * n

    for i in range(n):
        close = (highs[i] + lows[i]) / 2.0

        # Find nearest resistance above current price
        nearest_res = None
        for level_price in resistance_levels:
            if level_price > close:
                if nearest_res is None or level_price < nearest_res:
                    nearest_res = level_price
        resistance[i] = nearest_res

        # Find nearest support below current price
        nearest_sup = None
        for level_price in support_levels:
            if level_price < close:
                if nearest_sup is None or level_price > nearest_sup:
                    nearest_sup = level_price
        support[i] = nearest_sup

    return resistance, support


def _cluster_levels(points, tolerance_pct=0.02):
    """Cluster nearby price levels into resistance/support zones.

    Args:
        points: list of (index, price) tuples
        tolerance_pct: proximity threshold

    Returns:
        Sorted list of unique cluster center prices
    """
    if not points:
        return []

    prices = sorted(set(p for _, p in points))
    if not prices:
        return []

    clusters = []
    cluster_sum = prices[0]
    cluster_count = 1

    for i in range(1, len(prices)):
        prev_price = prices[i - 1]
        curr_price = prices[i]
        gap = abs(curr_price - prev_price) / prev_price

        if gap <= tolerance_pct:
            cluster_sum += curr_price
            cluster_count += 1
        else:
            clusters.append(cluster_sum / cluster_count)
            cluster_sum = curr_price
            cluster_count = 1

    # Don't forget the last cluster
    if cluster_count > 0:
        clusters.append(cluster_sum / cluster_count)

    return clusters


def compute_structure_columns(highs, lows, closes, n, lookback=5, tolerance_pct=0.02):
    """Compute all structure indicator columns for a single ticker's data."""
    if n < lookback * 2 + 1:
        # Not enough data for any structure detection
        empty = [None] * n
        zero = [0] * n
        return {
            "ta_swing_high": empty,
            "ta_swing_low": empty,
            "ta_swing_high_idx": [-1] * n,
            "ta_swing_low_idx": [-1] * n,
            "ta_hh": zero,
            "ta_hl": zero,
            "ta_lh": zero,
            "ta_ll": zero,
            "ta_trend": zero,
            "ta_bos": zero,
            "ta_choch": zero,
            "ta_nearest_resistance": empty,
            "ta_nearest_support": empty,
        }

    structure = compute_structure(highs, lows, lookback)
    resistance, support = compute_support_resistance(
        highs, lows, structure, lookback, tolerance_pct
    )

    return {
        "ta_swing_high": structure["swing_high"],
        "ta_swing_low": structure["swing_low"],
        "ta_swing_high_idx": structure["swing_high_idx"],
        "ta_swing_low_idx": structure["swing_low_idx"],
        "ta_hh": structure["hh"],
        "ta_hl": structure["hl"],
        "ta_lh": structure["lh"],
        "ta_ll": structure["ll"],
        "ta_trend": structure["trend"],
        "ta_bos": structure["bos"],
        "ta_choch": structure["choch"],
        "ta_nearest_resistance": resistance,
        "ta_nearest_support": support,
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = pd.read_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()
    n = file_total

    # Merge with existing TA data if available
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        n = file_total
        # Recompute structure columns aligned to the sorted existing data
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        closes = raw_df["Close"].tolist()
        highs = raw_df["High"].tolist()
        lows = raw_df["Low"].tolist()
    else:
        df = raw_df.copy()

    structure_cols = compute_structure_columns(highs, lows, closes, n)
    for col, values in structure_cols.items():
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
    print(f"Computing structure indicators: HH/HL/LH/LL, BOS, CHoCH, Support/Resistance")

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

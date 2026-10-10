import os
import sys
import math
import threading
import concurrent.futures
import warnings

import numpy as np
import pandas as pd
import shutil

# Suppress arch/hmmlearn noise during fitting
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

from arch import arch_model
from hmmlearn.hmm import GaussianHMM


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


def compute_garch_volatility(closes, p=1, q=1):
    """Compute GARCH(p,q) volatility from close prices.

    Fits a GARCH model via MLE and extracts conditional volatility
    for each bar in the historical series.

    Args:
        closes: list/array of close prices.
        p: ARCH order (number of lagged squared residuals).
        q: GARCH order (number of lagged variances).

    Returns:
        dict with:
            ta_garch_vol   — conditional volatility (std dev form, σₜ)
            ta_garch_sq    — conditional variance (σ²ₜ)
    """
    n = len(closes)
    if n < max(p, q) + 10:
        return {
            "ta_garch_vol": [None] * n,
            "ta_garch_sq": [None] * n,
        }

    # Compute log returns
    log_returns = np.zeros(n)
    for i in range(1, n):
        if closes[i - 1] > 0 and closes[i] > 0:
            log_returns[i] = math.log(closes[i] / closes[i - 1])
        else:
            log_returns[i] = 0.0

    # Drop first element (NaN/zero return at t=0)
    r = log_returns[1:]

    if len(r) < 30:
        return {
            "ta_garch_vol": [None] * n,
            "ta_garch_sq": [None] * n,
        }

    try:
        model = arch_model(r, vol="Garch", p=p, q=q, mean="Zero",
                           dist="normal")
        result = model.fit(disp="off", options={"maxiter": 1000})
        cv = result.conditional_volatility
        cond_vol = cv.flatten() if hasattr(cv, "flatten") else np.asarray(cv).flatten()
        cond_var = cond_vol ** 2

        # Align back to original series: first element is None (no return)
        vol = [None] + cond_vol.tolist()
        sq = [None] + cond_var.tolist()
    except Exception:
        # If fitting fails, return all None
        vol = [None] * n
        sq = [None] * n

    return {
        "ta_garch_vol": vol,
        "ta_garch_sq": sq,
    }


def compute_hmm_regime(closes, n_states=3):
    """Compute Hidden Markov Model regime labels and probabilities.

    Fits a Gaussian HMM with n_states components on log returns,
    then labels the states post-hoc:
      - State with highest mean return → Bull (0)
      - State with lowest mean return  → Bear (1)
      - Remaining state               → Volatile (2)

    Args:
        closes: list/array of close prices.
        n_states: number of hidden states (default 3).

    Returns:
        dict with:
            ta_hmm_regime              — most likely state per bar (int, 0/1/2)
            ta_hmm_regime_prob_0       — P(Bull) per bar
            ta_hmm_regime_prob_1       — P(Bear) per bar
            ta_hmm_regime_prob_2       — P(Volatile) per bar
    """
    n = len(closes)
    if n < n_states * 10:
        empty = [None] * n
        return {
            "ta_hmm_regime": empty,
            "ta_hmm_regime_prob_0": empty,
            "ta_hmm_regime_prob_1": empty,
            "ta_hmm_regime_prob_2": empty,
        }

    # Compute log returns
    log_returns = np.zeros(n)
    for i in range(1, n):
        if closes[i - 1] > 0 and closes[i] > 0:
            log_returns[i] = math.log(closes[i] / closes[i - 1])
        else:
            log_returns[i] = 0.0

    r = log_returns[1:]  # Drop first element (no return)

    if len(r) < n_states * 10:
        empty = [None] * n
        return {
            "ta_hmm_regime": empty,
            "ta_hmm_regime_prob_0": empty,
            "ta_hmm_regime_prob_1": empty,
            "ta_hmm_regime_prob_2": empty,
        }

    try:
        # Standardize returns for better fitting
        r_std = r.copy()
        mean_r = np.mean(r_std)
        std_r = np.std(r_std)
        if std_r > 0:
            r_standardized = (r_std - mean_r) / std_r
        else:
            r_standardized = r_std - mean_r

        # Reshape to 2D for hmmlearn
        X = r_standardized.reshape(-1, 1)

        # Fit Gaussian HMM
        model = GaussianHMM(
            n_components=n_states,
            covariance_type="full",
            n_iter=100,
            random_state=42,
        )
        model.fit(X)

        # Viterbi decoding: most likely state sequence
        states = model.predict(X)

        # Posterior probabilities
        posteriors = model.predict_proba(X)  # shape (n-1, n_states)

        # Label states post-fit based on emission parameters
        # Mean return per hidden state (on original, unstandardized scale)
        means = model.means_.flatten()
        sorted_indices = np.argsort(means)

        # Build label map: remap learned state indices to semantic labels
        if n_states == 3:
            # sorted_indices[2] → highest mean → Bull (0)
            # sorted_indices[0] → lowest mean  → Bear (1)
            # sorted_indices[1] → middle mean  → Volatile (2)
            label_map = np.empty(n_states, dtype=int)
            label_map[sorted_indices[0]] = 1  # Bear
            label_map[sorted_indices[2]] = 0  # Bull
            label_map[sorted_indices[1]] = 2  # Volatile
        elif n_states == 2:
            # Two-state: Bull/Bear
            label_map = np.empty(n_states, dtype=int)
            label_map[sorted_indices[0]] = 1  # Bear (lowest mean)
            label_map[sorted_indices[1]] = 0  # Bull (highest mean)
        else:
            # Generic fallback: highest mean → 0, lowest → 1, rest → 2+
            label_map = np.empty(n_states, dtype=int)
            label_map[sorted_indices[0]] = 1  # Bear
            label_map[sorted_indices[-1]] = 0  # Bull
            for i, idx in enumerate(sorted_indices):
                if idx not in (sorted_indices[0], sorted_indices[-1]):
                    label_map[idx] = i  # sequential for extras

        # Remap Viterbi states to labeled states
        labeled_states = np.array([label_map[s] for s in states])

        # Remap posteriors: columns in labeled order
        labeled_probs = np.empty_like(posteriors)
        for src_idx in range(n_states):
            labeled_probs[:, label_map[src_idx]] = posteriors[:, src_idx]

        # Align back to original series (first element is None)
        regime = [None] + labeled_states.tolist()
        prob_bull = [None] + labeled_probs[:, 0].tolist()
        prob_bear = [None] + labeled_probs[:, 1].tolist()
        # prob_2 only exists for n_states >= 3
        if n_states >= 3:
            prob_volatile = [None] + labeled_probs[:, 2].tolist()
        else:
            prob_volatile = [None] * n

    except Exception:
        regime = [None] * n
        prob_bull = [None] * n
        prob_bear = [None] * n
        prob_volatile = [None] * n

    return {
        "ta_hmm_regime": regime,
        "ta_hmm_regime_prob_0": prob_bull,
        "ta_hmm_regime_prob_1": prob_bear,
        "ta_hmm_regime_prob_2": prob_volatile,
    }


def compute_regime_columns(closes, n):
    """Compute all regime indicator columns for a single ticker's data.

    Args:
        closes: list/array of close prices.
        n: number of bars (usually len(closes), but may differ if merging).

    Returns:
        dict of column_name → list of values, aligned to length n.
    """
    garch_cols = compute_garch_volatility(closes)
    hmm_cols = compute_hmm_regime(closes)

    # Ensure all columns are length n (trim or pad if needed)
    result = {}
    for col, values in {**garch_cols, **hmm_cols}.items():
        if len(values) > n:
            result[col] = values[:n]
        elif len(values) < n:
            result[col] = values + [None] * (n - len(values))
        else:
            result[col] = values

    return result


def _read_yfinance_csv(input_path):
    """Read a yfinance CSV, handling 2-row or 3-row header formats.

    yfinance CSVs have header rows like:
      Row 0: Ticker,NG.L,NG.L,NG.L,NG.L,NG.L
      Row 1: Price,Open,High,Low,Close,Volume
      Row 2: Date,,,,,  (3-row only)
      Row 3+: actual data
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


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = _read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()
    n = file_total

    # Merge with existing TA data if available (preserves columns from prior modules)
    if os.path.exists(output_path):
        df = pd.read_csv(output_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        file_total = len(df)
        n = file_total
        # Realign closes to the sorted existing data
        raw_df = raw_df.sort_values("Date").reset_index(drop=True)
        closes = raw_df["Close"].tolist()
    else:
        df = raw_df.copy()

    regime_cols = compute_regime_columns(closes, n)
    for col, values in regime_cols.items():
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
    print(f"Computing regime indicators: GARCH(1,1) volatility, 3-state HMM")

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

import json
import math
import os
import warnings

import numpy as np
import pandas as pd

from common import main, read_yfinance_csv

# Suppress arch/hmmlearn/scipy noise during fitting
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*optimizer.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="hmmlearn")

from arch import arch_model
from hmmlearn.hmm import GaussianHMM


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

    # Compute log returns (also exposed as ta_log_return output column)
    ta_log_return = [None] * n
    log_returns = np.zeros(n)
    for i in range(1, n):
        if closes[i - 1] > 0 and closes[i] > 0:
            log_returns[i] = math.log(closes[i] / closes[i - 1])
            ta_log_return[i] = log_returns[i]
        else:
            log_returns[i] = 0.0

    # Drop first element (NaN/zero return at t=0)
    r = log_returns[1:]

    if len(r) < 30:
        return {
            "ta_garch_vol": [None] * n,
            "ta_garch_sq": [None] * n,
            "ta_log_return": ta_log_return,
        }

    try:
        with warnings.catch_warnings(record=True) as caught:
            # rescale=True lets arch internally normalize y for the optimizer,
            # suppressing the DataScaleWarning while keeping results in the
            # original log-return scale.
            warnings.simplefilter("always")
            # Seed numpy for deterministic MLE fitting (arch uses numba which
            # may read from numpy's RNG for numerical gradient computation)
            np.random.seed(42)
            model = arch_model(r, vol="Garch", p=p, q=q, mean="Zero",
                               dist="normal", rescale=True)
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
        with warnings.catch_warnings(record=True) as _caught:
            # Suppress hmmlearn/NumPy 2.5 deprecation warnings from C extensions
            warnings.simplefilter("always")

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

    # ta_log_return is already in garch_cols (exposed as output column)
    combined = {**garch_cols, **hmm_cols}

    # Ensure all columns are length n (trim or pad if needed)
    result = {}
    for col, values in combined.items():
        if len(values) > n:
            result[col] = values[:n]
        elif len(values) < n:
            result[col] = values + [None] * (n - len(values))
        else:
            result[col] = values

    return result


# =============================================================================
# State file helpers
# =============================================================================


def _save_state(state, state_path):
    """Persist computation state to a JSON file."""
    with open(state_path, "w") as f:
        json.dump(state, f)


def _load_state(state_path):
    """Load computation state from a JSON file."""
    if not os.path.exists(state_path):
        return None
    try:
        with open(state_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    """Process a single ticker's OHLCV data into regime indicator output.

    When a previous output file and state file exist, this function performs
    **incremental computation**: it only computes regime indicators for rows
    that were appended since the last run, greatly improving efficiency for
    tickers that gain new data points regularly.

    Parameters
    ----------
    input_path : str
        Path to the OHLCV CSV (yfinance format).
    output_path : str
        Path to write the regime indicator CSV.
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
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    # State file lives alongside the output CSV
    base, ext = os.path.splitext(output_path)
    state_path = base + "_state.json"

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
            # (safety net for corrupted previous state)
            pass  # fall through to full computation below
        else:
            # There are new rows — try incremental computation
            new_row_count = file_total - prev_row_count

            # Load state; if missing, fall back to full computation
            state = _load_state(state_path)
            if state is not None and state.get("_version") == 1:
                try:
                    # --- Incremental path ---
                    closes = raw_df["Close"].tolist()

                    # Full computation for all rows (GARCH/HMM need full history)
                    # We only write the new rows, but we compute full for
                    # correctness since model fitting requires all data.
                    all_cols = compute_regime_columns(closes, file_total)

                    # Build output for new rows only
                    df_new_full = pd.DataFrame({"Date": raw_df["Date"].iloc[prev_row_count:]})
                    for col, values in all_cols.items():
                        df_new_full[col] = values[prev_row_count:]

                    # Merge with old output
                    df_old = prev_df
                    merged = pd.concat([df_old, df_new_full.reset_index(drop=True)],
                                       ignore_index=True)

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
    n = file_total

    # Compute this module's TA columns only
    regime_cols = compute_regime_columns(closes, n)

    # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in regime_cols.items():
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


main(
    module_name="calculate_regime",
    description="regime detection: GARCH volatility + 3-state HMM, log return",
    process_csv_fn=process_csv,
)

#!/usr/bin/env python
"""Orchestrator for all calculate_*.py TA modules.

Runs all TA indicator modules in parallel within a single process:

    calculate_trend.py       – EMA, SuperTrend, MA, slopes, price/EMA distance
    calculate_momentum.py    – RSI, MACD, ROC, RSI Z-Score, RSI Percentile
    calculate_volume.py      – OBV, CMF, VWAP, OFI, Volume Oscillator
    calculate_volatility.py  – ATR, Bollinger Bands, ATR Percentile
    calculate_regime.py      – GARCH, HMM regime, log return
    calculate_structure.py   – Swing points, HH/HL/LH/LL, BOS, CHoCH, S/R
    calculate_return.py      – Forward 5d/10d/20d returns, rolling alpha/beta

Each module reads from data/market-data/*.csv and writes to
data/ta-data/{ticker}_ta_{type}.csv, which are then merged into
data/ta-data/{ticker}.csv.

Usage:
    python run_calculation.py                          # run all, in parallel
    python run_calculation.py trend momentum           # run specific modules
    python run_calculation.py --ticker NG.L            # specific ticker
    python run_calculation.py --ticker NG.L --ticker BP.L  # multiple tickers
    python run_calculation.py --help                   # show usage
"""

import argparse
import concurrent.futures
import inspect
import os
import sys
import threading
from pathlib import Path

import pandas as pd

# Import read_yfinance_csv early so it's available before modules are patched
import common as _common_for_read
_read_yfinance_csv = _common_for_read.read_yfinance_csv

MODULES = {
    "trend":       "calculate_trend.py",
    "momentum":    "calculate_momentum.py",
    "volume":      "calculate_volume.py",
    "volatility":  "calculate_volatility.py",
    "regime":      "calculate_regime.py",
    "structure":   "calculate_structure.py",
    "return":      "calculate_return.py",
}

ALL_ORDER = [
    "trend",
    "momentum",
    "volume",
    "volatility",
    "regime",
    "structure",
    "return",
]

DESCRIPTIONS = {
    "trend":       "trend indicators: EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA ratio, price/EMA distance, Aroon, ADX/DI, Donchian, Keltner",
    "momentum":    "momentum indicators: RSI(14), MACD, ROC(20), Williams %R, CCI, TSI, RSI Z-Score, RSI Percentile",
    "volume":      "volume indicators: OBV, CMF(20), VWAP, OFI, log volume, ADL, MFI(14), EMV(14), Volume Oscillator, Volume Z-Score, Volume Percentile",
    "volatility":  "volatility indicators: ATR(14), Bollinger Bands(20,2), Band Width(20), %B(20), Historical Volatility, Parkinson Volatility, ATR Stop Distance, ATR Position Size, Reward Risk Ratio, ATR Percentile",
    "regime":      "regime detection: GARCH volatility + 3-state HMM, log return",
    "structure":   "structure indicators: HH/HL/LH/LL, BOS, CHoCH, Support/Resistance",
    "return":      "future returns: 5d/10d/20d, rolling alpha/beta, relative strength",
}

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load_modules(script_dir: Path) -> dict[str, object]:
    """Import all calculate_*.py modules and return a dict of name → module.

    Each module has an unconditional main() call at the bottom that triggers
    the old subprocess pipeline. We prevent this by temporarily replacing
    common.main with a no-op before importing.
    """
    # Add script dir to path so 'from common import main' resolves
    sys.path.insert(0, str(script_dir))

    # Import common first so we can patch its main() before any calculate
    # module does 'from common import main'
    import common as _common_orig
    _original_main = _common_orig.main
    _common_orig.main = lambda **kwargs: None

    try:
        modules = {}
        for name, filename in MODULES.items():
            module_path = script_dir / filename
            if not module_path.exists():
                print(
                    f"[WARN] Skipping {name}: {module_path} not found",
                    file=sys.stderr,
                )
                continue
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    f"calculate_{name}", module_path
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                modules[name] = mod
            except Exception as e:
                print(
                    f"[WARN] Skipping {name}: failed to import ({e})",
                    file=sys.stderr,
                )
        return modules
    finally:
        _common_orig.main = _original_main


def _process_ticker_in_module(
    ticker: str,
    module_name: str,
    module,
    df: pd.DataFrame,
    output_dir: str,
    lock: object,
) -> tuple[str, int]:
    """Process a single (ticker, module) pair in-process.

    Accepts a pre-parsed DataFrame (shared cache from run_task) to avoid
    re-reading the OHLCV CSV for each module.

    Returns (ticker, row_count).
    """
    output_path = os.path.join(output_dir, f"{ticker}_ta_{module_name}.csv")

    # Call the module's process_csv directly (in-process, not subprocess).
    # All modules accept either a DataFrame (from cache) or a file path (standalone).
    fn = module.process_csv
    sig = inspect.signature(fn)
    if "lock" in sig.parameters:
        row_count = fn(df, output_path, len(df), 1, _lock=lock)
    else:
        row_count = fn(df, output_path, len(df), 1)

    return ticker, row_count


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def _merge_ticker(
    ticker: str,
    ticker_files: list[str],
    output_dir: Path,
    deleted_files: set,
    file_lock: object,
) -> tuple[str, int, int]:
    """Merge all per-module CSVs for one ticker into {ticker}.csv.

    Uses pd.concat(axis=1) for efficient column-wise concatenation.
    """
    frames: list[pd.DataFrame] = []
    for fname in sorted(ticker_files):
        fpath = output_dir / fname
        df = pd.read_csv(fpath)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        ta_cols = [c for c in df.columns if c.startswith("ta_")]
        frames.append(df[ta_cols])

    # Concat all columns at once instead of sequential merge
    merged = pd.concat(frames, axis=1)
    merged = merged.reset_index()
    merged["Date"] = merged["Date"].dt.strftime("%Y-%m-%d")
    merged = merged.sort_values("Date").reset_index(drop=True)
    merged.to_csv(output_dir / f"{ticker}.csv", index=False)

    n_cols = len([c for c in merged.columns if c != "Date"])
    n_rows = len(merged)

    # Clean up intermediate files (thread-safe)
    with file_lock:
        for fname in ticker_files:
            fpath = output_dir / fname
            if fname not in deleted_files:
                fpath.unlink()
                deleted_files.add(fname)

    return ticker, n_rows, n_cols


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Run all TA indicator modules in parallel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"\nAvailable modules:\n"
               + "\n".join(f"  {name:12s}  {DESCRIPTIONS[name]}" for name in ALL_ORDER),
    )
    parser.add_argument(
        "modules",
        nargs="*",
        choices=list(MODULES.keys()),
        help=(
            "Modules to run (default: all). "
            f"Available: {', '.join(MODULES.keys())}. "
            "All modules run in parallel."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be run without executing.",
    )
    parser.add_argument(
        "--ticker",
        action="append",
        metavar="TICKER",
        help=(
            "Ticker(s) to process. By default all tickers in market-data/ are used. "
            "Repeat for multiple tickers (e.g. --ticker NG.L --ticker BP.L)."
        ),
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir.parent.parent / "data" / "ta-data"

    # Resolve requested modules → ordered list (for display only)
    if args.modules:
        order = [m for m in ALL_ORDER if m in args.modules]
    else:
        order = list(ALL_ORDER)

    # Discover tickers from market-data dir
    input_dir = script_dir.parent.parent / "data" / "market-data"
    csv_files = sorted(
        f for f in os.listdir(input_dir) if f.endswith(".csv")
    ) if input_dir.exists() else []
    all_tickers = [f[:-4] for f in csv_files]  # strip .csv

    if not all_tickers:
        print("[ERROR] No ticker CSVs found in market-data directory", file=sys.stderr)
        sys.exit(1)

    # Filter to requested ticker(s) if specified
    if args.ticker:
        tickers = [t for t in args.ticker if t in all_tickers]
        missing = set(args.ticker) - set(all_tickers)
        if missing:
            print(
                f"[WARN] Ticker(s) not found in market-data/: {', '.join(sorted(missing))}",
                file=sys.stderr,
            )
    else:
        tickers = all_tickers

    print(f"\nTA Pipeline Runner")
    print(f"{'='*60}")
    print(f"  Scripts directory : {script_dir}")
    print(f"  Output directory  : {output_dir}")
    print(f"  Tickers to process: {', '.join(tickers)}")
    print(f"  Modules to run    : {', '.join(order)} (parallel)")
    print(f"{'='*60}")

    if args.dry_run:
        for name in order:
            print(f"  (dry-run) Would run: python {script_dir / MODULES[name]}")
        sys.exit(0)

    # --- Phase 1: Run all modules in-process in parallel ---
    print(f"\n[PHASE 1] Running modules in-process (shared thread pool)")

    # Load all modules (skip any that fail to import)
    loaded_modules = _load_modules(script_dir)
    available = [name for name in order if name in loaded_modules]
    skipped = [name for name in order if name not in loaded_modules]
    if skipped:
        print(f"  Skipped unavailable modules: {', '.join(skipped)}")
    print(f"  Loaded {len(available)} module(s)")

    total_tasks = len(tickers) * len(available)
    print(f"  Total tasks: {total_tasks} ({len(tickers)} tickers × {len(available)} modules)")
    print()

    # Shared state for OHLCV DataFrame cache and progress
    ohlcv_cache: dict[str, pd.DataFrame] = {}
    cache_lock = threading.Lock()
    file_lock = threading.Lock()
    file_completed = [0] * total_tasks

    def run_task(task_idx, ticker, module_name):
        """Wrapper to track progress and handle errors."""
        mod = loaded_modules[module_name]
        try:
            # Read CSV once per ticker (cached across modules)
            with cache_lock:
                if ticker not in ohlcv_cache:
                    csv_path = os.path.join(str(input_dir), f"{ticker}.csv")
                    ohlcv_cache[ticker] = _read_yfinance_csv(csv_path)
                df = ohlcv_cache[ticker]

            _, rows = _process_ticker_in_module(
                ticker, module_name, mod, df,
                str(output_dir), file_lock,
            )
            with file_lock:
                file_completed[task_idx] = 1
                completed_count = sum(file_completed)
            if completed_count % max(1, total_tasks // 20) == 0 or completed_count == total_tasks:
                pct = completed_count / total_tasks * 100
                sys.stdout.write(
                    f"\r  Progress: {completed_count}/{total_tasks} ({pct:.0f}%)  "
                )
                sys.stdout.flush()
            return True
        except Exception as e:
            print(f"\n  [ERROR] {ticker}/{module_name}: {e}", file=sys.stderr)
            return False

    # Calculate thread pool size: enough for parallel I/O + computation
    num_workers = min(max(4, len(available) * 2), max(8, os.cpu_count() * 2))

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        task_idx = 0
        # Module-first order: each module's tasks are submitted together
        # so all workers can stay busy as modules complete
        for module_name in available:
            for ticker in tickers:
                futures[executor.submit(run_task, task_idx, ticker, module_name)] = (
                    ticker, module_name
                )
                task_idx += 1

        failed = []
        for future in concurrent.futures.as_completed(futures):
            ticker, module_name = futures[future]
            if not future.result():
                failed.append(f"{ticker}/{module_name}")

        # Flush progress bar
        if failed:
            print()

    if failed:
        print(f"\n  Failed tasks ({len(failed)}):")
        for f in failed[:10]:
            print(f"    - {f}")
        if len(failed) > 10:
            print(f"    ... and {len(failed) - 10} more")

    # --- Phase 2: Merge per-module outputs ---
    if not failed:
        print(f"\n[PHASE 2] Merging per-module outputs")

        # Gather per-module files grouped by ticker
        ticker_files_map: dict[str, list[str]] = {}
        for f in output_dir.glob("*_ta_*.csv"):
            parts = f.name.rsplit("_ta_", 1)
            if len(parts) != 2:
                continue
            ticker = parts[0]
            ticker_files_map.setdefault(ticker, []).append(f.name)

        if not ticker_files_map:
            print("[MERGE] No per-module output files found, skipping merge.")
        else:
            deleted_files = set()
            print(f"  Merging {len(ticker_files_map)} ticker(s)")

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(8, len(ticker_files_map))
            ) as merge_executor:
                merge_futures = {
                    merge_executor.submit(
                        _merge_ticker, ticker, files, output_dir, deleted_files, file_lock
                    ): ticker
                    for ticker, files in sorted(ticker_files_map.items())
                }
                for future in concurrent.futures.as_completed(merge_futures):
                    ticker = merge_futures[future]
                    _, n_rows, n_cols = future.result()
                    print(f"  {ticker}.csv  ({n_rows} rows, {n_cols} columns)")

            print("[MERGE] Complete.\n")

    print(f"\n{'='*60}")
    print(f"  Pipeline {'complete' if not failed else 'FAILED'}")
    if failed:
        print(f"  Failed tasks: {', '.join(failed)}")
    else:
        print(f"  All modules passed.")
    print(f"{'='*60}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

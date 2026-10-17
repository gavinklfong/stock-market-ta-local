#!/usr/bin/env python
"""Orchestrator for all calculate_*.py TA modules.

Runs all TA indicator modules in parallel (modules are independent):

    calculate_trend.py       – EMA, SuperTrend, MA, slopes, price/MA ratio
    calculate_momentum.py    – RSI, MACD, ROC
    calculate_volume.py      – OBV, CMF, VWAP, OFI, log volume
    calculate_volatility.py  – ATR, Bollinger Bands
    calculate_regime.py      – GARCH, HMM regime, log return
    calculate_structure.py   – Swing points, HH/HL/LH/LL, BOS, CHoCH, S/R
    calculate_return.py      – Forward 5d/10d/20d returns

Each module reads from data/market-data/*.csv and writes its own file to
data/ta-data/{ticker}_ta_{type}.csv.

Usage:
    python run_calculation.py                          # run all, in parallel
    python run_calculation.py trend momentum           # run specific modules
    python run_calculation.py --help                   # show usage
"""

import argparse
import concurrent.futures
import subprocess
import sys
from pathlib import Path

import pandas as pd

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
    "trend":       "trend indicators: EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA ratio",
    "momentum":    "momentum indicators: RSI(14), MACD, ROC(20)",
    "volume":      "volume indicators: OBV, CMF(20), VWAP, OFI, log volume",
    "volatility":  "volatility indicators: ATR(14), Bollinger Bands(20,2)",
    "regime":      "regime detection: GARCH volatility + 3-state HMM, log return",
    "structure":   "structure indicators: HH/HL/LH/LL, BOS, CHoCH, Support/Resistance",
    "return":      "future returns: 5d/10d/20d",
}

# Maximum number of threads for parallel execution (modules + merge).
MAX_WORKERS = 8


def find_script_dir() -> Path:
    """Return the directory containing calculate_*.py scripts."""
    return Path(__file__).resolve().parent


def run_module(module_name: str, script_dir: Path, *, dry_run: bool = False) -> bool:
    """Run a single calculate_*.py module.

    Returns True on success, False on failure.
    """
    script = script_dir / MODULES[module_name]
    desc = DESCRIPTIONS[module_name]
    print(f"\n{'='*60}")
    print(f"  [{module_name.upper()}] {desc}")
    print(f"{'='*60}")

    if dry_run:
        print(f"  (dry-run) Would run: python {script}")
        return True

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script_dir),
        capture_output=False,
    )

    if result.returncode != 0:
        print(f"\n[ERROR] {module_name} failed with exit code {result.returncode}", file=sys.stderr)
        return False

    return True


def merge_outputs(script_dir: Path, output_dir: Path) -> bool:
    """Merge all per-module CSVs into a single {ticker}.csv per ticker.

    After parallel modules write {ticker}_ta_{type}.csv, this function
    collects them by ticker, merges on Date, and writes {ticker}.csv.

    Returns True on success, False on failure.
    """
    # Gather per-module files grouped by ticker
    ticker_files: dict[str, list[str]] = {}
    for f in output_dir.glob("*_ta_*.csv"):
        parts = f.name.rsplit("_ta_", 1)
        if len(parts) != 2:
            continue
        ticker = parts[0]
        ticker_files.setdefault(ticker, []).append(f.name)

    if not ticker_files:
        print("[MERGE] No per-module output files found, skipping merge.")
        return True

    print(f"\n{'='*60}")
    print(f"  [MERGE] Merging {len(ticker_files)} ticker(s)")
    print(f"{'='*60}")

    for ticker, files in sorted(ticker_files.items()):
        merged = None
        for fname in sorted(files):
            df = pd.read_csv(output_dir / fname)
            df["Date"] = pd.to_datetime(df["Date"])
            if merged is None:
                merged = df.sort_values("Date").reset_index(drop=True)
            else:
                # Merge on Date, keep only Date + ta_ columns from new file
                ta_cols = [c for c in df.columns if c.startswith("ta_")]
                new_cols = df[["Date"] + ta_cols]
                merged = merged.merge(new_cols, on="Date", how="left")

        merged["Date"] = merged["Date"].dt.strftime("%Y-%m-%d")
        merged = merged.sort_values("Date").reset_index(drop=True)
        merged.to_csv(output_dir / f"{ticker}.csv", index=False)
        n_cols = len([c for c in merged.columns if c != "Date"])
        print(f"  {ticker}.csv  ({len(merged)} rows, {n_cols} columns)")

        # Remove intermediate per-module files
        for fname in files:
            fpath = output_dir / fname
            fpath.unlink()

    print("[MERGE] Complete.\n")
    return True


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
    args = parser.parse_args()

    script_dir = find_script_dir()
    output_dir = script_dir.parent.parent / "data" / "ta-data"

    # Resolve requested modules → ordered list (for display only)
    if args.modules:
        order = [m for m in ALL_ORDER if m in args.modules]
    else:
        order = list(ALL_ORDER)

    print(f"\nTA Pipeline Runner")
    print(f"{'='*60}")
    print(f"  Scripts directory : {script_dir}")
    print(f"  Output directory  : {output_dir}")
    print(f"  Modules to run    : {', '.join(order)} (parallel)")
    print(f"{'='*60}")

    if args.dry_run:
        for name in order:
            print(f"  (dry-run) Would run: python {script_dir / MODULES[name]}")
        sys.exit(0)

    # Shared thread pool for parallel module execution and merge.
    num_workers = min(len(order) + 1, MAX_WORKERS)
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Run all modules in parallel
        module_futures = {
            executor.submit(run_module, name, script_dir): name
            for name in order
        }
        failed = []
        for future in concurrent.futures.as_completed(module_futures):
            name = module_futures[future]
            if not future.result():
                failed.append(name)

        # Merge per-module outputs into {ticker}.csv (only if all succeeded)
        if not failed:
            merge_future = executor.submit(merge_outputs, script_dir, output_dir)
            merge_future.result()  # wait for merge to complete

    print(f"\n{'='*60}")
    print(f"  Pipeline {'complete' if not failed else 'FAILED'}")
    if failed:
        print(f"  Failed modules    : {', '.join(failed)}")
    else:
        print(f"  All modules passed.")
    print(f"{'='*60}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

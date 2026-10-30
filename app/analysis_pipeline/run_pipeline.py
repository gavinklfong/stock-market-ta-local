#!/usr/bin/env python3
"""
Orchestrate the full stock-data pipeline with Prefect:

  1. Download OHLCV market data        (download_market_data/download_tickers.py)
  2. Download P/E ratio data           (download_market_data/download_stock_info.py)
  3. Run TA indicator calculations     (calculate_ta/run_calculation.py)
  4. Merge market + TA data into analysis (inline)
  5. Generate HTML analysis reports    (analyse_market_data/run_analysis.py)

Steps 1 & 2 run in parallel (independent downloads).
Steps 3, 4 & 5 run sequentially after both downloads complete.

Usage:
    # Run the flow locally (no server required):
    python -m app.analysis_pipeline.run_pipeline

    # CLI (passes args through to TA step):
    python -m app.analysis_pipeline.run_pipeline trend momentum

    # Process a specific ticker only:
    python -m app.analysis_pipeline.run_pipeline --ticker NG.L
    python -m app.analysis_pipeline.run_pipeline --ticker NG.L trend momentum

    # Force full recalculation (disable incremental TA computation):
    python -m app.analysis_pipeline.run_pipeline --force
    python -m app.analysis_pipeline.run_pipeline --force trend momentum
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

from prefect import flow, task
from prefect.task_runners import ThreadPoolTaskRunner

# ---------------------------------------------------------------------------
# Resolve paths relative to the project root (parent of the ``app/`` dir)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # …/stock-market-ta-local
APP_DIR = PROJECT_ROOT / "app"

DOWNLOAD_TICKERS = APP_DIR / "download_market_data" / "download_tickers.py"
DOWNLOAD_STOCK_INFO = APP_DIR / "download_market_data" / "download_stock_info.py"
TA_RUN_CALCULATION = APP_DIR / "calculate_ta" / "run_calculation.py"
ANALYSIS_RUN = APP_DIR / "analyse_market_data" / "run_analysis.py"


# ---------------------------------------------------------------------------
# Prefect tasks
# ---------------------------------------------------------------------------

@task(name="download-ohlcv")
def download_ohlcv(ticker: str | None = None) -> None:
    """Run the OHLCV market-data download script."""
    import subprocess
    print(f"\n{'='*60}")
    print("  ▶ Download OHLCV market data")
    print(f"{'='*60}")
    cmd = [sys.executable, str(DOWNLOAD_TICKERS)]
    if ticker:
        cmd.extend(["--ticker", ticker])
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(f"  ✓ OHLCV download completed (exit code {result.returncode})")


@task(name="download-stock-info")
def download_stock_info(ticker: str | None = None) -> None:
    """Run the P/E ratio download script."""
    import subprocess
    print(f"\n{'='*60}")
    print("  ▶ Download P/E ratio data")
    print(f"{'='*60}")
    cmd = [sys.executable, str(DOWNLOAD_STOCK_INFO)]
    if ticker:
        cmd.extend(["--ticker", ticker])
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(f"  ✓ P/E download completed (exit code {result.returncode})")


@task(name="run-ta-calculations")
def run_ta_calculations(ta_args: Sequence[str] = (), ticker: str | None = None) -> None:
    """Run the TA indicator calculation script."""
    import subprocess
    ta_cmd = [sys.executable, str(TA_RUN_CALCULATION)]
    if ticker:
        ta_cmd.extend(["--ticker", ticker])
    if ta_args:
        ta_cmd.extend(ta_args)

    print(f"\n{'='*60}")
    print("  ▶ Run TA indicator calculations")
    print(f"{'='*60}")
    result = subprocess.run(
        ta_cmd,
        cwd=str(PROJECT_ROOT),
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(f"  ✓ TA calculations completed (exit code {result.returncode})")


@task(name="merge-analysis-data")
def merge_analysis_data(ticker: str | None = None) -> None:
    """Merge market data, TA data, and P/E data into a single analysis CSV per ticker."""
    import sys

    import pandas as pd

    # Reuse the yfinance CSV parser (handles multi-row headers)
    sys.path.insert(0, str(APP_DIR / "calculate_ta"))
    from common import read_yfinance_csv  # noqa: E402

    market_dir = PROJECT_ROOT / "data" / "market-data"
    ta_dir = PROJECT_ROOT / "data" / "ta-data"
    pe_dir = PROJECT_ROOT / "data" / "pe-data"
    analysis_dir = PROJECT_ROOT / "data" / "analysis-data"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Discover tickers present in both market-data and ta-data
    market_files = {f.stem for f in market_dir.glob("*.csv")}
    ta_files = {f.stem for f in ta_dir.glob("*.csv")}
    tickers = sorted(market_files & ta_files)

    # Filter to requested ticker if specified
    if ticker:
        if ticker not in tickers:
            print(f"\n[MERGE] Ticker '{ticker}' not found in market-data/ta-data, skipping.")
            return
        tickers = [ticker]

    if not tickers:
        print("\n[MERGE] No matching market/TA files found, skipping.")
        return

    print(f"\n{'='*60}")
    print(f"  ▶ Merge analysis data ({len(tickers)} ticker(s))")
    print(f"{'='*60}")

    for ticker in tickers:
        market_df = read_yfinance_csv(str(market_dir / f"{ticker}.csv"))
        ta_df = pd.read_csv(ta_dir / f"{ticker}.csv")

        # Merge on Date (outer to keep all rows; most will align)
        merged = market_df.merge(ta_df, on="Date", how="outer")
        merged["Date"] = pd.to_datetime(merged["Date"])
        merged = merged.sort_values("Date").reset_index(drop=True)
        merged["Date"] = merged["Date"].dt.strftime("%Y-%m-%d")

        # Merge P/E ratio data (per-date) from {ticker}_PE.csv
        pe_file = pe_dir / f"{ticker}_PE.csv"
        if pe_file.exists():
            pe_df = pd.read_csv(pe_file)
            # Align Date format to the merged DataFrame (YYYY-MM-DD strings)
            pe_df["Date"] = pd.to_datetime(pe_df["Date"]).dt.strftime("%Y-%m-%d")
            pe_merged = merged.merge(pe_df, on="Date", how="left").copy()
            # Keep the more complete Close column (from market data)
            if "Close_x" in pe_merged.columns and "Close_y" in pe_merged.columns:
                pe_merged["Close"] = pe_merged["Close_x"].combine_first(pe_merged["Close_y"])
                pe_merged = pe_merged.drop(columns=["Close_x", "Close_y"])
            merged = pe_merged

        merged = merged.sort_values("Date").reset_index(drop=True)

        out_path = analysis_dir / f"{ticker}.csv"
        merged.to_csv(out_path, index=False)
        n_cols = len([c for c in merged.columns if c != "Date"])
        print(f"  {ticker}.csv  ({len(merged)} rows, {n_cols} data columns)")

    print(f"[MERGE] Output directory: {analysis_dir}\n")


@task(name="generate-analysis-reports")
def generate_analysis_reports(ticker: str | None = None) -> None:
    """Run the HTML report generation pipeline."""
    import subprocess

    print(f"\n{'='*60}")
    print("  ▶ Generate analysis HTML reports")
    print(f"{'='*60}")
    cmd = [sys.executable, str(ANALYSIS_RUN)]
    if ticker:
        cmd.extend(["--tickers", ticker])
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(f"  ✓ Analysis reports completed (exit code {result.returncode})")


# ---------------------------------------------------------------------------
# Prefect flow
# ---------------------------------------------------------------------------

@flow(
    name="stock-data-pipeline",
    description=(
        "Downloads market data (OHLCV + P/E) in parallel, "
        "runs TA indicator calculations, merges market + TA data "
        "into per-ticker analysis CSVs, then generates HTML reports."
    ),
    task_runner=ThreadPoolTaskRunner,
)
def run_pipeline(ta_args: Sequence[str] = (), ticker: str | None = None) -> None:
    """Execute the full data pipeline.

    Parameters
    ----------
    ta_args :
        Extra CLI arguments passed through to ``run_calculation.py``
        (e.g. ``["trend", "momentum"]`` for a subset).
    ticker :
        If provided, only download, calculate, merge, and report for
        this single ticker. Otherwise all tickers are processed.
    """
    from prefect.futures import wait as prefect_wait

    # -- Steps 1 & 2: download in parallel (ThreadPoolTaskRunner) ----------
    ohlcv_task = download_ohlcv.submit(ticker=ticker)
    info_task = download_stock_info.submit(ticker=ticker)

    # Wait for both downloads to complete (raises on failure)
    prefect_wait([ohlcv_task, info_task])

    # -- Step 3: TA calculations (depends on downloads) -------------------
    run_ta_calculations(ta_args=ta_args, ticker=ticker)

    # -- Step 4: merge market + TA data into analysis ---------------------
    merge_analysis_data(ticker=ticker)

    # -- Step 5: generate HTML reports ------------------------------------
    generate_analysis_reports(ticker=ticker)

    print(f"\n{'='*60}")
    print("  ✓  Full pipeline completed successfully.")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Orchestrate the stock-data pipeline with Prefect."
    )
    parser.add_argument(
        "ta_args",
        nargs="*",
        help="TA module names to run (default: all). "
             "e.g. trend momentum volume",
    )
    parser.add_argument(
        "--ticker",
        help="Process only this ticker (download, TA, merge, report).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full recalculation for TA modules (disable incremental computation).",
    )
    args = parser.parse_args()

    # Build the list of arguments passed through to run_calculation.py
    ta_args = list(args.ta_args)
    if args.force:
        ta_args.append("--force")

    run_pipeline(ta_args=ta_args, ticker=args.ticker)


if __name__ == "__main__":
    main()

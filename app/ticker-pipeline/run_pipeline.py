#!/usr/bin/env python3
"""
Orchestrate the full stock-data pipeline with Prefect:

  1. Download OHLCV market data        (ticker-retriever/download_tickers.py)
  2. Download P/E ratio data           (ticker-retriever/download_stock_info.py)
  3. Run TA indicator calculations     (calculate-ta/run_calculation.py)
  4. Merge market + TA data into analysis (inline)

Steps 1 & 2 run in parallel (independent downloads).
Steps 3 & 4 run sequentially after both downloads complete.

Usage:
    # Run the flow locally (no server required):
    python -m app.ticker_pipeline.run_pipeline

    # CLI (passes args through to TA step):
    python -m app.ticker_pipeline.run_pipeline trend momentum
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

DOWNLOAD_TICKERS = APP_DIR / "ticker-retriever" / "download_tickers.py"
DOWNLOAD_STOCK_INFO = APP_DIR / "ticker-retriever" / "download_stock_info.py"
TA_RUN_CALCULATION = APP_DIR / "calculate-ta" / "run_calculation.py"


# ---------------------------------------------------------------------------
# Prefect tasks
# ---------------------------------------------------------------------------

@task(name="download-ohlcv")
def download_ohlcv() -> None:
    """Run the OHLCV market-data download script."""
    import subprocess
    print(f"\n{'='*60}")
    print("  ▶ Download OHLCV market data")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, str(DOWNLOAD_TICKERS)],
        cwd=str(PROJECT_ROOT),
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(f"  ✓ OHLCV download completed (exit code {result.returncode})")


@task(name="download-stock-info")
def download_stock_info() -> None:
    """Run the P/E ratio download script."""
    import subprocess
    print(f"\n{'='*60}")
    print("  ▶ Download P/E ratio data")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, str(DOWNLOAD_STOCK_INFO)],
        cwd=str(PROJECT_ROOT),
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(f"  ✓ P/E download completed (exit code {result.returncode})")


@task(name="run-ta-calculations")
def run_ta_calculations(ta_args: Sequence[str] = ()) -> None:
    """Run the TA indicator calculation script."""
    import subprocess
    ta_cmd = [sys.executable, str(TA_RUN_CALCULATION)]
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
def merge_analysis_data() -> None:
    """Merge market data and TA data into a single analysis CSV per ticker."""
    import sys

    import pandas as pd

    # Reuse the yfinance CSV parser (handles multi-row headers)
    sys.path.insert(0, str(APP_DIR / "calculate-ta"))
    from common import read_yfinance_csv  # noqa: E402

    market_dir = PROJECT_ROOT / "data" / "market-data"
    ta_dir = PROJECT_ROOT / "data" / "ta-data"
    analysis_dir = PROJECT_ROOT / "data" / "analysis-data"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Discover tickers present in both market-data and ta-data
    market_files = {f.stem for f in market_dir.glob("*.csv")}
    ta_files = {f.stem for f in ta_dir.glob("*.csv")}
    tickers = sorted(market_files & ta_files)

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

        out_path = analysis_dir / f"{ticker}.csv"
        merged.to_csv(out_path, index=False)
        n_cols = len([c for c in merged.columns if c != "Date"])
        print(f"  {ticker}.csv  ({len(merged)} rows, {n_cols} data columns)")

    print(f"[MERGE] Output directory: {analysis_dir}\n")


# ---------------------------------------------------------------------------
# Prefect flow
# ---------------------------------------------------------------------------

@flow(
    name="stock-data-pipeline",
    description=(
        "Downloads market data (OHLCV + P/E) in parallel, "
        "runs TA indicator calculations, then merges market + TA data "
        "into per-ticker analysis CSVs."
    ),
    task_runner=ThreadPoolTaskRunner,
)
def run_pipeline(ta_args: Sequence[str] = ()) -> None:
    """Execute the full data pipeline.

    Parameters
    ----------
    ta_args :
        Extra CLI arguments passed through to ``run_calculation.py``
        (e.g. ``["trend", "momentum"]`` for a subset).
    """
    from prefect.futures import wait as prefect_wait

    # -- Steps 1 & 2: download in parallel (ThreadPoolTaskRunner) ----------
    ohlcv_task = download_ohlcv.submit()
    info_task = download_stock_info.submit()

    # Wait for both downloads to complete (raises on failure)
    prefect_wait([ohlcv_task, info_task])

    # -- Step 3: TA calculations (depends on downloads) -------------------
    run_ta_calculations(ta_args=ta_args)

    # -- Step 4: merge market + TA data into analysis ---------------------
    merge_analysis_data()

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
    args = parser.parse_args()

    run_pipeline(ta_args=args.ta_args)


if __name__ == "__main__":
    main()

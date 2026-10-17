#!/usr/bin/env python3
"""
Orchestrate the full stock-data pipeline with Prefect:

  1. Download OHLCV market data        (ticker-retriever/download_tickers.py)
  2. Download P/E ratio data           (ticker-retriever/download_stock_info.py)
  3. Run TA indicator calculations     (calculate-ta/run_calculation.py)

Steps 1 & 2 run in parallel (independent downloads).
Step 3 runs sequentially after both downloads complete.

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


# ---------------------------------------------------------------------------
# Prefect flow
# ---------------------------------------------------------------------------

@flow(
    name="stock-data-pipeline",
    description=(
        "Downloads market data (OHLCV + P/E) in parallel, "
        "then runs TA indicator calculations."
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

#!/usr/bin/env python
"""Generate HTML reports for all tickers in ticker_list.csv and sector-level reports.

Runs ticker-level and sector-level reports in parallel within a single thread pool.
"""

import argparse
import concurrent.futures
import sys
import threading
from pathlib import Path

# Ensure parent directory is on sys.path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyse_ticker import (
    BENCHMARK_TICKER,
    TICKER_LIST,
    analyse_benchmark,
    analyse_ticker_report,
    generate_ticker_html,
    load_ticker,
    _price_change_pct,
    _fmt,
    DEFAULT_OUTPUT_DIR,
)
from analyse_sector import (
    _load_ticker_info,
    generate_sector_html,
    group_by_sector,
)
from analyse_all import (
    DEFAULT_OUTPUT_DIR as ALL_DEFAULT_OUTPUT_DIR,
    generate_all_tickers_html,
    load_ticker_latest,
    _fmt as _fmt_all,
    _price_icon,
)


_print_lock = threading.Lock()


def _safe_print(*args, **kwargs):
    """Thread-safe print."""
    with _print_lock:
        print(*args, **kwargs)


def discover_available_tickers():
    """Return set of ticker names that have analysis CSVs in analysis-data/."""
    return {f.stem for f in Path(__file__).resolve().parent.parent.parent.joinpath("data", "analysis-data").glob("*.csv")}


def _ticker_report_task(ticker, benchmark_periods, benchmark_analysis, output_dir, dry_run):
    """Run analysis and generate HTML for a single ticker.

    Returns (success: bool, ticker: str).
    """
    _safe_print(f"Analysing {ticker}...")
    r = analyse_ticker_report(ticker, benchmark_periods, benchmark_analysis)
    if r is None:
        return False, ticker

    if dry_run:
        _safe_print(f"  Dry run: analysis for {ticker} shown above.")
        return True, ticker

    out = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / f"{r['ticker']}_analysis.html"
    html = generate_ticker_html(r)
    output_path.write_text(html, encoding="utf-8")
    _safe_print(f"Report written to {output_path}")
    return True, ticker


def _sector_report_task(sector_name, sector_tickers, available, output_dir, dry_run):
    """Collect period returns and generate HTML for a single sector.

    Returns (success: bool, sector_name: str).
    """
    _safe_print(f"Analysing sector: {sector_name} ({len(sector_tickers)} tickers)")
    tickers_data = []
    for ticker, company in sector_tickers:
        try:
            df = load_ticker(ticker)
            periods = _price_change_pct(df)
            close = float(df["Close"].iloc[-1])
            latest_date = str(df["Date"].iloc[-1])[:10]
            tickers_data.append((ticker, company, close, latest_date, periods))
            _safe_print(f"  {ticker}: 1Y={periods.get('1Y')}")
        except Exception as e:
            _safe_print(f"  {ticker}: Error - {e}")

    # Sort by 1Y return descending (None values go last)
    tickers_data.sort(key=lambda x: x[4].get("1Y") if x[4].get("1Y") is not None else -999, reverse=True)

    if dry_run:
        return True, sector_name

    # Generate HTML report
    html = generate_sector_html(sector_name, tickers_data)
    filename = f"sector_analysis_{sector_name.replace(' ', '_')}.html"
    out = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / filename
    output_path.write_text(html, encoding="utf-8")
    _safe_print(f"Report written to {output_path}")
    return True, sector_name


def _generate_all_tickers_report(available, ticker_info, output_dir, dry_run, filter_tickers=None):
    """Collect period returns and generate the all-tickers overview HTML report.

    Args:
        available: set of ticker names with analysis CSVs.
        ticker_info: dict mapping ticker -> company name.
        output_dir: output directory path or None.
        dry_run: if True, only print data, don't write HTML.
        filter_tickers: optional set of tickers to include (subset of available).
    """
    if filter_tickers:
        available = available & filter_tickers

    tickers_data = []
    for ticker in sorted(available):
        try:
            latest = load_ticker_latest(ticker)
            close = float(latest.get("Close", 0)) or float(latest.get("Adj Close", 0))
            period_1y = latest.get("ta_performance_1y")
            period_6m = latest.get("ta_performance_6m")
            period_1m = latest.get("ta_performance_1m")
            company = ticker_info.get(ticker, ticker)
            tickers_data.append({
                "ticker": ticker,
                "company": company,
                "close": close,
                "period_1y": float(period_1y) if period_1y is not None else None,
                "period_6m": float(period_6m) if period_6m is not None else None,
                "period_1m": float(period_1m) if period_1m is not None else None,
            })
            y_str = _fmt_all(period_1y, 2) if period_1y is not None else "N/A"
            _safe_print(f"  {ticker}: 1Y={y_str}%")
        except Exception as e:
            _safe_print(f"  {ticker}: Error - {e}")

    # Sort by 1Y return descending (None values go last)
    tickers_data.sort(key=lambda x: x["period_1y"] if x["period_1y"] is not None else -999, reverse=True)

    if not tickers_data:
        _safe_print("No tickers data collected for all-tickers report.")
        return False

    if dry_run:
        _safe_print("\nDry run complete. All-tickers analysis shown above.")
        return True

    # Get latest date from first valid ticker
    latest_date = None
    for t in tickers_data:
        try:
            latest = load_ticker_latest(t["ticker"])
            latest_date = str(latest["Date"])[:10]
            break
        except Exception:
            continue
    latest_date = latest_date or "N/A"

    # Generate HTML report
    out = Path(output_dir) if output_dir else ALL_DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    html = generate_all_tickers_html(tickers_data, latest_date)
    output_path = out / "all_tickers.html"
    output_path.write_text(html, encoding="utf-8")
    _safe_print(f"\nAll-tickers report written to {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate HTML reports for all tickers in ticker_list.csv")
    parser.add_argument("--dry-run", action="store_true", help="Show analysis only, don't generate HTML")
    parser.add_argument("--output", default=None, help="Output directory for HTML reports")
    parser.add_argument("--tickers", nargs="*", help="Limit to specific tickers from ticker_list.csv")
    parser.add_argument("--no-sector", action="store_true", help="Skip sector-level reports")
    args = parser.parse_args()

    # Read ticker list
    if not TICKER_LIST.exists():
        print(f"Error: ticker list not found at {TICKER_LIST}")
        sys.exit(1)

    import pandas as pd
    ticker_df = pd.read_csv(TICKER_LIST)
    tickers = ticker_df["Ticker"].str.strip().tolist()

    # Limit to requested tickers if specified
    if args.tickers:
        tickers = [t for t in tickers if t in args.tickers]
        if not tickers:
            print(f"Error: no matching tickers found in ticker_list.csv")
            sys.exit(1)

    available = discover_available_tickers()
    missing = [t for t in tickers if t not in available]
    if missing:
        print(f"Warning: {len(missing)} ticker(s) not found in analysis-data: {', '.join(missing)}")

    tickers = [t for t in tickers if t in available]
    if not tickers:
        print("Error: no tickers available in analysis-data/")
        print(f"Available: {', '.join(sorted(available))}")
        sys.exit(1)

    print(f"Found {len(tickers)} ticker(s) to process")
    print()

    # Load benchmark (FTSE) once
    benchmark_periods = None
    benchmark_analysis = None
    if BENCHMARK_TICKER in available:
        _safe_print(f"Loading benchmark {BENCHMARK_TICKER}...")
        bench_df = load_ticker(BENCHMARK_TICKER)
        benchmark_periods = _price_change_pct(bench_df)
        benchmark_analysis = analyse_benchmark(bench_df)
        benchmark_analysis["ticker"] = BENCHMARK_TICKER
        benchmark_analysis["company_name"] = "FTSE 100 Index"
        _safe_print(f"  Benchmark 1Y: {benchmark_periods.get('1Y')}")
        _safe_print(f"  Benchmark Close={_fmt(benchmark_analysis['close'])}, RSI={_fmt(benchmark_analysis['rsi'],1)}, MACD_hist={_fmt(benchmark_analysis['macd_hist'])}")
        _safe_print()

    output_dir = args.output

    # -------------------------------------------------------------------------
    # Phase 1: Prepare sector report data (only if needed)
    # -------------------------------------------------------------------------
    sectors = None
    sector_tasks = []
    if not args.no_sector:
        # Discover unique sectors (excluding Index)
        ticker_info = _load_ticker_info()
        sectors = group_by_sector(ticker_info, available)
        if not sectors:
            _safe_print("No sectors found (excluding Index)")
            sectors = {}

        # If specific tickers were requested, only include sectors that contain them
        if args.tickers:
            tickers_in_requested = [t for t in tickers if t in available]
            sectors_to_process = {}
            for ticker in tickers_in_requested:
                if ticker in ticker_info:
                    _, sector = ticker_info[ticker]
                    if sector != "Index" and sector in sectors:
                        sectors_to_process[sector] = sectors[sector]
            sectors = sectors_to_process

        if not sectors:
            _safe_print("No sectors found for the requested tickers")
        else:
            # Prepare tasks: each sector will run in parallel with ticker reports
            for sector_name in sorted(sectors.keys()):
                sector_tasks.append((sector_name, sectors[sector_name]))

    # -------------------------------------------------------------------------
    # Phase 2: Run ticker reports and sector reports in parallel
    # -------------------------------------------------------------------------
    total_tasks = len(tickers) + len(sector_tasks)
    num_workers = min(max(4, total_tasks), max(8, min(16, total_tasks * 2)))

    _safe_print(f"Running {len(tickers)} ticker report(s) + {len(sector_tasks)} sector report(s) in parallel ({num_workers} workers)...")
    _safe_print()

    ticker_success = 0
    ticker_failed = 0
    sector_success = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}

        # Submit ticker report tasks
        for t in tickers:
            futures[executor.submit(
                _ticker_report_task, t, benchmark_periods, benchmark_analysis, output_dir, args.dry_run
            )] = ("ticker", t)

        # Submit sector report tasks
        for sector_name, sector_tickers in sector_tasks:
            futures[executor.submit(
                _sector_report_task, sector_name, sector_tickers, available, output_dir, args.dry_run
            )] = ("sector", sector_name)

        # Collect results
        for future in concurrent.futures.as_completed(futures):
            task_type, name = futures[future]
            ok, _ = future.result()
            if task_type == "ticker":
                if ok:
                    ticker_success += 1
                else:
                    ticker_failed += 1
            else:
                if ok:
                    sector_success += 1

    print()
    _safe_print(f"Ticker reports: {ticker_success} generated, {ticker_failed} failed")
    _safe_print(f"Sector reports: {sector_success} generated")
    _safe_print()

    # -------------------------------------------------------------------------
    # Phase 3: Generate all-tickers overview report
    # -------------------------------------------------------------------------
    ticker_info = _load_ticker_info()
    filter_tickers = set(tickers) if args.tickers else None
    all_success = _generate_all_tickers_report(
        available, ticker_info, output_dir, args.dry_run, filter_tickers
    )

    _safe_print(f"Done: {ticker_success + sector_success + (1 if all_success else 0)} report(s) generated, {ticker_failed} failed")


if __name__ == "__main__":
    main()
